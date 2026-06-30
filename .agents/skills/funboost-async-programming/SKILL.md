---
name: funboost-async-programming
description: 当需要在 funboost 中使用异步（async/await）编程时使用。触发场景：async def 消费函数、aio_push/aio_publish、concurrent_mode=ASYNC、event loop 报错。关键词：async, await, asyncio, aio_push, aio_publish, ConcurrentModeEnum.ASYNC, 异步消费, 协程。
compatibility: Python 3.7+, funboost
---

# Funboost 异步编程

## 概述

funboost 对 asyncio 生态有直接支持：**消费**支持 `async def` 函数，**发布**支持 `aio_push` / `aio_publish`，**RPC 结果**支持 `AioAsyncResult`。远超 Celery 对 async 的支持。

**核心原则：** 异步消费函数用 `async def`；异步发布用 `await func.aio_push()`；异步获取 RPC 结果用 `await AioAsyncResult(...).result`，**禁止**在 async 环境中用同步的 `AsyncResult.result`（会阻塞 event loop）。

## 适用场景

- 消费函数内部已是 `async def`（aiohttp、httpx、aiomysql 等）
- 在 FastAPI / asyncio 应用中发布 funboost 任务
- 需要 `await` 等待 RPC 结果，而非阻塞 event loop
- 高并发 IO 密集型任务，希望用协程而非线程

## 铁律（绝对不可违反）

1. **异步 RPC 必须用 `AioAsyncResult`** — 禁止在 `async def` 里调用 `async_result.result`
2. **RPC 模式必须设置 `is_using_rpc_mode=True`** — 且需配置 Redis（结果存 Redis）（MEMORY_QUEUE 场景可使用 `publisher.get_future()` / `publisher.get_aio_future()` 替代 Redis RPC）
3. **`async def` 消费函数内禁止同步阻塞 IO** — 如 `time.sleep`、`requests.get`。注意：ASYNC 模式仍支持同步 `def` 消费函数（会在线程池中执行）
4. **禁止臆造 API** — 不存在 `async_consume`、`aio_consume` 等，启动消费仍是 `func.consume()`
5. **必须使用 `BoosterParams` 对象** — 禁止向 `@boost` 传递裸参数

## 速查表

| 操作 | 代码 |
|------|------|
| 异步消费函数 | `@boost(BoosterParams(..., concurrent_mode=ConcurrentModeEnum.ASYNC))` + `async def` |
| 异步发布（业务参数） | `await func.aio_push(x, y)` |
| 异步发布（字典 + 控制参数） | `await func.aio_publish({"x": 1}, task_options=TaskOptions(...))` |
| 异步 RPC 结果 | `aio_result = await func.aio_push(...); await aio_result.result` |
| 按 task_id 异步查结果 | `await AioAsyncResult(task_id).status_and_result` |
| 启动消费 | `func.consume()`（同步调用，内部自动跑协程池） |
| 解决 loop 绑定问题 | `specify_async_loop=loop` |
| 获取任务上下文 | `from funboost import fct; fct.task_id`（async 中同样可用） |

## 1. 异步消费函数的正确写法

### 1.1 ASYNC 协程模式（推荐用于纯 async 生态）

```python
import asyncio
from funboost import boost, BoosterParams, BrokerEnum, ConcurrentModeEnum, enable_ctrl_c_quit_on_windows

@boost(BoosterParams(
    queue_name="async_fetch_queue",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    concurrent_mode=ConcurrentModeEnum.ASYNC,  # ← 关键：协程并发池
    concurrent_num=100,
    qps=10,
))
async def async_fetch(url: str):
    await asyncio.sleep(0.1)  # 模拟 async IO
    print(f"fetch {url}")
    return url

if __name__ == "__main__":
    for i in range(5):
        async_fetch.push(f"https://example.com/{i}")
    async_fetch.consume()
    enable_ctrl_c_quit_on_windows()
```

**要点：**
- 函数必须是 `async def`
- `concurrent_mode=ConcurrentModeEnum.ASYNC` 使用 `AsyncPoolExecutor`，所有协程在同一 loop 中并发
- 函数内**只能**用 `await asyncio.sleep()`，**不能**用 `time.sleep()`

### 1.2 THREADING 模式也能运行 async def（更省心）

默认 `concurrent_mode=ConcurrentModeEnum.THREADING` 时，`FlexibleThreadPool` 会自动检测 `async def` 并在每个线程内临时创建 loop 运行协程。**不必为了 async 函数就切换到 ASYNC 模式**。

```python
from funboost import boost, BoosterParams, BrokerEnum

@boost(BoosterParams(queue_name="thread_async_queue", broker_kind=BrokerEnum.MEMORY_QUEUE))
async def my_async_task(x):
    import asyncio
    await asyncio.sleep(1)
    print(x)

if __name__ == "__main__":
    my_async_task.push(1)
    my_async_task.consume()
```

