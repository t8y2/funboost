# AI 重大设计更新记录

<<<<<<< HEAD
## 2026-05-09: NATS broker 全面重构 — 升级 nats-py + 移入 contrib + 枚举重命名
=======
## 2026-05-10: 修复 active_cousumer_info_getter.py 三个 bug

### Bug 1: hmget_many_by_all_queue_names 键值对错位
- **文件**：`funboost/core/active_cousumer_info_getter.py`
- **问题**：`hmget` 返回列表先过滤 None 再 zip，导致有 None 值时键值对错位（如 q2 拿到 q3 的值）
- **修复**：改为先 zip 再过滤 None：`{k: v for k, v in zip(keys, values) if v is not None}`

### Bug 2: get_all_queue_names 缓存 key 冲突
- 见下方详细条目

---

## 2026-05-10: 修复 get_all_queue_names 缓存 key 冲突 bug + 告警队列范围不一致

### Bug: get_all_queue_names 按 project_name 缓存时使用单一变量，切换项目会返回旧项目数据
- **文件**：`funboost/core/active_cousumer_info_getter.py`
- **问题**：`_cache_all_queue_names` 不区分 `care_project_name`。用户切换项目后 30 秒内，仍返回旧项目的队列列表
- **修复**：当 `care_project_name` 有值时，直接走 `self.project_name_queues`（内部已通过 `get_queue_names_by_project_name` 使用按 project_name 字典缓存），去掉有 bug 的单一变量缓存

### Bug: 告警检查和前端下拉使用不同的队列数据源
- **文件**：`funboost/funweb/flask_bps/queue_alerts.py`
- **问题**：`_check_rules_once` 用 `get_all_queue_names()` 获取所有注册过的队列名（含其他项目和废弃队列），而前端下拉用 `get_queues_params_and_active_consumers().keys()` 只返回有消费者配置的队列
- **修复**：统一改为 `getter.get_queues_params().keys()`

---

## 2026-05-10: 修复告警系统两个逻辑 bug

### Bug 1: evaluate_fail_spike 失败率被系统性低估
- **问题**：`all_consumers_last_x_s_execute_count` 是总执行次数（含成功+失败），但代码将其命名为 `total_succ` 并 `total = total_succ + total_fail` 重复计算了失败次数
- **影响**：失败率被低估，例如实际 20% 会被算成 16.7%，可能漏报
- **修复**：`total = total_exec`（直接用总执行次数作为分母），变量名改为 `total_exec`

### Bug 2: evaluate_consumer_lost 超时检测永远不可达
- **问题**：采集线程在 `active_consumer_count == 0` 时不存数据（`continue`），所以时序数据中的条目永远是 `active_consumer_count > 0`。当消费者停止后，旧数据仍在 Redis 中（保留 24h），导致 `all_lost` 始终为 False，超时检测分支永远不可达
- **影响**：消费者停止 1 小时也不会触发 consumer_lost 告警
- **修复**：先检查 `report_ts` 数据是否过期（>60s），再检查 `active_consumer_count`；移除了对 `_redis` 的直接依赖

---

## 2026-05-10: 告警系统重构 — 提取 AlertRuleStore / AlertLogStore / TimeSeriesEvaluator 三大类

### 改动范围
- 修改 `funboost/funweb/flask_bps/queue_alerts.py` — 将零散函数组织为三个职责清晰的类

### 背景
原 queue_alerts.py 中 rule 的 CRUD（`_gen_rule_id`、`_load_rules`、`_save_rule`、`_delete_rule`）和
日志管理（`_append_alert_log`）散落为模块级函数，Flask 路由中存在重复的 hget+json.loads 代码。

### 设计
1. **AlertRuleStore** — 规则 CRUD 管理器
   - `gen_id()` / `load_all()` / `get(rule_id)` / `save(rule_id, rule_dict)` / `delete(rule_id)`
   - `get()` 封装了之前路由中重复的 hget+decode+json.loads 逻辑
   - 支持注入 `redis_client`，便于测试
2. **AlertLogStore** — 告警日志管理器
   - `append(entry)` / `query(start_ts, end_ts, limit=200)`
   - `query()` 封装了之前 `get_alert_log` 路由中散写的 zrevrangebyscore + 反序列化逻辑
3. **TimeSeriesEvaluator** — 已有，实例化时自动取数据（上一轮改造）
4. **`_send_notification`** — 保持独立函数不变（纯通知工具，不属于 rule/log 管理）
5. Flask 路由变为薄层，只做 HTTP 参数解析 + 调用类方法 + 返回 JSON

