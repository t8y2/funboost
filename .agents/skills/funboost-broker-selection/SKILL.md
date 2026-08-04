---
name: funboost-broker-selection
description: 当需要为 funboost 任务选择消息中间件时使用。触发场景：对比 Redis/RabbitMQ/Kafka/本地队列、配置 broker 连接、设置 broker_exclusive_config。关键词：BrokerEnum, broker_kind, Redis, RabbitMQ, Kafka, MQTT, 中间件选型, 消息队列选择。
---

# Funboost 中间件选型

## 概述

Funboost 支持 50+ 种消息中间件。根据可靠性需求、基础设施和性能要求选择即可。

**核心原则：** 只需修改 `broker_kind` 参数——你的任务函数代码零改动。

## 适用场景

- 新项目选择合适的 broker
- 从一个 broker 迁移到另一个
- 对比不同 broker 的可靠性/性能
- 配置 broker 连接参数

## 决策流程图

```
需要消息持久化/可靠性？
├── 不需要 → MEMORY_QUEUE（最快，重启丢失）
├── 需要，单机部署？
│   ├── 简单场景 → SQLITE_QUEUE（默认，零配置）
│   └── 需要性能 → REDIS_ACK_ABLE
└── 需要，分布式部署？
    ├── 已有 Redis → REDIS_ACK_ABLE 或 REDIS_STREAM
    ├── 需要复杂路由 → RABBITMQ_AMQPSTORM
    ├── 高吞吐流处理 → KAFKA_CONFLUENT（推荐，至少消费一次）
    ├── IoT/轻量级 → MQTT（须先启动消费端）或 NATS_CORE
    └── 云托管 → SQS
```

## 速查表 — 最常用的 Broker

| 场景 | broker_kind | 原因 |
|------|-------------|------|
| **⭐ 本地并发/超级装饰器** | **`MEMORY_QUEUE`** | **SSS 级推荐！零序列化、零中间件、支持不可 pickle 的对象、自带 QPS 控频/并发/重试/超时，完美替代 ThreadPoolExecutor** |
| 开发/测试 | `SQLITE_QUEUE` | 零配置，自带持久化 |
| 生产环境（大多数场景） | `REDIS_ACK_ABLE` | ACK 确认，快速可靠 |
| 消费者组、消息回溯 | `REDIS_STREAM` | 类似 Kafka 但更简单 |
| 复杂路由/Exchange | `RABBITMQ_AMQPSTORM` | 完整 AMQP 特性 |
| 海量吞吐 | `KAFKA_CONFLUENT` | 至少消费一次，适合反复重启部署 |
| 优先级队列 | `REDIS_ZSET_PRIORITY` | 基于有序集合 |
| 延迟消息 | `REDIS_ZSET_DELAY` | 基于时间的投递 |
| IoT/嵌入式 | `MQTT` | 轻量级 pub/sub（须先启动消费端，不存消息） |
| AWS 云服务 | `SQS` | 托管，Serverless |
| 文件变更触发 | `WATCHDOG` | 文件系统监控 |
| MySQL Binlog 事件 | `MYSQL_CDC` | 数据库事件驱动 |

> **为什么 MEMORY_QUEUE 是 SSS 级推荐？**
>
> 很多场景其实不需要分布式 MQ。当你只需要「控频 + 并发 + 重试 + 超时」但不需要跨进程/跨机器时，`MEMORY_QUEUE` 是最佳选择：
> - **零安装**：不需要 Redis/RabbitMQ/Kafka 等任何中间件
> - **零序列化开销**：函数入参可以是任何 Python 对象（socket连接、数据库连接、GUI对象）
> - **极致性能**：无网络IO，性能显著高于分布式 broker
> - **完整能力**：QPS 控频、并发数控制、函数超时、重试、`get_future()` 获取结果
> - **无缝切换**：后续需要分布式时，只需把 `broker_kind` 改成 `REDIS_ACK_ABLE`，代码零改动
>
> 详见 skill：`funboost-memory-queue-pool`

## 所有 Broker 枚举

### Redis 家族
- `REDIS` — 简单 list，可能丢消息
- `REDIS_ACK_ABLE` — **推荐**，消费确认
- `REDIS_ACK_USING_TIMEOUT` — 超时型 ACK
- `REDIS_STREAM` — Stream + 消费者组
- `REDIS_PRIORITY` — 优先级队列
- `REDIS_BRPOP_LPUSH` — 原子移动
- `REDIS_PUBSUB` — 发布订阅（无持久化）
- `REDIS_ZSET_PRIORITY` — 有序集合优先级
- `REDIS_ZSET_DELAY` — 有序集合延迟投递

