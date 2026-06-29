---
name: developing-funboost-mixin
description: 当需要为 funboost 创建 Consumer 或 Publisher 的 Mixin 扩展类时使用。触发场景：添加监控、熔断、限流、链路追踪等横切关注点，编写自定义前置/后置处理钩子。关键词：mixin, consumer_override_cls, publisher_override_cls, ConsumerMixin, 自定义消费者, hook, 拦截器, 熔断器, 监控, Prometheus, OpenTelemetry。
compatibility: Python 3.7+, funboost source code access
---

# 开发 Funboost Mixin 扩展

## 概述

Mixin 可以向任意 funboost broker 添加横切关注点（监控、链路追踪、限流等），而无需修改 broker 本身。利用 Python 的 MRO 拦截方法。

**核心原则：** Mixin 重写特定方法，调用 `super()` 继续链路，配置存在 `user_options` 中。

## 适用场景

- 为任务执行添加监控/指标
- 实现熔断器、限流器
- 添加 OpenTelemetry / Prometheus 埋点
- 自定义任务执行前后的处理逻辑
- 通过 MRO 组合多种行为

## 已有 Mixin 参考

| Mixin | 用途 | 位置 |
|-------|------|------|
| `CircuitBreakerConsumerMixin` | 高错误率时停止消费 | `funboost/contrib/override_publisher_consumer_cls/` |
| `MicroBatchConsumerMixin` | 微批消费（攒多条再处理） | `funboost/contrib/override_publisher_consumer_cls/` |
| `PrometheusConsumerMixin` | 导出 Prometheus 指标 | `funboost/contrib/override_publisher_consumer_cls/` |
| `PrometheusPublisherMixin` | 发布端 Prometheus 指标 | `funboost/contrib/override_publisher_consumer_cls/` |
| `AutoOtelConsumerMixin` | OpenTelemetry 链路追踪 | `funboost/contrib/override_publisher_consumer_cls/` |
| `AutoOtelPublisherMixin` | 发布端 OpenTelemetry 追踪 | `funboost/contrib/override_publisher_consumer_cls/` |
| `PeriodicQuotaConsumerMixin` | 时间窗口配额限制 | `funboost/contrib/override_publisher_consumer_cls/` |
| `AlertNotifierConsumerMixin` | 异常告警通知 | `funboost/contrib/override_publisher_consumer_cls/` |

## Mixin 模板

```python
from funboost.consumers.base_consumer import AbstractConsumer

class MyConsumerMixin(AbstractConsumer):
    """
    继承 AbstractConsumer 是可选的（仅为 IDE 自动补全）。
    不继承也能正常工作——运行时 mixin 通过动态多重继承合并 MRO。
    """

    def custom_init(self):
        super().custom_init()
        # 从 user_options 读取配置
        opts = self.consumer_params.user_options.get("my_mixin_options", {})
        self._threshold = opts.get("threshold", 10)
        self._counter = 0

    def _submit_task(self, kw):
        """任务提交到线程池前的前置检查"""
        self._counter += 1
        if self._counter > self._threshold:
            print(f"[WARN] 连续失败 {self._counter} 次，超过阈值 {self._threshold}")
        super()._submit_task(kw)

    def _both_sync_and_aio_frame_custom_record_process_info_func(
        self, current_function_result_status, kw
    ):
        """
        每个任务执行后调用（同步和异步都会触发）。
        注意：此钩子内禁止有 IO 阻塞操作（如 HTTP 请求、数据库写入），
        否则会拖慢消费速度。如需 IO 操作，请用 _frame_custom_record_process_info_func
        （仅同步触发）或异步钩子配合 simple_run_in_executor。
        """
        super()._both_sync_and_aio_frame_custom_record_process_info_func(
            current_function_result_status, kw
        )
        if current_function_result_status.success:
            self._counter = 0  # 成功时重置计数
        else:
            self._counter += 1
```

## 使用方式

```python
from funboost import boost, BoosterParams, BrokerEnum

@boost(BoosterParams(
    queue_name="monitored_task",
    broker_kind=BrokerEnum.REDIS_ACK_ABLE,
    consumer_override_cls=MyConsumerMixin,
    user_options={
        "my_mixin_options": {
            "threshold": 100,
        }
    },
))
def my_task(x):
    return x * 2
```

## 关键重写点

### 前置钩子

| 方法 | 调用时机 | 用途 |
|------|----------|------|
| `_submit_task(kw)` | 任务进入线程池前 | 限流、熔断、配额检查 |
| `_before_start_consuming_message_hook()` | 消费者启动时（一次性） | 初始化连接、注册指标 |

### 后置钩子

| 方法 | 调用时机 | 用途 |
|------|----------|------|
| `_both_sync_and_aio_frame_custom_record_process_info_func` | 每个任务执行后（仅 CPU 操作） | 计数器、状态更新 |
| `_frame_custom_record_process_info_func` | 每个任务执行后（同步线程中，允许 IO） | 写数据库、HTTP 调用 |
| `_aio_frame_custom_record_process_info_func` | 每个任务执行后（异步协程中，允许 IO） | 异步写数据库 |

**三种后置钩子的选择原则：**

