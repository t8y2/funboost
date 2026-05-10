# AI 重大设计更新记录

## 2026-05-10: 引入 _REQUEUE_IS_NATIVE_NACK 类属性，修复 requeue 后仍 ACK 的问题

### 改动范围
- 修改 `funboost/consumers/base_consumer.py` — AbstractConsumer 新增 `_REQUEUE_IS_NATIVE_NACK = False` 类属性，替换第 913/1079 行的硬编码 broker 类型列表
- 修改 `funboost/consumers/rabbitmq_amqpstorm_consumer.py` — 设 `_REQUEUE_IS_NATIVE_NACK = True`
- 修改 `funboost/consumers/rabbitmq_pika_consumer.py` — 设 `_REQUEUE_IS_NATIVE_NACK = True`
- 修改 `funboost/consumers/rabbitmq_rabbitpy_consumer.py` — 设 `_REQUEUE_IS_NATIVE_NACK = True`
- 修改 `funboost/consumers/rabbitmq_amqp_consumer.py` — 设 `_REQUEUE_IS_NATIVE_NACK = True`（此前未在硬编码列表中，属于已有 bug 修复）
- 修改 `funboost/contrib/register_custom_broker_contrib/nats_jetstream_broker.py` — 设 `_REQUEUE_IS_NATIVE_NACK = True`
- 修改 `funboost/consumers/pulsar_consumer.py` — 设 `_REQUEUE_IS_NATIVE_NACK = True`
- 修改 `funboost/consumers/nsq_consumer.py` — 设 `_REQUEUE_IS_NATIVE_NACK = True`
- 修改 `funboost/consumers/kombu_consumer.py` — 设 `_REQUEUE_IS_NATIVE_NACK = True`
- 修改 `funboost/consumers/rocketmq5_consumer.py` — 设 `_REQUEUE_IS_NATIVE_NACK = True`
- 修改 `funboost/consumers/persist_queue_consumer.py` — 设 `_REQUEUE_IS_NATIVE_NACK = True`
- 修改 `funboost/consumers/mongomq_consumer.py` — 设 `_REQUEUE_IS_NATIVE_NACK = True`
- 修改 `funboost/consumers/postgres_consumer.py` — 设 `_REQUEUE_IS_NATIVE_NACK = True`
- 修改 `funboost/consumers/peewee_conusmer.py` — 设 `_REQUEUE_IS_NATIVE_NACK = True`
- 修改 `funboost/consumers/sqlachemy_consumer.py` — 设 `_REQUEUE_IS_NATIVE_NACK = True`

### 背景
原 `base_consumer.py` 中在消息处理完后决定是否 ACK 时，使用硬编码列表 `[BrokerEnum.RABBITMQ_AMQPSTORM, RABBITMQ_PIKA, RABBITMQ_RABBITPY]` 判断。
只有这三种 RabbitMQ broker 在 `_requeue`（NACK）后会跳过 `_confirm_consume`（ACK）。
其他使用原生 NACK 机制的 broker（如 NATS JetStream、RabbitmqAmqpConsumer、Pulsar、NSQ 等）会先 NACK 再 ACK，导致消息不会重投。

### 设计
- 新增 `AbstractConsumer._REQUEUE_IS_NATIVE_NACK = False` 类属性
- 含义：`_requeue` 是否使用了 broker 原生 NACK/reject 机制，已 requeue 的消息不应再调用 `_confirm_consume`
- 子类覆盖为 `True` 即可，无需再修改 `base_consumer.py` 的判断逻辑
- 共 14 个消费者设为 True：RabbitMQ×4、Pulsar、NSQ、Kombu、RocketMQ5、NATS JetStream、PersistQueue、MongoDB、Postgres、Peewee、SQLAlchemy
- 未设置的消费者（Redis系列、Kafka、SQS、内存队列等）的 `_requeue` 使用重新发布方式，不与 ACK 冲突

---

## 2026-05-10: NATS Core broker 新增 Queue Group（消费者组）可配置支持

### 改动范围
- 修改 `funboost/contrib/register_custom_broker_contrib/nats_core_broker.py`

### 背景
原 NATS Core broker 的消费者使用 `nc.subscribe(subject, cb=handler)` 订阅，没有传 `queue` 参数。
这导致多个消费者实例会收到相同的消息（广播模式），不符合 funboost 作为任务队列"多消费者分摊消息"的默认预期。

