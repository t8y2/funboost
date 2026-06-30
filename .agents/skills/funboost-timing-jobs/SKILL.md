---
name: funboost-timing-jobs
description: 当需要使用 funboost 创建定时/周期性任务时使用。触发场景：cron 定时调度、interval 间隔执行、ApsJobAdder 定时发布消息、APScheduler 集成。关键词：ApsJobAdder, timing, schedule, cron, interval, 定时任务, apscheduler, add_push_job, 周期执行。
compatibility: Python 3.7+, funboost with apscheduler installed
---

# Funboost 定时任务

## 概述

Funboost 集成 APScheduler 实现定时任务发布。`ApsJobAdder` 封装了 APScheduler，按 cron/interval/date 触发器定时推送消息到队列。

**核心原则：** 使用 `ApsJobAdder` — 绝对禁止直接用 `apscheduler.add_job` 调用 funboost 任务函数。

## 适用场景

- 按固定间隔运行任务（每 N 秒/分钟/小时）
- Cron 风格调度（如每天凌晨 2 点）
- 指定时间一次性执行
- 分布式调度（Redis 作业存储）

## 铁律

**绝对禁止** 使用 `apscheduler.add_job(my_task, ...)` — 这会在调度进程中直接执行函数，完全绕过队列。必须使用 `ApsJobAdder`，它在调度时间点调用 `push` 发送消息。

> **重要提醒：** `ApsJobAdder` 的第一个参数**必须是 `@boost` 装饰后的函数**（即 booster），严禁传入普通未装饰的函数。只有经过 `@boost` 装饰的函数才拥有 `.push()` 方法，`ApsJobAdder` 内部依赖此方法定时将消息推入队列。

## 速查表

| 触发器 | 用途 | 关键参数 |
|--------|------|----------|
| `interval` | 每隔 N 秒/分钟执行 | `seconds=`, `minutes=`, `hours=` |
| `cron` | 在指定时间点执行 | `hour=`, `minute=`, `day_of_week=` |
| `date` | 一次性在指定时间执行 | `run_date=datetime(...)` |

## 核心代码模式

> **注意：** 以下示例使用 `REDIS_ACK_ABLE` broker，需配置 Redis 连接。改用 `BrokerEnum.MEMORY_QUEUE` 可零依赖本地测试。

```python
from funboost import boost, BoosterParams, BrokerEnum, ApsJobAdder

@boost(BoosterParams(
    queue_name="scheduled_task",
    broker_kind=BrokerEnum.REDIS_ACK_ABLE,
    qps=5,
))
def cleanup_expired_data(table_name: str):
    print(f"清理 {table_name}")

if __name__ == "__main__":
    cleanup_expired_data.consume()

    # ⚠️ ApsJobAdder 第一个参数必须是 @boost 装饰后的函数（即 booster），
    #    禁止传入普通未装饰的函数！否则定时 push 无法进入队列。
    # 间隔：每 30 秒执行（默认 job_store_kind='memory'，重启后丢失）
    ApsJobAdder(cleanup_expired_data).add_push_job(
        trigger="interval",
        seconds=30,
        kwargs={"table_name": "sessions"},
        id="cleanup_sessions",
        replace_existing=True,
    )

    # Cron：每天凌晨 2:00 执行
    ApsJobAdder(cleanup_expired_data).add_push_job(
        trigger="cron",
        hour=2,
        minute=0,
        kwargs={"table_name": "logs"},
        id="cleanup_logs_daily",
        replace_existing=True,
    )
```

## 使用 Redis 作业存储（分布式）

```python
ApsJobAdder(cleanup_expired_data, job_store_kind="redis").add_push_job(
    trigger="interval",
    seconds=60,
    kwargs={"table_name": "cache"},
    id="cleanup_cache",
)
```

使用 `job_store_kind="redis"` 后，调度信息持久化到 Redis，进程重启不丢失，多实例部署时只有一个会触发。

## 一次性定时任务

```python
from datetime import datetime

ApsJobAdder(send_report).add_push_job(
    trigger="date",
    run_date=datetime(2026, 7, 1, 9, 0, 0),
    kwargs={"report_type": "monthly"},
    id="july_report",
)
```

## 传递位置参数

```python
ApsJobAdder(my_task).add_push_job(
    trigger="interval",
    seconds=10,
    args=(1, 2),      # push 的位置参数
    id="my_interval_job",
)
```

## 完整示例

```python
from funboost import boost, BoosterParams, BrokerEnum, ApsJobAdder


@boost(BoosterParams(
    queue_name="heartbeat_queue",
    broker_kind=BrokerEnum.REDIS_ACK_ABLE,
))
def heartbeat(service_name: str):
    import time
    print(f"[{time.strftime('%H:%M:%S')}] 心跳来自 {service_name}")

if __name__ == "__main__":
    heartbeat.consume()

    ApsJobAdder(heartbeat, job_store_kind="redis").add_push_job(
        trigger="interval",
        seconds=5,
        kwargs={"service_name": "api-server"},
        id="api_heartbeat",
    )
```

## 常见错误

| 错误 | 修正 |
|------|------|
| `apscheduler.add_job(my_task, ...)` | 使用 `ApsJobAdder(my_task).add_push_job(...)` |
| 缺少 `id` 参数 | 建议设置唯一 `id` 防止重复注册（非必填但强烈推荐） |
| 没有启动消费者 | `ApsJobAdder` 只负责定时发布，消费端需要 `func.consume()` |
| 用 `job_store_kind="redis"` 但没配 Redis | 确保 `BrokerConnConfig.REDIS_HOST` 等已配置 |
| 将函数参数直接传给 `add_push_job` | 使用 `args=()` 或 `kwargs={}` 传递任务参数 |

## 相关 Skill

- `using-funboost-basics` — 基础使用入门
- `funboost-funweb-ops` — Web 管理界面运维
