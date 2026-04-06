# funboost 教程速查 for AI

> 本文档提取自 funboost 完整教程，精确到章节编号和三级标题
> 
> 用途：帮助 AI 快速定位教程内容，理解功能用法
> 
> 源文档位置：`D:\codes\funboost_docs\source\articles\`

---

## 教程文件清单

| 章节 | 文件名 | 主题 |
|------|--------|------|
| c0 | c0.md | 快速预览（视频/音频） |
| c1 | c1.md | 框架简介与安装 |
| c2 | c2.md | 与 Celery 对比 |
| c3 | c3.md | 中间件选择指南 |
| c4 | c4.md | 基础代码示例（最重要） |
| c4b | c4b.md | 高级进阶示例 |
| c5 | c5.md | （预留） |
| c6 | c6.md | 常见问题回答 |
| c7 | c7.md | 更新记录 |
| c8 | c8.md | 爬虫应用 |
| c9 | c9.md | 性能测试 |
| c10 | c10.md | 框架原理剖析 |
| c11 | c11.md | 辅助功能 |
| c12 | c12.md | 贡献指南 |
| c13 | c13.md | 架构设计 |
| c14 | c14.md | AI 学习指南（必读） |
| c15 | c15.md | 命令行工具 |
| c16 | c16.md | 工作流编排 |
| c20 | c20.md | 版本迁移指南 |
| - | funboost_vs_celery.md | 详细对比 |

---

## c0 - 快速预览

### c0.0 多媒体资源
- 视频演示、音频介绍
- 运行流程图、功能思维导图

---

## c1 - 框架简介

### c1.0 框架说明
- **核心价值**：把复杂留给框架，把简单留给用户
- **安装**：`pip install funboost` 或 `pip install funboost[all]`

### c1.1 框架架构
- 生产者 → Broker → 消费者 模型
- 可选 RPC 模式（消费者 → 生产者）

### c1.2 功能特性
- 40+ 种消息队列支持
- 30+ 种任务控制功能
- Python 所有并发模式
- FaaS、CDC、爬虫、工作流等

### c1.3 使用例子
- 最简示例、生产级示例

---

## c2 - 与 Celery 对比

### c2.0 核心差异
- Celery 对目录结构要求严格
- funboost 零约束，任意文件夹可用

### c2.1 目录结构对比
- Celery 需要固定项目结构
- funboost 无要求

### c2.2 性能对比
- 发布性能：funboost 是 Celery 的 22 倍
- 消费性能：funboost 是 Celery 的 46 倍
- 控制变量法跑分

### c2.3 IDE 补全对比
- Celery 重要方法无法补全
- funboost 全面支持代码补全

### c2.4 配置方式对比
- Celery 配置复杂（100+ 配置项）
- funboost 自动生成 funboost_config.py

### c2.5 启动方式对比
- Celery 命令行启动复杂
- funboost `fun.consume()` 一行启动

### c2.6 性能跑分代码
- 严格的控制变量法对比

---

## c3 - 中间件选择指南

### c3.1 BrokerEnum 详解

#### c3.1.1 传统 MQ
- `RABBITMQ_AMQPSTORM` - 强烈推荐
- `RABBITMQ_COMPLEX_ROUTING` - 复杂路由
- `KAFKA` / `KAFKA_CONFLUENT` - Kafka
- `ROCKETMQ` / `ROCKETMQ5` - RocketMQ
- `PULSAR` - Apache Pulsar
- `NSQ` - NSQ
- `MQTT` - MQTT
- `NATS` - NATS

#### c3.1.2 Redis 系列
- `REDIS` - List 结构（高性能，不保证）
- `REDIS_ACK_ABLE` - List + ZSet ACK（推荐）
- `REDIS_STREAM` - Stream 结构
- `REDIS_PRIORITY` - 优先级队列
- `REDIS_BRPOP_LPUSH` - 双队列
- `REDIS_PUBSUB` - 发布订阅

#### c3.1.3 内存/文件
- `MEMORY_QUEUE` - Python queue.Queue（超一等公民）
- `FASTEST_MEM_QUEUE` - collections.deque（更快）
- `SQLITE_QUEUE` - SQLite 持久化
- `TXT_FILE` - 文本文件

#### c3.1.4 数据库
- `MONGOMQ` - MongoDB
- `SQLACHEMY` - SQLAlchemy（MySQL/Oracle/PostgreSQL/SQLite）
- `POSTGRES` - PostgreSQL 原生
- `PEEWEE` - Peewee ORM

#### c3.1.5 Socket/协议
- `TCP` / `UDP` / `HTTP` / `GRPC` / `WEBSOCKET`
- `ZEROMQ` - ZeroMQ

#### c3.1.6 其他框架
- `CELERY` - Celery 作为 broker
- `DRAMATIQ` - Dramatiq 作为 broker
- `HUEY` - Huey 作为 broker
- `RQ` - RQ 作为 broker
- `NAMEKO` - Nameko 微服务
- `KOMBU` - Kombu

#### c3.1.7 特殊
- `MYSQL_CDC` - MySQL binlog CDC
- `WATCHDOG` - 文件系统监控
- `SQS` - AWS SQS
- `EMPTY` - 空实现（自定义扩展）

### c3.2 选择建议
- 高可靠：RabbitMQ、Redis ACK
- 高吞吐：Kafka、Pulsar
- 简单场景：SQLite、MEMORY_QUEUE
- 无中间件：TCP/UDP/HTTP

---

## c4 - 基础代码示例（最重要章节）

### c4.0 装饰器入参格式

#### c4.0.1 老方式（兼容但不推荐）
```python
@boost('queue_test_f01', qps=0.2, broker_kind=BrokerEnum.REDIS_ACK_ABLE)
```

#### c4.0.2 新方式（强烈推荐）
```python
@boost(BoosterParams(queue_name='queue_test_f01', qps=0.2, broker_kind=BrokerEnum.REDIS_ACK_ABLE))
```

#### c4.0.3 PyCharm 代码补全
- 安装 pydantic 插件

#### c4.0.4 自定义 BoosterParams 子类
```python
class BoosterParamsMy(BoosterParams):
    broker_kind: str = BrokerEnum.RABBITMQ
    max_retry_times: int = 4
    log_level: int = logging.DEBUG
    log_filename: str = '自定义.log'