### 设计
1. 通过 `register_broker_exclusive_config_default` 注册 NATS Core 专属配置：
   - `nats_url`：可覆盖全局 `BrokerConnConfig.NATS_URL`
   - `queue_group`：消费者组名，默认 `'default'`
2. 默认行为为**负载均衡**（与 Redis、RabbitMQ 等 broker 一致）
3. 用户如需广播模式，设 `broker_exclusive_config={'queue_group': ''}` 即可
4. Publisher 和 Consumer 都支持从 `broker_exclusive_config` 读取 `nats_url`

---

## 2026-05-09: NATS broker 升级为 nats-py 官方客户端 + 新增 NATS JetStream broker

### 改动范围
- 修改 `funboost/consumers/nats_consumer.py` — 使用 `nats-py` (asyncio) 替代废弃的 `pynats`
- 修改 `funboost/publishers/nats_publisher.py` — 同上
- 修改 `funboost/core/lazy_impoter.py` — NatsImporter 改为 import nats
- 新增 `funboost/contrib/register_custom_broker_contrib/nats_jetstream_broker.py` — NATS JetStream 持久化 broker

### 背景
原有 NATS 实现使用的是 2019 年的 `pynats` 包（同步、无 JetStream 支持、已停止维护）。
有用户在 GitHub issue 中反馈该包过旧。

### 设计
1. **NATS Core**（`BrokerEnum.NATS`）：升级为 `nats-py` 官方 asyncio 客户端，保持原有行为（无持久化、无ACK）
2. **NATS JetStream**（`BROKER_KIND_NATS_JETSTREAM`）：新增 contrib broker，支持：
   - 消息持久化（Stream）
   - 消费确认（ACK/NAK）
   - 持久化消费者（durable，重启不丢失消费位置）
   - 消费者组（多实例分摊消息）
   - Pull 模式拉取
   - 可配置 ack_wait、max_deliver

### 依赖
- `pip install nats-py`（替代 `pip install nats-python`/`pynats`）

---

## 2026-05-07: 修复 get_cols() 在 MongoDB 不可用时队列名为空的问题

### 改动范围
- 修改 `funboost/funweb/functions.py` 中的 `get_cols()` 函数

### 问题
当 MongoDB 未安装或不可用时，"函数结果表"和"消费速率图"页面的队列名称下拉框无法选择（为空），
而其他页面（队列操作、消费者管理等）的队列名称可以正常显示。

### 原因
`get_cols()` 第一行就调用 `MongoMixin().mongo_db_task_status`，如果 MongoDB 连接失败则整个函数抛异常。
而队列名本身来自 Redis（`QueuesConusmerParamsGetter`），不需要 MongoDB。

### 修复
将 MongoDB 连接用 try-except 包裹，失败时 `db = None`。遍历队列时如果 `db` 为 None 则跳过 count 查询，
设 `count = -1` 标记为 MongoDB 不可用。队列名列表始终能正常返回。

---

## 2026-05-07: funweb 新增 Dashboard 概览页

### 改动范围
- 新增 `funboost/funweb/flask_bps/dashboard.py` — Dashboard 后端聚合 API 蓝图
- 新增 `funboost/funweb/templates/dashboard.html` — Dashboard 前端模板（卡片 + ECharts 图表 + 列表 + 系统资源）
- 修改 `funboost/funweb/app.py` — 注册 `dashboard_bp` 蓝图
- 修改 `funboost/funweb/templates/index.html` — 侧边栏新增 Dashboard 导航项，设为登录后默认首页

### 功能说明
Dashboard 概览页提供全局统一视图：
1. **统计卡片**：队列总数、活跃消费者数、消息积压总量、当前总吞吐(msg/s)、消费者节点数
2. **图表**：队列积压 Top 10 柱状图、队列吞吐 Top 10 柱状图（使用 ECharts）
3. **排行列表**：积压排行 Top 15、吞吐排行 Top 15
4. **系统资源概览**：CPU/内存/磁盘使用率进度条（复用 system_monitor 的 Redis 时序数据）
5. **自动刷新**：每 10 秒自动刷新数据

### API
- `GET /api/dashboard/summary` — 需要登录，返回 `{succ: true, data: {...}}` 结构

### 数据来源
- 使用 `QueuesConusmerParamsGetter().get_queues_params_and_active_consumers()` 获取队列+消费者信息
- 使用 Redis `monitor:*` sorted set 获取系统资源数据