### RabbitMQ 家族
- `RABBITMQ_AMQPSTORM`（= `RABBITMQ`）— **推荐**，amqpstorm 库
- `RABBITMQ_COMPLEX_ROUTING` — Direct/Fanout/Topic/Headers 交换机
- `RABBITMQ_AMQP` — amqp 库
- `RABBITMQ_PIKA` — pika 库
- `RABBITMQ_RABBITPY` — rabbitpy 库

### Kafka 家族
- `KAFKA` — kafka-python 库（最多消费一次，重启可能丢消息）
- `KAFKA_CONFLUENT`（= `CONFLUENT_KAFKA`）— confluent-kafka 库（**推荐**，至少消费一次）
- `KAFKA_CONFLUENT_SASlPlAIN` — SASL 认证（连接参数在 `BrokerConnConfig.KFFKA_SASL_CONFIG`）

### 其他
- `ROCKETMQ` — Apache RocketMQ 4.x（仅 Linux/macOS）
- `ROCKETMQ5` — RocketMQ 5.x（纯 Python gRPC 客户端，支持 Windows/Linux/macOS）
- `PULSAR` — Apache Pulsar
- `NSQ` — NSQ 分布式消息系统
- `MQTT` — 轻量级 pub/sub（不存消息，须先启动消费端）
- `NATS_CORE` — NATS 核心（无持久化）
- `NATS_JETSTREAM` — NATS JetStream（持久化、消费者组）
- `ZEROMQ` — ZeroMQ
- `SQS`, `HTTPSQS` — AWS SQS / HTTPSQS
- `TCP`, `UDP`, `HTTP`, `GRPC`, `WEBSOCKET` — 网络协议（须先启动消费端，不支持持久化）
- `CELERY`, `DRAMATIQ`, `HUEY`, `RQ`, `NAMEKO`, `KOMBU` — 框架桥接
- `MONGOMQ`, `SQLACHEMY`, `POSTGRES`, `PEEWEE` — 数据库驱动
- `MEMORY_QUEUE`, `FASTEST_MEM_QUEUE` — 内存队列
- `SQLITE_QUEUE`, `TXT_FILE` — 本地文件
- `MYSQL_CDC` — Binlog 事件驱动
- `WATCHDOG` — 文件系统监控
- `EMPTY` — 空实现

## 使用示例

```python
from funboost import boost, BoosterParams, BrokerEnum

@boost(BoosterParams(
    queue_name="production_task",
    broker_kind=BrokerEnum.REDIS_ACK_ABLE,
))
def my_task(data: dict):
    process(data)
```

## Broker 连接配置

在项目根目录创建 `funboost_config.py`（首次运行 funboost 会自动生成模板）。

**配置加载机制：** funboost 启动时通过 `importlib.import_module('funboost_config')` 从 `sys.path` 中查找配置文件。设置 `PYTHONPATH=项目根目录` 使该目录进入 `sys.path`，框架就能找到并加载 `funboost_config.py`。优先级：脚本所在目录 > PYTHONPATH 目录。找不到时自动在项目根目录生成模板。

```python
# funboost_config.py（项目根目录，首次运行自动生成）
from funboost.utils.simple_data_class import DataClassBase

class BrokerConnConfig(DataClassBase):
    # Redis
    REDIS_HOST = "127.0.0.1"
    REDIS_PORT = 6379
    REDIS_PASSWORD = ""
    REDIS_DB = 7

    # RabbitMQ（按实际账号修改）
    RABBITMQ_HOST = "127.0.0.1"
    RABBITMQ_PORT = 5672
    RABBITMQ_USER = "rabbitmq_user"
    RABBITMQ_PASS = "rabbitmq_pass"
    RABBITMQ_VIRTUAL_HOST = "/"

    # Kafka
    KAFKA_BOOTSTRAP_SERVERS = ["127.0.0.1:9092"]
```

## broker_exclusive_config

Broker 专属配置使用 `broker_exclusive_config` 字典——**严禁臆造键名**：

```python
@boost(BoosterParams(
    queue_name="rabbit_task",
    broker_kind=BrokerEnum.RABBITMQ_AMQPSTORM,
    broker_exclusive_config={
        "queue_durable": True,
        "no_ack": False,
    }
))
def task(x): ...
```

## 常见错误

| 错误 | 修正 |
|------|------|
| 需要可靠性却用 `REDIS` | 应使用 `REDIS_ACK_ABLE` |
| 臆造 `broker_exclusive_config` 的键名 | 查阅源码或文档确认有效键名 |
| 生产环境用 `MEMORY_QUEUE` | 重启会丢失所有消息 |
| 使用 `do_task_filtering` 等功能却没配置 Redis | 这些功能依赖 Redis，需正确配置连接 |

## 相关 Skill

- `funboost-memory-queue-pool` — 内存队列替代线程池
- `using-funboost-basics` — 基础使用入门
