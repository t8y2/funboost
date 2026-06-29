---
name: funboost-workflow
description: 当需要编排多个 funboost 任务按顺序或并行执行时使用。触发场景：chain 串行流水线、group 并行执行、chord 扇出聚合、DAG 工作流、任务依赖编排。关键词：workflow, chain, group, chord, pipeline, DAG, 工作流, 任务依赖, fan-out, fan-in, WorkflowBoosterParams。
compatibility: Python 3.7+, funboost with workflow module
---

# Funboost 工作流编排

## 概述

Funboost workflow 模块提供类似 Celery 的原语（`chain`、`group`、`chord`），用于编排多步骤任务流水线，但比 Celery 更简单。

**核心原则：** 用 `chain`（串行）、`group`（并行）、`chord`（扇出后聚合）组合任务编排流水线。

## 适用场景

- 多步骤处理流水线（下载 -> 处理 -> 上传）
- 扇出/扇入模式（并行处理，然后汇总）
- 任务依赖——步骤 B 需要步骤 A 的结果
- 复杂多步骤工作流

## 速查表

| 原语 | 模式 | 说明 |
|------|------|------|
| `chain(a, b, c)` | A -> B -> C | 串行执行 |
| `group(a, b, c)` | A // B // C | 并行执行 |
| `chord(group(...), callback.s())` | (A // B // C) -> D | 并行后聚合 |
| `func.s(*args)` | — | 创建签名（懒任务引用） |
| `func.si(*args)` | — | 创建不可变签名（忽略上游结果） |

## 核心代码模式

```python
from funboost import boost, BoosterParams, BrokerEnum
from funboost.workflow import chain, group, chord, WorkflowBoosterParams

@boost(WorkflowBoosterParams(
    queue_name="download_queue",
    broker_kind=BrokerEnum.REDIS_ACK_ABLE,
    is_using_rpc_mode=True,
))
def download(url: str):
    print(f"下载 {url}")
    return f"/tmp/{url.split('/')[-1]}"

@boost(WorkflowBoosterParams(
    queue_name="process_queue",
    broker_kind=BrokerEnum.REDIS_ACK_ABLE,
    is_using_rpc_mode=True,
))
def process(file_path: str, resolution: str = "720p"):
    print(f"处理 {file_path}，分辨率 {resolution}")
    return f"{file_path}.{resolution}.mp4"

@boost(WorkflowBoosterParams(
    queue_name="notify_queue",
    broker_kind=BrokerEnum.REDIS_ACK_ABLE,
    is_using_rpc_mode=True,
))
def notify(results: list, user_id: int):
    print(f"通知用户 {user_id}：{len(results)} 个文件已就绪")
    return "done"
```

## Chain — 串行流水线

```python
workflow = chain(
    download.s("https://example.com/video.mp4"),
    process.s(resolution="1080p"),
)
result = workflow.apply()
```

每个任务的返回值作为下一个任务的第一个参数传入（使用 `.si()` 可忽略上游结果）。

## Group — 并行执行

```python
parallel_tasks = group(
    process.s("/tmp/video.mp4", resolution="360p"),
    process.s("/tmp/video.mp4", resolution="720p"),
    process.s("/tmp/video.mp4", resolution="1080p"),
)
result = parallel_tasks.apply()
```

所有任务并发运行。

## Chord — 扇出后聚合

```python
workflow = chord(
    group(
        process.s("/tmp/v.mp4", resolution=r)
        for r in ["360p", "720p", "1080p"]
    ),
    notify.s(user_id=1001),
)
result = workflow.apply()
```

group 中所有任务并行执行；全部完成后，结果收集为列表传给回调函数。

## 复杂嵌套流水线

```python
workflow = chain(
    download.s("https://example.com/video.mp4"),
    chord(
        group(
            process.s(resolution=r)
            for r in ["360p", "720p", "1080p"]
        ),
        notify.s(user_id=1001),
    ),
)
result = workflow.apply()
```

## 重要注意事项

1. **`WorkflowBoosterParams`** — 工作流任务推荐用这个（已默认 `is_using_rpc_mode=True` 并注入必要 Mixin）
2. **导入 `funboost.workflow`** — `.s()` / `.si()` 方法仅在导入 workflow 模块后才可用（如 `from funboost.workflow import chain, ...`）
3. **`.s()` 方法** — 创建签名（懒引用），用于工作流组合；`.si()` 为不可变签名，忽略上游结果
4. **统一 broker** — 工作流中的所有任务建议使用相同的 broker
5. **需配置 Redis** — 工作流依赖 RPC（即使用非 Redis broker 也需要 Redis 存储 RPC 结果）
6. **启动消费者** — 每个任务函数都需 `func.consume()` 才能执行

## 常见错误

| 错误 | 修正 |
|------|------|
| 工作流任务用 `BoosterParams` | 推荐用 `WorkflowBoosterParams`（已内置 RPC 和 Mixin） |
| 忘记 import funboost.workflow | `.s()` 方法需要导入 workflow 模块后才可用 |
| 直接调用 `func(args)` 而非 `func.s(args)` | `.s()` 创建签名，不要直接调用函数 |
| 工作流中混用不同 broker | 所有工作流任务保持相同 broker |
| 没有启动消费者 | 每个任务函数都需要 `func.consume()` 运行 |