**选择建议：**
- 已有大量 async 库、追求协程轻量 → `ConcurrentModeEnum.ASYNC`
- 混合 sync/async 函数、不想处理 loop 问题 → 默认 `THREADING`（不写 concurrent_mode）

## 2. 异步发布

`aio_push` / `aio_publish` 通过 `loop.run_in_executor` 将同步发布转为异步，无需异步消息队列客户端。

```python
import asyncio
from funboost import boost, BoosterParams, BrokerEnum, ConcurrentModeEnum, TaskOptions

@boost(BoosterParams(
    queue_name="aio_publish_demo",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    concurrent_mode=ConcurrentModeEnum.ASYNC,
))
async def process(x: int):
    await asyncio.sleep(0.5)
    print(f"process {x}")

async def main():
    # 方式1：aio_push — 传业务参数
    for i in range(3):
        await process.aio_push(i)

    # 方式2：aio_publish — 传字典 + 框架控制参数
    await process.aio_publish(
        {"x": 99},
        task_options=TaskOptions(countdown=2),
    )

if __name__ == "__main__":
    asyncio.run(main())
    process.consume()
```

| 方法 | 入参 | 返回 |
|------|------|------|
| `await func.aio_push(*args, **kwargs)` | 业务参数 | `AioAsyncResult` |
| `await func.aio_publish(msg_dict, task_options=...)` | 字典 + 可选 TaskOptions | `AioAsyncResult` |

> 局域网发布通常 < 1ms，在 FastAPI 里偶尔用同步 `push()` 也可接受；对外网 MQ 发布建议用 `aio_push`。

## 3. 异步 RPC 结果获取

RPC 模式需同时满足：**`is_using_rpc_mode=True`** + **Redis 已配置**。

```python
import asyncio
from funboost import boost, BoosterParams, BrokerEnum, ConcurrentModeEnum, AioAsyncResult

@boost(BoosterParams(
    queue_name="async_rpc_add",
    broker_kind=BrokerEnum.REDIS_ACK_ABLE,
    concurrent_mode=ConcurrentModeEnum.ASYNC,
    is_using_rpc_mode=True,  # ← 必须
))
async def async_add(x: int, y: int):
    await asyncio.sleep(0.1)
    return x + y

async def main():
    async_add.consume()

    # 方式1：aio_push 直接返回 AioAsyncResult
    aio_result = await async_add.aio_push(10, 20)
    print(await aio_result.result)  # 30

    # 方式2：同步 push + AioAsyncResult 包装（适合 FastAPI 中已 push 的场景）
    sync_result = async_add.push(1, 2)
    status = await AioAsyncResult(sync_result.task_id).status_and_result
    print(status["result"])  # 3

if __name__ == "__main__":
    asyncio.run(main())
```

**MEMORY_QUEUE 专用：** 不依赖 Redis RPC 时，可用 `publisher.get_aio_future()`：

```python
future = async_task.publisher.get_aio_future(1, 2)
result_status = await future
print(result_status.result)
```

## 4. 同步函数 vs 异步函数：区别与选择

| 维度 | 同步 `def` | 异步 `async def` |
|------|-----------|-----------------|
| 默认并发模式 | `THREADING`（多线程） | `ASYNC` 或 `THREADING` 均可 |
| 函数内 IO | `requests`、`time.sleep` | `httpx`、`await asyncio.sleep` |
| 发布方式 | `func.push()` | `await func.aio_push()`（async 环境中） |
| RPC 结果 | `async_result.result`（阻塞） | `await AioAsyncResult(...).result` |
| 复杂度 | 低，推荐大多数用户 | 高，涉及跨线程 loop 问题 |
| 适用 | CPU 密集、简单 IO、混合代码 | 已有 asyncio 生态（FastAPI + aiohttp） |

**文档建议：** funboost 对 async 支持很强，但**不鼓励非资深开发者用 async def 定义消费函数**。若业务函数已是 async 写法且复用 async 库，再选 ASYNC 模式。

## 5. 常见 Event Loop 报错及解决

### 5.1 `attached to a different loop`

**原因：** ASYNC 模式在**子线程**中运行 loop；部分库（aiohttp、aiomysql）的连接池绑定创建时的 loop，跨 loop 使用会报错。httpx、sqlalchemy 通常无此问题。

**解决：** 传递 `specify_async_loop`

```python
import asyncio
import aiohttp
from funboost import boost, BoosterParams, BrokerEnum, ConcurrentModeEnum

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

@boost(BoosterParams(
    queue_name="aiohttp_task",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    concurrent_mode=ConcurrentModeEnum.ASYNC,
    specify_async_loop=loop,  # ← 共享全局连接池时需要；函数内临时创建可省略
))
async def fetch(url: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            return (await resp.text())[:50]
```

