---
name: funboost-advanced-retry
description: 当需要配置 funboost 的高级重试策略时使用。触发场景：指数退避重试、死信队列、熔断器、任务去重过滤、自定义错误处理。关键词：retry, max_retry_times, dead letter, DLX, exponential backoff, circuit breaker, is_using_advanced_retry, is_push_to_dlx_queue_when_retry_max_times, do_task_filtering, 重试, 死信, 熔断。
compatibility: Python 3.7+, funboost package installed
---

# Funboost 高级重试与容错

## 概述

Funboost 提供多层错误恢复能力：自动重试、指数退避、死信队列、熔断器和任务去重。

**核心原则：** 通过 BoosterParams 声明式配置重试行为——不要手动编写 try/except 重试循环。

## 适用场景

- 任务可能因瞬态故障失败（网络、API 限流）
- 需要重试间递增等待时间（指数退避）
- 希望最终失败的任务路由到死信队列
- 需要熔断器保护下游服务
- 需要防止同一任务重复执行

## 速查表

| 功能 | BoosterParams 字段 | 默认值 |
|------|-------------------|--------|
| 最大重试次数 | `max_retry_times` | 3 |
| 指数退避 | `is_using_advanced_retry` | False |
| 死信队列 | `is_push_to_dlx_queue_when_retry_max_times` | False |
| 任务去重 | `do_task_filtering` | False |
| 函数超时 | `function_timeout` | None |

## 基础重试

```python
from funboost import boost, BoosterParams

@boost(BoosterParams(
    queue_name="fragile_task",
    max_retry_times=5,          # 异常时最多重试 5 次
    function_timeout=30,        # 单次执行超过 30 秒则终止
))
def call_external_api(url: str):
    import requests
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    return resp.json()
```

## 指数退避重试

```python
@boost(BoosterParams(
    queue_name="backoff_task",
    max_retry_times=5,
    is_using_advanced_retry=True,  # 启用指数退避
))
def rate_limited_api(endpoint: str):
    """指数退避：间隔 = min(base * 2^n, max_interval)，默认 1s,2s,4s,8s...封顶60s"""
    import requests
    resp = requests.get(endpoint)
    if resp.status_code == 429:
        raise Exception("被限流了")
    return resp.json()
```

### advanced_retry_config 参数

通过 `BoosterParams.advanced_retry_config` 字典自定义退避行为：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `retry_mode` | str | `"sleep"` | `"sleep"` = 当前线程 sleep 等待后重试；`"requeue"` = 发回队列（附带 countdown），释放线程 |
| `retry_base_interval` | float | `1.0` | 退避基础间隔（秒） |
| `retry_multiplier` | float | `2.0` | 退避倍数（每次重试间隔乘以此值） |
| `retry_max_interval` | float | `60.0` | 退避最大间隔（秒），封顶值 |
| `retry_jitter` | bool | `False` | 是否加随机抖动，防止多消费者同时重试（惊群） |

```python
@boost(BoosterParams(
    queue_name="custom_backoff_task",
    max_retry_times=8,
    is_using_advanced_retry=True,
    advanced_retry_config={
        "retry_mode": "requeue",         # 重试时发回队列，释放线程资源
        "retry_base_interval": 2.0,      # 起始等 2 秒
        "retry_multiplier": 3.0,         # 每次 x3：2s, 6s, 18s, 54s, 60s(封顶)...
        "retry_max_interval": 60.0,      # 最大 60 秒
        "retry_jitter": True,            # 加随机抖动
    },
))
def custom_backoff_task(data: dict):
    process(data)
```

**两种 retry_mode 的区别：**
- `"sleep"` — 简单场景，线程被占用直到重试完成；适合并发数充足时
- `"requeue"` — 消息重新入队（带 countdown 延迟），当前线程立即释放去处理其他消息；适合高并发/长退避场景

## 死信队列 (DLX)

开启 `is_push_to_dlx_queue_when_retry_max_times=True` 后，重试耗尽的任务推送到死信队列：

```python
@boost(BoosterParams(
    queue_name="important_task",
    max_retry_times=3,
    is_push_to_dlx_queue_when_retry_max_times=True,  # -> important_task_dlx
))
def process_payment(order_id: str, amount: float):
    """3 次重试全部失败后，消息进入 'important_task_dlx' 队列"""
    charge(order_id, amount)
```

## 熔断器 (Mixin)

连续失败达阈值时熔断（OPEN 状态下消费端 `_submit_task` 阻塞等待恢复，消息暂留队列；不影响发布端 `push`/`publish`），防止级联故障：

```python
from funboost import boost, BoosterParams
from funboost.contrib.override_publisher_consumer_cls.circuit_breaker_mixin import CircuitBreakerConsumerMixin

@boost(BoosterParams(
    queue_name="protected_task",
    consumer_override_cls=CircuitBreakerConsumerMixin,
    user_options={
        "circuit_breaker_options": {
            "failure_threshold": 5,     # 连续 5 次失败后熔断(OPEN)
            "recovery_timeout": 60,     # 60 秒后进入半开(HALF_OPEN)试探
        },
    },
))
def call_fragile_service(data: dict):
    return external_service.process(data)
```

## 任务去重（过滤）

消费端过滤：相同入参的任务**完成一次消费周期后**，再次发布会被跳过（需 Redis）：

```python
@boost(BoosterParams(
    queue_name="dedup_task",
    do_task_filtering=True,  # 需要 Redis 配置
))
def send_notification(user_id: int, message: str):
    """相同 (user_id, message) 组合完成消费后不会重复处理"""
    notify(user_id, message)
```

## 获取重试上下文

```python
from funboost import fct

@boost(BoosterParams(queue_name="ctx_retry", max_retry_times=3))
def task_with_context(url: str):
    run_times = fct.function_result_status.run_times
    if run_times > 1:
        print(f"第 {run_times} 次执行（第 {run_times - 1} 次重试）")
    fetch(url)
```

## 组合多种策略

```python
@boost(BoosterParams(
    queue_name="resilient_pipeline",
    max_retry_times=5,
    is_using_advanced_retry=True,
    is_push_to_dlx_queue_when_retry_max_times=True,
    function_timeout=60,
    do_task_filtering=True,
))
def resilient_task(job_id: str, payload: dict):
    """
    - 指数退避重试 5 次
    - 每次超时 60 秒
    - 相同入参完成消费后自动跳过
    - 重试耗尽后进入死信队列
    """
    process(job_id, payload)
```

## 常见错误

| 错误 | 修正 |
|------|------|
| `max_retries=5` | 正确字段：`max_retry_times=5` |
| `timeout=30` | 正确字段：`function_timeout=30` |
| 手写重试循环 | 让 funboost 通过 BoosterParams 处理重试 |
| `do_task_filtering=True` 但没配 Redis | 任务过滤依赖 Redis |
| 搞混 DLX 队列名 | 自动命名为 `{原队列名}_dlx` |
| 用 `try/except` 吞掉所有异常 | 让异常正常抛出，funboost 才能执行重试 |
