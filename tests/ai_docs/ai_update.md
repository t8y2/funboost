# AI 重大设计更新记录

## 2026-05-09: NATS broker 全面重构 — 升级 nats-py + 移入 contrib + 枚举重命名

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

