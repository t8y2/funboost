---
name: funboost-memory-queue-pool
description: 当需要用 funboost 的内存队列替代传统线程池/协程池、或需要零中间件依赖的本地并发时使用。触发场景：不需要分布式但需要并发控制、替代 ThreadPoolExecutor、MEMORY_QUEUE、FunboostPool、get_future。关键词：MEMORY_QUEUE, MemoryFunboostPool, FunboostPool, 内存队列, 本地并发, 线程池替代。
compatibility: Python 3.7+, funboost
---

# Funboost 内存队列与任务池

## 概述

`BrokerEnum.MEMORY_QUEUE` 是 funboost 中 **SSS 级** broker——不是玩具，而是替代 `ThreadPoolExecutor` / 协程池 / tomorrow 装饰器的首选方案。发布和消费在同一 Python 进程内，零中间件、零序列化、极致性能。

**核心原则：** 不需要分布式时，优先用内存队列；需要分布式时，只改 `broker_kind` 一行，业务代码不变。

## 适用场景

- 本地并发任务，不需要 Redis/RabbitMQ 等中间件
- 用 `@boost` 替代 `ThreadPoolExecutor.submit()`
- 函数入参/返回值含不可 JSON/pickle 序列化的对象（如数据库连接、自定义类实例）
- 需要 QPS 控频 + 并发控制 + 重试 + 超时，但不想手写一堆装饰器
- 开发阶段用内存队列，上线后一行切换到 Redis/RabbitMQ

---

别名：`BrokerEnum.LOCAL_PYTHON_QUEUE` = `MEMORY_QUEUE`。

---

## 2. 为什么选择内存队列

1. **零中间件依赖** — 不需要安装/配置 Redis、RabbitMQ 等，开箱即用
2. **零序列化开销** — 消息直接在进程内存中传递，任意 Python 对象都可作为入参（不可 JSON/pickle 的类型也行）
3. **无 socket IO** — `queue.Queue` 纯内存操作，比任何网络 broker 都快
4. **同进程发布+消费** — funboost 的 `consume()` 就在当前脚本进程启动；Celery worker 是独立进程，无法共享内存队列，所以 memory 在 Celery 中是二等公民，在 funboost 中是 **超一等公民**
5. **背压/解耦/限流** — 内存 queue 无处不在（`ThreadPoolExecutor` 内部也有 `_work_queue`），funboost 在此基础上叠加 30+ 控制能力

---

## 3. 作为「超级装饰器」

用 `broker_kind=BrokerEnum.MEMORY_QUEUE` 的 `@boost`，一个装饰器抵得上多个常规装饰器叠加：

| 能力 | BoosterParams 字段 | 说明 |
|------|-------------------|------|
| QPS 控频 | `qps=10` | 精确到小数（`0.01` = 每 100 秒 1 次） |
| 并发控制 | `concurrent_num=50` | 配合智能线程池自动扩缩 |
| 自动重试 | `max_retry_times=3` | 异常自动重试 |
| 指数退避 | `is_using_advanced_retry=True` | sleep / requeue 两种模式 |
| 函数超时 | `function_timeout=30` | 超时强制终止 |
| 任务去重 | `do_task_filtering=True` | 入参去重（需 Redis） |
| 死信队列 | `is_push_to_dlx_queue_when_retry_max_times=True` | 重试耗尽进 DLX |
| 运行时段 | `allow_run_time_cron='* 9-17 * * 1-5'` | cron 表达式限制 |

裸 `ThreadPoolExecutor` 只有并发，没有控频、重试、超时、去重等能力。

---

## 4. MemoryFunboostPool / FunboostPool 用法

funboost 提供 API 兼容 `ThreadPoolExecutor` 的任务池，**只需把 `ThreadPoolExecutor(...)` 换成 `MemoryFunboostPool(...)` 或 `FunboostPool(...)`**，`pool.submit(fn, *args)` 用法完全一致。

### 4.1 MemoryFunboostPool — 纯内存，快速替代线程池

固定使用 `MEMORY_QUEUE`，固定 `max_retry_times=0`（复刻原生线程池不重试行为），自动启动消费。

```python
from funboost import MemoryFunboostPool

pool = MemoryFunboostPool(concurrent_num=10, qps=5)
future = pool.submit(my_func, arg1, arg2)
result = future.result(timeout=10)  # 默认直接返回函数返回值
```