- `_both_sync_and_aio_frame_custom_record_process_info_func(self, current_function_result_status, kw)`
  **禁止 IO 阻塞**。在任务框架的核心路径上调用（同步/异步统一入口），适合纯内存操作（计数器递增、状态标记）。

- `_frame_custom_record_process_info_func(self, current_function_result_status, kw)`
  **允许同步 IO**。在同步消费模式（threading/gevent/eventlet）下独立线程中调用，适合写数据库、发 HTTP 请求等阻塞操作。不会影响主消费速度。

- `_aio_frame_custom_record_process_info_func(self, current_function_result_status, kw)`
  **允许异步 IO**。在异步消费模式（`concurrent_mode=ASYNC`）下作为协程调用，适合 `await` 异步数据库写入。

```python
class MonitorMixin(AbstractConsumer):
    def custom_init(self):
        super().custom_init()
        self._total = 0
        self._failures = 0

    def _both_sync_and_aio_frame_custom_record_process_info_func(
        self, current_function_result_status, kw
    ):
        """纯内存操作 — 禁止 IO"""
        super()._both_sync_and_aio_frame_custom_record_process_info_func(
            current_function_result_status, kw
        )
        self._total += 1
        if not current_function_result_status.success:
            self._failures += 1

    def _frame_custom_record_process_info_func(
        self, current_function_result_status, kw
    ):
        """同步 IO 允许 — 如写数据库、发告警"""
        super()._frame_custom_record_process_info_func(
            current_function_result_status, kw
        )
        if not current_function_result_status.success:
            import requests
            requests.post("http://alert.example.com/notify", json={
                "queue": self.queue_name,
                "error": str(current_function_result_status.exception),
                "total": self._total,
            })

    async def _aio_frame_custom_record_process_info_func(
        self, current_function_result_status, kw
    ):
        """异步 IO 允许 — 异步消费模式下使用"""
        await super()._aio_frame_custom_record_process_info_func(
            current_function_result_status, kw
        )
        if not current_function_result_status.success:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                await session.post("http://alert.example.com/notify", json={
                    "queue": self.queue_name,
                    "error": str(current_function_result_status.exception),
                })
```

### 执行包裹

| 方法 | 调用时机 | 用途 |
|------|----------|------|
| `_run(kw)` | 同步任务执行 | 链路追踪 Span、计时 |
| `_async_run(kw)` | 异步任务执行 | 异步链路追踪 |

## 配置规范

将 mixin 专属配置放在 `user_options` 的命名空间 key 下：

```python
user_options={
    "circuit_breaker_options": {
        "failure_threshold": 5,
        "recovery_timeout": 60,
    },
    "my_custom_mixin_options": {
        "my_key": "my_value",
    },
}
```

这样防止多个 mixin 的配置键冲突。

## 组合多个 Mixin

```python
class CombinedMixin(CircuitBreakerConsumerMixin, PrometheusConsumerMixin):
    """MRO 确保两个 mixin 的方法都能执行"""
    pass

@boost(BoosterParams(
    queue_name="combined_task",
    consumer_override_cls=CombinedMixin,
    user_options={
        "circuit_breaker_options": {"failure_threshold": 5},
    },
))
def my_task(x): ...
```

两个 mixin 都能正常工作，因为它们都调用了 `super()` — MRO 正确串联。

## 异步兼容

如果后置钩子涉及 IO 操作：

```python
from funboost.concurrent_pool.async_helper import simple_run_in_executor

class MyAsyncAwareMixin(AbstractConsumer):

    def _frame_custom_record_process_info_func(self, status, kw):
        """同步版本（含 IO）"""
        super()._frame_custom_record_process_info_func(status, kw)
        self._save_to_db(status)

    async def _aio_frame_custom_record_process_info_func(self, status, kw):
        """异步版本 — 通过 executor 复用同步逻辑"""
        await super()._aio_frame_custom_record_process_info_func(status, kw)
        await simple_run_in_executor(
            self._frame_custom_record_process_info_func, status, kw
        )
```

## 常见错误

| 错误 | 修正 |
|------|------|
| 重写时忘记调 `super()` | 除抽象方法外始终调用 super() |
| `user_options` 键名扁平化 | 应放在 mixin 专属的嵌套 key 下 |
| 只重写 `_run` 不重写 `_async_run` | 必须同时处理同步和异步路径 |
| 到处写 try/except 防御 | 让异常正常抛出——funboost 处理重试 |
| 不继承导致无 IDE 补全 | 继承 `AbstractConsumer` 获取自动补全（运行时可选） |
| 多 mixin 组合时 MRO 冲突 | 确保所有 mixin 中一致调用 super() |

## Publisher Mixin 示例

```python
from funboost.publishers.base_publisher import AbstractPublisher

class MyPublisherMixin(AbstractPublisher):

    def _publish_impl(self, msg: str):
        """拦截发布，添加日志/指标"""
        self._log_publish(msg)
        super()._publish_impl(msg)

    def _after_publish(self, publish_msg_context):
        super()._after_publish(publish_msg_context)
        self._record_publish_metric()
```

## 参考代码位置

- 已有 mixin：`funboost/contrib/override_publisher_consumer_cls/`
- 基础 consumer 类：`funboost/consumers/base_consumer.py`
- 基础 publisher 类：`funboost/publishers/base_publisher.py`
- 教程：`funboost_all_docs_and_codes.md` 4.21b 章节
