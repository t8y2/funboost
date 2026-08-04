---
name: using-funboost-basics
description: 当需要使用 funboost 编写分布式任务时使用。触发场景：创建 @boost 装饰器任务函数、使用 push/publish 发布消息、启动 consume 消费者、配置 BoosterParams 参数、设置并发和限流。关键词：boost, BoosterParams, queue_name, push, publish, consume, distributed task, 分布式任务, 消息队列。
---

# Funboost 基础使用

## 概述

Funboost 用一个 `@boost` 装饰器把任意 Python 函数变成分布式任务。零侵入设计——`func(x, y)` 直接本地运行，`func.push(x, y)` 发送到队列。

**核心原则：** 你的函数保持为普通函数，不需要任何框架改造。

## 适用场景

- 创建新的分布式任务函数
- 向任务队列发布消息
- 启动任务消费者（Worker）
- 将现有函数改造为分布式任务
- 配置基础并发和限流

## 铁律（绝对不可违反）

1. **必须使用 `BoosterParams` 对象** — 禁止向 `@boost` 传递裸参数
2. **禁止使用 Celery 模式** — 不用 `self`、不用 `bind=True`，获取上下文用 `fct`
4. **`push` 只传业务参数；`publish` 用字典传业务参数，并通过 `task_options=TaskOptions(...)` 附加框架控制参数**

## 速查表

| 操作 | 代码 |
|------|------|
| 定义任务 | `@boost(BoosterParams(queue_name="q1"))` |
| 推送消息 | `func.push(x, y)` |
| 带控制选项发布 | `func.publish({"x": 1}, task_options=TaskOptions(countdown=5))` |
| 异步推送 | `await func.aio_push(x, y)` |
| 启动消费 | `func.consume()` |
| 多进程消费 | `func.multi_process_consume(3)` |
| 获取任务上下文 | `from funboost import fct; fct.task_id` |
| Windows 下 Ctrl+C 退出 | `enable_ctrl_c_quit_on_windows()`（可选，不加也能运行） |

## 核心代码模式

以下是零依赖最小示例（使用 `MEMORY_QUEUE`，无需 Redis/RabbitMQ）：

```python
from funboost import boost, BoosterParams, BrokerEnum

@boost(BoosterParams(
    queue_name="hello_funboost",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
))
def add(a, b):
    print(f"计算: {a} + {b} = {a + b}")
    return a + b

if __name__ == "__main__":
    add.push(1, 2)
    add.push(10, 20)
    add.consume()
    # funboost 消费者永久运行，不会自动退出（和 Celery worker 一样）
    # 如果是 Windows 想用 Ctrl+C 停止：
    from funboost import enable_ctrl_c_quit_on_windows
    enable_ctrl_c_quit_on_windows()
```

以下示例使用 Redis（需先在 `funboost_config.py` 中配置 `REDIS_HOST` 等参数）：

```python
from funboost import boost, BoosterParams, BrokerEnum

@boost(BoosterParams(
    queue_name="my_task_queue",
    broker_kind=BrokerEnum.REDIS_ACK_ABLE,
    concurrent_num=30,
    qps=10,
    max_retry_times=3,
    log_level=20,
))
def my_task(url: str, depth: int = 1):
    """你的业务逻辑——保持为普通函数"""
    import requests
    resp = requests.get(url)
    return resp.status_code

if __name__ == "__main__":
    # 发布消息
    for i in range(100):
        my_task.push(f"https://example.com/page/{i}", depth=2)

    # 启动消费
    my_task.consume()
```

## 发布方法详解

### push — 只传业务参数

```python
my_task.push("https://example.com", depth=3)
```

### publish — 附带框架控制参数（countdown、task_id 等）

```python
from funboost import TaskOptions

my_task.publish(
    {"url": "https://example.com", "depth": 3},
    task_options=TaskOptions(
        countdown=10,           # 延迟 10 秒执行
        task_id="custom-id-1",  # 自定义 task ID
    )
)
```

### 异步发布（须在 async def 内）

```python
async def publish_tasks():
    await my_task.aio_push("https://example.com", depth=3)
    await my_task.aio_publish({"url": "..."}, task_options=TaskOptions(countdown=5))
```

## 启动多个消费者

```python
task_a.consume()
task_b.consume()
task_c.consume()
```

**绝对禁止** 用 `threading.Thread` 包装 `consume()` — 它本身就是非阻塞的。

## 任务上下文 (fct)

```python
from funboost import fct

@boost(BoosterParams(queue_name="ctx_demo"))
def my_task(x):
    print(f"Task ID: {fct.task_id}")
    print(f"队列名: {fct.queue_name}")
    print(f"执行次数: {fct.function_result_status.run_times}")
    print(f"函数参数: {fct.function_params}")
    print(f"完整消息: {fct.full_msg}")
    fct.logger.info("当前任务 logger")
```

常用属性：

| 属性 | 说明 |
|------|------|
| `fct.task_id` | 当前任务 ID |
| `fct.queue_name` | 队列名 |
| `fct.function_result_status.run_times` | 运行次数（含重试） |
| `fct.function_params` | 函数入参 |
| `fct.full_msg` | 完整消息体 |
| `fct.logger` | 当前任务 logger |

## BoosterParams 核心字段

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `queue_name` | str | — | **必填**，队列名 |
| `broker_kind` | str | SQLITE_QUEUE | 消息中间件类型 |
| `concurrent_num` | int | 50 | 并发数量 |
| `concurrent_mode` | str | ConcurrentModeEnum.THREADING | threading/gevent/eventlet/async/single_thread |
| `qps` | float/int/None | None | 每秒执行次数限制 |
| `max_retry_times` | int | 3 | 最大重试次数 |
| `function_timeout` | int/float/None | None | 函数超时秒数 |
| `log_level` | int | 10 (DEBUG) | 日志级别 |
| `is_using_rpc_mode` | bool | False | 是否启用 RPC 获取结果 |

## 常见错误

| 错误写法 | 正确写法 |
|----------|----------|
| `@boost("queue", qps=5)` | `@boost(BoosterParams(queue_name="queue", qps=5))` |
| `def task(self, x):` 获取上下文 | 使用 `fct.task_id` |
| `timeout=30` | `function_timeout=30` |
| `max_retries=5` | `max_retry_times=5` |
| 用 threading 启动多个消费者 | 直接顺序调用 `func1.consume(); func2.consume()` |
| `func.push(msg_dict)` 带控制参数 | 使用 `func.publish(msg_dict, task_options=TaskOptions(...))` |
| `obj.method.push(arg1)` 实例方法 push | `ClassName.method.push(obj_instance, arg1, arg2)`，第一个参数传对象实例 |

> **实例方法 push 语法：** 必须写成 `ClassName.method.push(obj_instance, arg1, arg2)`，第一个参数传对象实例。禁止写 `obj.method.push(arg1)`。

## 消费来自其他系统的消息

当消费非 funboost 发布的消息（如 Java/Go 写入的）时：

```python
@boost(BoosterParams(
    queue_name="external_queue",
    should_check_publish_func_params=False,
))
def handle_external(**kwargs):
    """使用 **kwargs 接收任意 JSON 结构"""
    print(kwargs)
```

**绝对禁止** 用 `def handle(msg):` 单参数接收整个字典——必须用 `**kwargs` 或 `**msg` 解包接收。

## 相关 Skill

- `understanding-funboost-concepts` — 框架概念入门
- `funboost-rpc-mode` — 获取任务执行返回值
- `funboost-async-programming` — async/await 异步编程
- `funboost-broker-selection` — Broker 中间件选型
