# AI 重大设计更新记录

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