构造参数（源码 `funboost/core/funboost_pool.py`）：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `concurrent_num` | `4` | 最大并发数 |
| `qps` | `None` | 每秒执行次数，None 不限频 |
| `is_future_direct_ret_result` | `True` | `True` 时 `future.result()` 返回函数返回值；`False` 返回 `FunctionResultStatus` |
| `is_auto_start_consuming_message` | `True` | 是否自动 `consume()` |

队列名自动生成 `universal_pool_{id(self)}`，无需手动指定。

### 4.2 FunboostPool — 全功能，可切换任意 broker

接受完整 `BoosterParams`，支持 Redis/RabbitMQ 等分布式 broker + 持久化。

```python
from funboost import FunboostPool, BoosterParams, BrokerEnum

pool = FunboostPool(
    BoosterParams(
        queue_name='persistent_pool',
        broker_kind=BrokerEnum.REDIS_ACK_ABLE,
        concurrent_num=10,
        qps=10,
        max_retry_times=5,
    ),
    is_need_result=True,  # 分布式 broker 需开启才能 future.result()
)
future = pool.submit(my_func, arg1, arg2)
result = future.result(timeout=30)
```

| 对比 | MemoryFunboostPool | FunboostPool |
|------|-------------------|--------------|
| 持久化 | 无（内存） | 支持（消息队列） |
| 分布式 | 不支持 | 支持 |
| 配置灵活度 | 低（并发数、QPS） | 高（全部 BoosterParams） |
| 重试/超时等 | 固定不重试 | 完全可配 |
| API | 兼容 ThreadPoolExecutor | 兼容 ThreadPoolExecutor |

**FunboostPool 额外能力（MemoryFunboostPool 没有）：**
- 支持分布式 broker（Redis、RabbitMQ、Kafka 等），任务可跨进程/跨机器
- 完整 BoosterParams 配置（重试、超时、RPC 等全部可用）
- 非 MEMORY broker 时，函数通过模块路径字符串发送（消费端自动 import 执行）

---

## 5. get_future() 获取 Future 对象

MEMORY_QUEUE **独有**能力：不依赖 Redis RPC，直接在进程内通过 `Future` 获取结果。

### 5.1 在 @boost 任务上使用

```python
import concurrent.futures
from funboost import boost, BoosterParams, BrokerEnum

@boost(BoosterParams(queue_name="demo", broker_kind=BrokerEnum.MEMORY_QUEUE, concurrent_num=10))
def add(x, y):
    return x + y

if __name__ == "__main__":
    add.consume()
    future: concurrent.futures.Future = add.publisher.get_future(1, 2)
    status = future.result(timeout=10)       # 返回 FunctionResultStatus
    print(status.result, status.success)     # 3, True
```

异步消费函数用 `get_aio_future()`：

```python
future = async_task.publisher.get_aio_future(1, y=2)
result_status = await future  # 在 async 上下文中 await
```

### 5.2 原理

`get_future()` 创建 `concurrent.futures.Future`，将其放入消息体 `extra['_memory_call_future']` 中随消息流转（内存队列不序列化，Future 对象可直接传递）。消费端执行完毕后通过 `future.set_result(FunctionResultStatus)` 回传。

### 5.3 MemoryFunboostPool 内部也使用 get_future

`MemoryFunboostPool.submit()` 内部调用 `self.booster.publisher.get_future(fn, args, kwargs)`，再包装为 `FunboostFuture` 返回。

---

## 6. 与分布式 broker 的切换

**只改 `broker_kind` 一行**，任务函数、发布/消费代码不变：

```python
# 本地开发 — 内存队列，零依赖
@boost(BoosterParams(queue_name='my_task', broker_kind=BrokerEnum.MEMORY_QUEUE, qps=10))
def my_task(url):
    ...

# 上线 — 切换到 Redis，函数体零改动
@boost(BoosterParams(queue_name='my_task', broker_kind=BrokerEnum.REDIS_ACK_ABLE, qps=10))
def my_task(url):
    ...
```

FunboostPool 同样一行切换：

```python
# 开发
pool = MemoryFunboostPool(concurrent_num=10, qps=5)

# 生产
pool = FunboostPool(BoosterParams(queue_name='pool', broker_kind=BrokerEnum.REDIS_ACK_ABLE, concurrent_num=10, qps=5), is_need_result=True)
```

> 切换到非 MEMORY_QUEUE broker 后，`get_future()` 不可用；需用 `is_using_rpc_mode=True` + `AsyncResult.result` 或 FunboostPool 的 `is_need_result=True`。

---

## 7. 完整代码示例

### 示例 A：@boost 替代 ThreadPoolExecutor（4.23 章节模式）