**不需要 specify_async_loop 的情况：** 函数内临时创建 Session（如上例），不用全局连接池。

### 5.2 `context manager should be used inside a task`

**原因：** 与 5.1 同类——异步连接池/Session 在错误的 loop 或上下文中使用。

**解决：** 同上，使用 `specify_async_loop`；或在函数内临时创建资源而非共享全局池。

### 5.3 `RuntimeError: This event loop is already running`（nested loop）

**原因：** 主线程 loop 已 `run_forever()`，又在同一线程调用 `asyncio.run()` 或 `loop.run_until_complete()`。

**解决：**
- 不要在已运行 loop 的线程里再嵌套 `asyncio.run()`
- FastAPI/uvicorn 已管理 loop，业务代码用 `await`，不要额外 `asyncio.run()`
- 若需 `specify_async_loop`，注意启动顺序：先配置 booster，再启动 `loop.run_forever()`，避免主/子线程 loop 竞争

### 5.4 在 async 代码中用 `AsyncResult.result` 阻塞 event loop

**现象：** FastAPI 接口卡死，所有请求排队。

**解决：** 改用 `AioAsyncResult`

```python
# ❌ 错误 — 阻塞整个 event loop
async def api_bad():
    r = my_task.push(1)
    return r.result

# ✅ 正确
async def api_good():
    r = my_task.push(1)
    return await AioAsyncResult(r.task_id).result
```

### 5.5 ASYNC 模式中使用 `time.sleep` / `requests.get`

**现象：** 整个协程池被卡死，QPS 骤降。

**解决：** 全部改为 async 等价物（`await asyncio.sleep`、`httpx` / `aiohttp`）。

## 6. 在 FastAPI / 异步框架中使用 funboost

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from funboost import boost, BoosterParams, BrokerEnum, AioAsyncResult, ConcurrentModeEnum

@boost(BoosterParams(
    queue_name="web_async_task",
    broker_kind=BrokerEnum.REDIS_ACK_ABLE,
    concurrent_mode=ConcurrentModeEnum.ASYNC,
    is_using_rpc_mode=True,
))
async def handle_order(order_id: int):
    import asyncio
    await asyncio.sleep(1)
    return f"order {order_id} done"

@asynccontextmanager
async def lifespan(app: FastAPI):
    handle_order.consume()  # 应用启动时启动消费
    yield

app = FastAPI(lifespan=lifespan)

@app.post("/order/{order_id}")
async def create_order(order_id: int):
    # 推荐：aio_push + await result
    aio_result = await handle_order.aio_push(order_id)
    return {"result": await aio_result.result}

@app.post("/order/sync-push/{order_id}")
async def create_order_sync_push(order_id: int):
    # 可接受：同步 push（通常很快）+ AioAsyncResult 等结果
    async_result = handle_order.push(order_id)
    status = await AioAsyncResult(async_result.task_id).status_and_result
    return {"result": status["result"] if status else None}
```

**要点：**
- 在 `lifespan` / `startup` 中调用 `consume()`，不要在每个请求里启动
- 异步路由中**禁止** `async_result.result`，必须用 `AioAsyncResult`
- 也可使用 `funboost.faas.fastapi_router` 一键暴露 HTTP 发布接口（见 funboost-faas-deploy skill）

## 7. 异步消费 + 同步消费混合场景

同一进程可同时运行 async 消费函数和 sync 消费函数，分别 `consume()` 即可：

```python
import asyncio
import time
from funboost import boost, BoosterParams, BrokerEnum, ConcurrentModeEnum, enable_ctrl_c_quit_on_windows

@boost(BoosterParams(
    queue_name="mixed_async_queue",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    concurrent_mode=ConcurrentModeEnum.ASYNC,
    is_using_rpc_mode=True,
))
async def async_worker(x):
    await asyncio.sleep(0.5)
    return f"async {x}"

@boost(BoosterParams(
    queue_name="mixed_sync_queue",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    is_using_rpc_mode=True,
))
def sync_worker(x):
    time.sleep(0.5)
    return f"sync {x}"

if __name__ == "__main__":
    async def publish_all():
        for i in range(3):
            await async_worker.aio_push(i)
        for j in range(3):
            sync_worker.push(j)  # 同步函数仍用 push

    asyncio.run(publish_all())

    async_worker.consume()
    sync_worker.consume()
    enable_ctrl_c_quit_on_windows()