### 优势
- 整个模块 3 个类 + 薄路由 + 1 个通知工具函数，职责清晰
- 消除 `update_rule`、`toggle_rule` 路由中重复的 Redis 操作代码
- 所有类都支持注入 `redis_client`，可独立 mock 测试

---

## 2026-05-10: 告警系统改造 — 复用时序数据 + 多点聚合判断

### 改动范围
- 修改 `funboost/core/active_cousumer_info_getter.py` — 时序数据采集增加 `active_consumer_count` 字段
- 重写 `funboost/funweb/flask_bps/queue_alerts.py` — 告警检查从时序数据读取，改为多点聚合判断
- 修改 `funboost/funweb/templates/queue_alerts.html` — 前端新增 `check_window_count` 配置项

### 背景
原告警系统每 10 秒独立调用 `get_queues_params_and_active_consumers()` 做一次完整 Redis 聚合查询，
与已有的时序数据采集线程做完全重复的工作。且只基于单一 10 秒快照判断，瞬时抖动容易误报。

### 设计
1. **复用时序数据**：告警线程不再独立查询，而是读取 `funboost_queue_time_series_data:{queue_name}` 中已采集的时序数据
2. **多点聚合判断**：读取最近 N 个周期（可配 `check_window_count`，默认 3 = 30 秒），按告警类型做不同聚合策略：
   - `backlog`（积压）：全部超阈值才触发
   - `qps_drop`（QPS 骤降）：平均 QPS <= 阈值
   - `consumer_lost`（消费者掉线）：全部无消费者 或 时序数据停止更新超 60 秒
   - `fail_spike`（失败率飙升）：汇总 N 个周期的总成功/失败数计算失败率
   - `avg_time_high`（耗时过高）：N 个周期平均耗时 >= 阈值
3. **时序数据增加 `active_consumer_count`**：采集时记录消费者数量（整数），供 `consumer_lost` 判断
4. **前端新增"检查窗口"**：用户可配置连续几个周期异常才触发告警，带实时秒数提示
5. **兼容处理**：`consumer_lost` 类型因消费者全停后采集也停，特殊处理为"时序数据超时 60 秒即视为掉线"

### 优势
- 减少 Redis 查询负载（从完整聚合查询降为 O(1) 的 zrevrange）
- 告警和监控面板使用同源数据，保证一致性
- 多点聚合消除瞬时抖动误报

---

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
>>>>>>> b4aa98c3bd9eefce467172abf4ccdcaf26fd1cea

### 改动范围
- 删除 `funboost/consumers/nats_consumer.py` 和 `funboost/publishers/nats_publisher.py`
- 删除 `funboost/core/lazy_impoter.py` 中的 `NatsImporter` 类
- 新增 `funboost/contrib/register_custom_broker_contrib/nats_core_broker.py` — NATS Core broker (合并 consumer+publisher)
- 新增 `funboost/contrib/register_custom_broker_contrib/nats_jetstream_broker.py` — NATS JetStream 持久化 broker
- 修改 `funboost/constant.py` — `BrokerEnum.NATS` 重命名为 `BrokerEnum.NATS_CORE`，新增 `BrokerEnum.NATS_JETSTREAM`
- 修改 `funboost/factories/broker_kind__publsiher_consumer_type_map.py` — NATS 从模块级导入改为 `regist_to_funboost` 惰性导入

### 背景
原有 NATS 实现使用 2019 年的 `pynats` 包（同步、无 JetStream 支持、已停止维护）。
GitHub issue 反馈该包过旧。同时为了和 WATCHDOG/WEBSOCKET 等 contrib broker 保持一致架构。

### 设计
1. **BrokerEnum.NATS_CORE**：使用 `nats-py` 官方 asyncio 客户端，无持久化、无ACK
2. **BrokerEnum.NATS_JETSTREAM**：支持消息持久化(Stream)、ACK/NAK、durable consumer、消费者组、Pull模式、ConsumerConfig(ack_wait/max_deliver)
3. **导入方式**：两者都通过 `regist_to_funboost` 惰性导入 contrib 模块，不使用 NATS 的用户不会触发 `import nats`
4. **`import nats` 位置**：放在 broker 模块级（而非方法内），因为只有使用该 broker 时才会导入该模块

### 修复的 bug
- JetStream Publisher 的 `find_stream_name_by_subject` 参数用了 `self.queue_name` 而非 `self._subject`
- JetStream Consumer 的 `_confirm_consume`/`_requeue` 在新 event loop 中执行 `msg.ack()`，而 msg 绑定在 dispatch loop 上 → 改为 `run_coroutine_threadsafe` 调度到正确的 loop
- JetStream Consumer 的 `self.booster_params` 应为 `self.consumer_params`

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