```python
import time
from funboost import boost, BoosterParams, BrokerEnum

# 传统写法：
# from concurrent.futures import ThreadPoolExecutor
# pool = ThreadPoolExecutor(5)
# for i in range(100):
#     pool.submit(f, i, i * 2)

@boost(BoosterParams(queue_name='test1', broker_kind=BrokerEnum.MEMORY_QUEUE, concurrent_num=5, qps=10))
def f(x, y):
    print(f'{x} + {y} = {x + y}')
    time.sleep(1)

if __name__ == '__main__':
    f.consume()
    for i in range(100):
        f.push(i, i * 2)
```

### 示例 B：MemoryFunboostPool 一行替换 ThreadPoolExecutor

```python
from funboost import MemoryFunboostPool

def process(item):
    return item * 2

with MemoryFunboostPool(concurrent_num=5, qps=20) as pool:
    futures = [pool.submit(process, i) for i in range(100)]
    results = [f.result(timeout=30) for f in futures]
    print(results[:5])  # [0, 2, 4, 6, 8]
```

### 示例 C：get_future 同步/异步 RPC

```python
import time
import asyncio
import concurrent.futures
from funboost import boost, BoosterParams, BrokerEnum, ConcurrentModeEnum

@boost(BoosterParams(queue_name="sync_q", broker_kind=BrokerEnum.MEMORY_QUEUE, qps=2, concurrent_num=10))
def sync_task(x, y):
    time.sleep(0.5)
    return x + y

@boost(BoosterParams(queue_name="async_q", broker_kind=BrokerEnum.MEMORY_QUEUE,
                     concurrent_mode=ConcurrentModeEnum.ASYNC, concurrent_num=10))
async def async_task(x, y):
    await asyncio.sleep(0.5)
    return x * y

if __name__ == '__main__':
    sync_task.consume()
    async_task.consume()

    # 同步 Future
    f = sync_task.publisher.get_future(3, 4)
    status = f.result(timeout=10)
    print(f'同步: {status.result}')  # 7

    # 异步 Future
    async def run_async():
        af = async_task.publisher.get_aio_future(3, 4)
        status = await af
        print(f'异步: {status.result}')  # 12

    asyncio.run(run_async())
```

### 示例 D：不可序列化对象作为入参

```python
from funboost import boost, BoosterParams, BrokerEnum

class DBConnection:
    def query(self, sql):
        return f'result of {sql}'

@boost(BoosterParams(queue_name='nosql_demo', broker_kind=BrokerEnum.MEMORY_QUEUE))
def run_query(conn: DBConnection, sql: str):
    return conn.query(sql)

if __name__ == '__main__':
    run_query.consume()
    conn = DBConnection()  # 不可 pickle 的对象
    run_query.push(conn, 'SELECT 1')  # MEMORY_QUEUE 直接传递对象引用
```

---

## 8. 注意事项

### 8.1 进程退出后消息丢失

内存队列数据存在 Python 进程内存中。**进程退出、重启、kill -9 后所有未消费和正在执行的任务全部丢失**，无法断点续传。

### 8.2 不支持持久化

与 `SQLITE_QUEUE`、`REDIS_ACK_ABLE` 等不同，MEMORY_QUEUE 不做任何磁盘持久化。

### 8.3 不支持跨进程 / 跨脚本 / 跨机器

- 发布者和消费者必须在 **同一个 Python 进程** 内
- 不能用 `multi_process_consume()` 跨进程共享 MEMORY_QUEUE 任务（多进程各自有独立内存）
- 不能一个脚本 `push`、另一个脚本 `consume`

### 8.4 RPC 模式差异

- MEMORY_QUEUE：`get_future()` / `get_aio_future()` 零依赖获取结果
- 其他 broker：需 `is_using_rpc_mode=True` + Redis 存储 RPC 结果
- FunboostPool 在非 MEMORY_QUEUE 模式下，`is_need_result=True` 会自动开启 RPC

### 8.5 concurrent_num 不要过大

`concurrent_num` 同时作为预取消息的有界队列大小。设过大（如 100 万）会导致内存暴涨。建议 **1000 以下**，配合 `qps` 控频即可。

---

## 铁律

1. **同进程原则** — MEMORY_QUEUE 要求 push 和 consume 在同一进程；分离部署请换 broker
2. **get_future 仅 MEMORY_QUEUE** — 其他 broker 用 `AsyncResult` / `is_using_rpc_mode`
3. **MemoryFunboostPool 无 queue_name 参数** — 队列名自动生成

## 相关 Skill

- `funboost-broker-selection` — Broker 中间件选型
- `funboost-async-programming` — async/await 异步编程