```

### c4.1 装饰器方式调度函数
- 基础示例：qps 控频、发布/消费

### c4.2 发布任务方式
- `publish` / `pub` / `apply_async` - 传字典
- `push` / `delay` - 传函数参数
- `aio_publish` / `aio_push` - 异步发布

### c4.3 消费任务方式
- `consume()` - 启动消费（非阻塞）
- `multi_process_consume(n)` - 多进程消费

### c4.4 定时任务
- `ApsJobAdder` 使用
- date / interval / cron 三种触发器

### c4.5 RPC 模式
- `is_using_rpc_mode=True`
- `AsyncResult.result` 获取结果

### c4.6 任务过滤去重
- `do_task_filtering=True`
- `task_filtering_expire_seconds`

### c4.7 死信队列
- `is_push_to_dlx_queue_when_retry_max_times=True`

### c4.8 消费确认 ACK
- Redis ACK 机制说明

### c4.9 并发模式选择
- threading / gevent / eventlet / async / single_thread

### c4.10 分布式控频
- `is_using_distributed_frequency_control=True`

### c4.11 任务状态持久化
- `FunctionResultStatusPersistanceConfig`
- MongoDB 保存状态和结果

### c4.12 超时控制
- `function_timeout`
- 谨慎使用，可能影响性能

### c4.13 远程杀死任务
- `is_support_remote_kill_task=True`

### c4.14 高级重试
- `is_using_advanced_retry=True`
- 指数退避配置

### c4.15 消息过期
- `msg_expire_seconds`

### c4.16 优先级队列
- `REDIS_PRIORITY`
- `priority` 参数

### c4.17 批量发布
- `multi_process_pub_params_list`

### c4.18 暂停/恢复消费
- `pause_consume()` / `continue_consume()`

### c4.19 清空队列
- `clear()` / `clear_queue()`

### c4.20 获取消息数量
- `get_message_count()`

### c4.21 自定义 broker
- `register_custom_broker()`
- 继承 `AbstractConsumer` + `AbstractPublisher`

### c4.22 远程部署
- `fabric_deploy()`
- 自动上传代码并启动消费

### c4.23 消费分组
- `booster_group` 参数
- `BoosterRegistry.consume_group()`

### c4.24 函数装饰器
- `consuming_function_decorator` 参数
- 避免直接在函数上叠加装饰器

### c4.25 指定线程池
- `specify_concurrent_pool`
- 多个消费者共享线程池

### c4.26 指定事件循环
- `specify_async_loop`
- aiohttp 等兼容

### c4.27 中间件专属配置
- `broker_exclusive_config`
- 各中间件特有参数

### c4.28 用户自定义配置
- `user_options` 参数
- 自由扩展

### c4.29 优先级队列详解
- Redis 优先级实现
- RabbitMQ 优先级实现

### c4.30 微批消费
- `pull_msg_batch_size` 批量拉取

---

## c4b - 高级进阶示例

### c4b.1 日志模板中显示 task_id
- `TaskIdLogger` 使用
- 日志模板配置
- `fct.logger` 使用

### c4b.2 获取当前任务信息
- `fct.task_id`
- `fct.run_times`
- `fct.full_msg`
- `fct.function_result_status`

### c4b.3 任务状态查询
- `FunctionResultStatus` 字段
- MongoDB 查询

### c4b.4 消费速度统计
- 实时消费速率显示

### c4b.5 多进程发布
- 快速发布大量任务

### c4b.6 用户自定义配置使用
- `user_options` 配合 `consumer_override_cls`

### c4b.7 消费者类继承重写
- 自定义消费者行为

### c4b.8 发布者类继承重写
- 自定义发布者行为

### c4b.9 批量确认消费
- 微批消费模式

### c4b.10 微批消费详解
- `MicroBatchConsumerMixin`
- `MicroBatchBoosterParams`
- 聚合多条消息处理

### c4b.11 周期额度控制
- `periodic_quota_mixin`
- 周期次数限制

### c4b.12 熔断器
- `circuit_breaker_mixin`
- 失败率熔断

### c4b.13 Prometheus 监控
- `funboost_promethus_mixin`
- 指标暴露

### c4b.14 OpenTelemetry 链路追踪
- `funboost_otel_mixin`
- Jaeger/SkyWalking 集成

### c4b.15 告警通知
- `alert_notifier_mixin`
- 异常告警

### c4b.16 队列转发
- `queue2queue.py`
- 消息路由转发

### c4b.17 Django 数据库兼容
- `django_db_deco.py`

### c4b.18 CDC MySQL 数据同步
- `mysql2mysql.py`
- 轻量级 Canal 替代

---

## c6 - 常见问题回答

### c6.0 框架值得学习吗？
- 绝对值得
- 自由编程 vs 框架奴役
- 功能全面、性能卓越

### c6.1 目录结构要求
- 零约束，任意文件夹

### c6.2 消费者不执行
- 检查队列名一致性
- 检查消费者是否启动

### c6.3 任务丢失
- 使用 ACK 模式
- Redis ACK 机制说明

### c6.4 性能优化
- 批量拉取
- 多进程叠加
- 选择合适的中间件

### c6.5 调试技巧
- 日志级别设置
- task_id 追踪

### c6.6 与 Celery 共存
- 可以共存，互不影响

### c6.7 Windows 支持
- 完全支持
- 多进程注意事项

### c6.8 多机器部署
- Redis 共享配置
- 分布式控频

### c6.9 定时任务不执行
- 检查 apscheduler 配置
- jobstores 选择

### c6.10 RPC 超时
- 检查消费端是否运行
- 调整超时时间

### c6.11 消息序列化
- JSON 默认
- pickle 支持（MEMORY_QUEUE）
- 自定义序列化

### c6.12 是否抄袭 Celery
- 核心本质不同
- iPhone vs 诺基亚

---

## c7 - 更新记录

### v7.1 Redis ACK 消费者
- `RedisConsumerAckAble`
- 心跳检测，孤儿消息重回队列

### v7.2 Redis 管理页面
- 消费速度显示

### v7.3 乞丐版实现
- 10 行代码演示原理

### v7.4 SQLAlchemy 支持
- 5 种数据库作为 broker

### v7.5 nb_log 集成
- 独立日志包

### v7.6 Kafka Confluent
- 性能提升 10 倍

### v7.7 优先级队列
- Redis 优先级实现

### v7.8 死信队列
- 失败消息单独处理

### v7.9 分布式控频
- 多机总 QPS 控制

### v7.10 FaaS 功能
- FastAPI/Flask/Django 集成

### v7.11 工作流编排
- Chain/Group/Chord

### v7.12 OpenTelemetry
- 全链路追踪

### v7.13 更多中间件
- Pulsar、NATS、MQTT 等

---

## c8 - 爬虫应用

### c8.0 前置说明
- funboost vs Scrapy 对比
- 自由编程 vs 框架奴役
- FaaS 架构优势

### c8.1 boost_spider 介绍
- `pip install boost_spider`
- `RequestClient` - 请求客户端
- `SpiderResponse` - 响应封装
- `DatasetSink` - 数据入库

### c8.2 RequestClient 用法
- `get()` / `post()` / `request()`
- 代理配置：`proxy_name_list`
- UA 切换：`is_change_ua_every_request`
- 重试配置：`request_retry_times`
- 超时配置：`timeout`

### c8.3 两层级爬虫示例
- 列表页 → 详情页
- 分层控频

### c8.4 多层爬虫示例
- 无限层级扩展

### c8.5 与 Scrapy 对比
- 代码量对比
- 自由度对比
- 性能对比

### c8.6 boost_scrapy（兼容层）
- Scrapy API 兼容
- 双模式运行

### c8.7 JS 渲染支持
- Playwright 集成
- DrissionPage 集成

### c8.8 数据入库
- `DatasetSink` 使用
- SQLite/MySQL/MongoDB

### c8.9 增量爬虫
- 任务过滤去重
- 断点续爬

### c8.10 分布式爬虫
- 多机部署
- Redis 共享任务

### c8.11 实时爬虫
- FaaS HTTP 接口
- 动态添加任务

### c8.12 爬虫监控
- Web 管理界面
- 消费速度统计

### c8.13 代理池集成
- `nb_proxypool` 使用

### c8.14 Scrapy 迁移指南
- 从 Scrapy 迁移到 boost_spider

---

## c9 - 性能测试

### c9.1 测试环境
- 硬件配置
- 中间件配置

### c9.2 测试方法
- 控制变量法
- 发布测试
- 消费测试

### c9.3 测试结果
- 与 Celery 对比
- 与 RQ 对比
- 与 Dramatiq 对比

### c9.4 优化建议
- 批量拉取
- 多进程叠加
- 中间件选择

---

## c10 - 框架原理剖析

### c10.1 架构设计
- 生产者-消费者模式
- 装饰器实现原理

### c10.2 Booster 类详解
- `__call__` 魔术方法
- 方法动态绑定

### c10.3 消费者调度
- `_submit_task` 核心
- 并发池管理

### c10.4 消息确认机制
- ACK 实现原理
- 心跳检测

### c10.5 QPS 控频实现
- 令牌桶算法
- 分布式统计

### c10.6 RPC 实现
- Redis 结果存储
- 异步等待

### c10.7 定时任务实现
- APScheduler 集成
- 任务序列化

---

## c11 - 辅助功能

### c11.1 配置管理
- `funboost_config.py`
- 环境变量支持

### c11.2 日志系统
- nb_log 集成
- 彩色日志
- 文件日志

### c11.3 Redis 工具
- `RedisMixin`
- 连接池管理

### c11.4 异常处理
- `ExceptionForRetry`
- `ExceptionForRequeue`
- `ExceptionForPushToDlxqueue`

### c11.5 信号处理
- `ctrl_c_recv()`
- 优雅退出

---

## c12 - 贡献指南

### c12.1 开发环境搭建
- 源码安装
- 测试运行

### c12.2 代码规范
- PEP8
- 类型提示

### c12.3 提交 PR
- 分支管理
- 测试覆盖

---

## c13 - 架构设计

### c13.1 设计哲学
- 函数至上
- 自由编程

### c13.2 扩展机制
- 自定义 broker
- Mixin 扩展

### c13.3 性能设计
- 无锁队列
- 批量处理

---

## c14 - AI 学习指南（必读）

### c14.1 如何使用 AI 学习 funboost
- 上传 `funboost_all_docs_and_codes.md`
- Google AI Studio
- 腾讯 IMA 知识库

### c14.2 AI 编程提示词
- 角色设定
- 任务描述
- 输出要求

### c14.3 常见 AI 误解
- 认为必须有 BaseSpider
- 认为必须有 middleware
- 不理解 RequestClient 价值

### c14.4 AI 生成代码检查清单
- 使用 `BoosterParams` 传参
- 使用 `push` 发布
- 使用 `fct` 获取上下文
- 避免装饰器叠加

---

## c15 - 命令行工具

### c15.1 funboost CLI
- `funboost --help`
- 子命令列表

### c15.2 启动消费
- `funboost consume <queue_name>`

### c15.3 查看队列
- `funboost list`

### c15.4 清空队列
- `funboost clear <queue_name>`

---

## c16 - 工作流编排

### c16.1 Workflow 介绍
- Chain - 链式执行
- Group - 并行执行
- Chord - 分组聚合

### c16.2 Chain 用法
- 任务链式调用
- 结果传递

### c16.3 Group 用法
- 任务并行执行
- 结果汇总

### c16.4 Chord 用法
- 先并行后聚合
- MapReduce 模式

### c16.5 与 Celery Canvas 对比
- API 对比
- 功能对比

---

## c20 - 版本迁移指南

### c20.1 v40.0 重大变更
- `BoosterParams` 成为主要传参方式
- `BoostersManager` → `BoosterRegistry`
- 旧方式仍兼容但会警告

### c20.2 迁移步骤
1. 替换装饰器入参
2. 更新管理器引用
3. 测试验证

### c20.3 兼容性说明
- 老代码仍然可用
- 建议逐步迁移

---

## funboost_vs_celery - 详细对比

### 1. 目录结构
- Celery 严格 vs funboost 自由

### 2. 性能对比
- 发布性能 22 倍差距
- 消费性能 46 倍差距
- 跑分代码

### 3. IDE 体验
- 代码补全对比
- 配置提示对比

### 4. 功能对比表
| 功能 | Celery | funboost |
|------|--------|----------|
| 目录约束 | 严格 | 无 |
| 并发模式 | 3 种 | 5 种+叠加 |
| 中间件 | 几种 | 50 种 |
| QPS 控频 | 粗糙 | 精确 |
| RPC | 支持 | 支持 |
| FaaS | 无 | 内置 |
| 定时任务 | 复杂 | 简单 |
| 监控 | Flower | 内置 Web |

### 5. 代码量对比
- 同样功能代码行数对比

### 6. 学习曲线
- Celery 陡峭 vs funboost 平缓

---

## 快速检索索引

### 按功能检索

| 功能 | 章节 |
|------|------|
| 基础用法 | c4.0 - c4.5 |
| 定时任务 | c4.4 |
| RPC 模式 | c4.5 |
| 任务过滤 | c4.6 |
| 死信队列 | c4.7 |
| 并发模式 | c4.9 |
| 分布式控频 | c4.10 |
| 状态持久化 | c4.11 |
| 高级重试 | c4.14 |
| 自定义 broker | c4.21 |
| 远程部署 | c4.22 |
| 微批消费 | c4b.10 |
| 熔断器 | c4b.12 |
| Prometheus | c4b.13 |
| OpenTelemetry | c4b.14 |
| 爬虫 | c8 |
| 工作流 | c16 |
| AI 指南 | c14 |

### 按问题检索

| 问题 | 章节 |
|------|------|
| 怎么安装 | c1.0 |
| 怎么选择中间件 | c3 |
| 怎么发布任务 | c4.2 |
| 怎么启动消费 | c4.3 |
| 怎么定时执行 | c4.4 |
| 怎么获取结果 | c4.5 |
| 怎么防止重复 | c4.6 |
| 怎么处理失败 | c4.7, c4.14 |
| 怎么控制并发 | c4.9 |
| 怎么控制 QPS | c4.1 |
| 怎么多机部署 | c4.10, c6.8 |
| 怎么写爬虫 | c8 |
| 怎么自定义 broker | c4.21 |
| 怎么迁移 Celery | c2, funboost_vs_celery |
| AI 怎么生成代码 | c14 |

---

*本文档由 AI 从 funboost 教程中提取生成，精确到章节编号，方便快速定位。*