```

**注意：**
- 两种函数使用**不同 queue_name**（不同 BoosterParams）
- 启动：`func1.consume(); func2.consume()` 连续调用，**不要**用 `threading.Thread` 包装
- async 函数链式调度下游：在 async 消费函数内可 `await downstream.aio_push(...)`

## 8. 完整可运行示例

### 8.1 无 Redis 依赖（MEMORY_QUEUE + get_aio_future）

```python
"""funboost 异步编程最小完整示例 — 可直接 python 运行，无需 Redis"""
import asyncio
import os
import time

from funboost import boost, BoosterParams, BrokerEnum, ConcurrentModeEnum

@boost(BoosterParams(
    queue_name="skill_async_demo_q",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    concurrent_mode=ConcurrentModeEnum.ASYNC,
    concurrent_num=20,
))
async def async_task(n: int):
    await asyncio.sleep(0.3)
    return n * n

@boost(BoosterParams(
    queue_name="skill_sync_demo_q",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
))
def sync_task(n: int):
    time.sleep(0.3)
    return n + 1


async def async_main():
    # 异步发布
    for i in range(3):
        await async_task.aio_push(i)

    # 同步发布（在 async 函数中也可偶尔使用）
    sync_task.push(100)

    # MEMORY_QUEUE 异步获取 RPC 结果（不依赖 Redis）
    status = await async_task.publisher.get_aio_future(7)
    print(f"async_task(7) = {status.result}")

    status2 = await sync_task.publisher.get_aio_future(10)
    print(f"sync_task(10) = {status2.result}")


if __name__ == "__main__":
    async_task.consume()
    sync_task.consume()
    asyncio.run(async_main())
    time.sleep(2)
    os._exit(0)
```

### 8.2 带 Redis 的 RPC 完整示例

需配置 `funboost_config.py` 中 Redis：

```python
import asyncio
from funboost import boost, BoosterParams, BrokerEnum, ConcurrentModeEnum, AioAsyncResult

@boost(BoosterParams(
    queue_name="skill_redis_async_rpc",
    broker_kind=BrokerEnum.REDIS_ACK_ABLE,
    concurrent_mode=ConcurrentModeEnum.ASYNC,
    is_using_rpc_mode=True,
))
async def add(x: int, y: int):
    await asyncio.sleep(0.1)
    return x + y

async def main():
    add.consume()
    aio_result = await add.aio_push(3, 4)
    print(await aio_result.result)  # 7

if __name__ == "__main__":
    asyncio.run(main())
```

## 9. 常见错误对照表

| 错误现象 / 报错信息 | 原因 | 正确做法 |
|---------------------|------|----------|
| `attached to a different loop` | aiohttp/aiomysql 等连接池绑定了另一个 loop | 设置 `specify_async_loop=loop` |
| `context manager should be used inside a task` | 异步资源在错误 loop/上下文使用 | 同上，或函数内临时创建连接 |
| `RuntimeError: This event loop is already running` | 在已运行 loop 中嵌套 `asyncio.run()` | 只用 `await`，不嵌套 run |
| FastAPI 所有请求卡死 | 用了 `async_result.result` 阻塞 loop | `await AioAsyncResult(task_id).result` |
| ASYNC 模式 QPS 极低 / 假死 | 函数内用了 `time.sleep` / `requests` | 改用 `await asyncio.sleep` / httpx |
| RPC 超时 / `HasNotAsyncResult` | 未设 `is_using_rpc_mode=True` 或未配 Redis | 开启 RPC 并配置 Redis |
| 在 async 路由里 `await func.push()` | `push` 是同步方法，不会 await | 用 `await func.aio_push()` |
| 臆造 `from funboost import async_consume` | 该 API 不存在 | 使用 `func.consume()` |
| async 消费函数不执行 | 忘记 `consume()` | 启动消费后再发布 |
| 相同参数 RPC 永远无结果 | 同时开了 `do_task_filtering=True` | RPC 与任务去重不要同时使用 |

## 相关 BoosterParams 字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `concurrent_mode` | `str` | 默认 `THREADING`；纯协程用 `ConcurrentModeEnum.ASYNC` |
| `concurrent_num` | `int` | 协程/线程并发数，默认 50 |
| `specify_async_loop` | `asyncio.AbstractEventLoop` | 指定 loop，解决 `attached to a different loop` |
| `is_auto_start_specify_async_loop_in_child_thread` | `bool` | 默认 True；False 时需手动 `loop.run_forever()` |
| `is_using_rpc_mode` | `bool` | RPC 模式，异步结果获取前置条件 |

## 相关 Skill

- `funboost-memory-queue-pool` — 内存队列替代线程池
- `funboost-rpc-mode` — 获取任务执行返回值

## 参考

- 文档 4.12（asyncio 并发）、4.6.5（asyncio RPC）、4b.3（全 asyncio 生态）
- FAQ 6.26（loop 报错）、6.29.3（ASYNC 模式推荐）
- 示例代码：`test_frame/full_asyncio_demo/`
