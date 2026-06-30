---
name: funboost-rpc-mode
description: 当需要获取 funboost 任务的执行返回值时使用。触发场景：实现请求-响应模式、使用 AsyncResult/AioAsyncResult 获取函数返回值、查询任务状态和结果。关键词：RPC, task result, AsyncResult, AioAsyncResult, is_using_rpc_mode, 获取任务结果, 返回值。
compatibility: Python 3.7+, funboost with Redis configured
---

# Funboost RPC 模式

## 概述

RPC 模式让你获取已消费任务函数的返回值。发布者推送消息后得到 task_id，后续可查询执行结果。

**核心原则：** 在 BoosterParams 中设置 `is_using_rpc_mode=True`，然后用 `AsyncResult`（同步）或 `AioAsyncResult`（异步）获取结果。

## 适用场景

- 需要获取任务函数的返回值
- 实现请求-响应模式
- 构建等待后台任务完成的 API
- 编排依赖前置任务结果的工作流

## 前置条件

- **必须配置 Redis** — RPC 结果存储在 Redis 中
- **必须设置 `is_using_rpc_mode=True`** — 不设此项结果不会被持久化

## 速查表

| 方法 | 环境 | 返回 |
|------|------|------|
| `func.push(...)` | 同步 | `AsyncResult` 对象 |
| `func.publish(msg, task_options=...)` | 同步 | `AsyncResult` 对象 |
| `async_result.result` | 同步 | 阻塞直到结果就绪 |
| `async_result.status_and_result` | 同步 | 阻塞返回结果字典（超时返回 None） |
| `await func.aio_push(...)` | 异步 | `AioAsyncResult` 对象 |
| `await func.aio_publish(...)` | 异步 | `AioAsyncResult` 对象 |
| `await aio_result.result` | 异步 | 等待直到结果就绪 |
| `await aio_result.status_and_result` | 异步 | 返回结果字典（超时返回 None） |

## 同步 RPC 模式

> **前置条件：** RPC 模式依赖 Redis 存储结果，需在 `funboost_config.py` 中配置 `REDIS_HOST`、`REDIS_PORT`、`REDIS_PASSWORD`。详见 `funboost-broker-selection` skill。

```python
from funboost import boost, BoosterParams, BrokerEnum

@boost(BoosterParams(
    queue_name="add_queue",
    broker_kind=BrokerEnum.REDIS_ACK_ABLE,
    is_using_rpc_mode=True,  # ← 必须设置
))
def add(x: int, y: int):
    return x + y

if __name__ == "__main__":
    add.consume()

    async_result = add.push(3, 4)
    print(f"Task ID: {async_result.task_id}")
    print(f"结果: {async_result.result}")  # 阻塞等待 → 7
```

## 异步 RPC 模式

```python
import asyncio
from funboost import boost, BoosterParams, BrokerEnum, ConcurrentModeEnum

@boost(BoosterParams(
    queue_name="async_add_queue",
    broker_kind=BrokerEnum.REDIS_ACK_ABLE,
    concurrent_mode=ConcurrentModeEnum.ASYNC,
    is_using_rpc_mode=True,
))
async def async_add(x: int, y: int):
    return x + y

async def main():
    async_add.consume()

    aio_result = await async_add.aio_push(10, 20)
    result = await aio_result.result  # 等待结果 → 30
    print(f"结果: {result}")

if __name__ == "__main__":
    asyncio.run(main())
```

## 根据 task_id 查询结果

```python
from funboost import AsyncResult, AioAsyncResult

# 如果之前保存了 task_id
task_id = "some-task-id-string"

# 同步查询
result_obj = AsyncResult(task_id)
status_dict = result_obj.status_and_result  # 返回字典（超时返回 None）
print(status_dict['result'])    # 函数返回值
print(status_dict['success'])   # 是否成功

# 也可用 status_and_result_obj 获得对象（有更好的 IDE 补全）
status_obj = result_obj.status_and_result_obj  # 返回 FunctionResultStatus 对象
print(status_obj.result)
print(status_obj.success)

# 异步查询（须在 async def 内）
async def query_result():
    aio_obj = AioAsyncResult(task_id)
    status_dict = await aio_obj.status_and_result
    if status_dict:
        print(status_dict['result'])
    else:
        print("超时未获取到结果")
```

## 常见错误

| 错误 | 修正 |
|------|------|
| 忘记设置 `is_using_rpc_mode=True` | 必须加到 BoosterParams 中——否则结果不会被存储 |
| 在 async 代码中用 `AsyncResult.result` | 必须用 `AioAsyncResult` + `await` |
| 没有配置 Redis | RPC 结果依赖 Redis，需配置 `BrokerConnConfig.REDIS_*` |
| 期望 `publish()` 直接返回结果 | `publish()`/`push()` 返回结果对象，需调用 `.result` |
| 用 `MEMORY_QUEUE` 作为 broker 并期望 RPC | RPC 支持任何 broker，但结果始终存储在 Redis 中 |

> **超时行为：** `AsyncResult.result` 默认等待 1800 秒（30 分钟），可通过 `AsyncResult(task_id, timeout=30)` 设置较短超时。

## 铁律

**必须设置 `is_using_rpc_mode=True`。** 不设置此项，框架不会持久化函数返回值。未设置时 `status_and_result` 超时返回 None，`.result` 将阻塞后抛出 `HasNotAsyncResult` 异常。

## 相关 Skill

- `funboost-async-programming` — async/await 异步编程
- `funboost-faas-deploy` — HTTP 微服务部署
