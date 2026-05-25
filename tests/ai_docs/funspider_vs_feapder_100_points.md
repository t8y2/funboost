# funboost 生态 vs feapder 生态 — 100 维终极对比

> **对比双方**
>
> | 阵营 | 组成 |
> |------|------|
> | **funboost 生态** | funboost（调度引擎）+ funweb（管理面板）+ funspider（爬虫辅助）+ nb_log（日志）+ nb_cache（缓存/布隆/限流/熔断）+ PyPI 50 万三方包自由导入 |
> | **feapder 生态** | feapder（爬虫框架）+ feaplat（Docker 管理平台）+ feapder_pipelines（扩展管道） |
>
> 每条标注 **F 胜**（funboost 生态胜）、**P 胜**（feapder 生态胜）或 **平**（持平/各有千秋）。基于 `tests/ai_codes/crawl3/` 同一任务的实际代码 + 官方文档 + GitHub Issues 综合评定。

---

## 一、设计理念（1-5）

| # | 维度 | funboost 生态 | feapder 生态 | 胜负 |
|---|------|--------------|-------------|------|
| 1 | 核心哲学 | **反框架**：函数装饰器赋能，零代码侵入 | **框架**：类继承 + 生命周期回调 | F 胜 |
| 2 | 代码侵入性 | 零。`func(x,y)` 脱离 funboost 也能独立运行 | 强绑定，必须继承 Spider 类才能运行 | F 胜 |
| 3 | 适用领域 | **通用分布式调度引擎**：爬虫、数据处理、微服务、CDC、定时任务均可 | **专用爬虫框架**：仅用于 Web 数据采集 | F 胜 |
| 4 | Pythonic 程度 | 极高——装饰器 + 函数平铺，是最自然的 Python 写法 | 类继承 + callback + yield Request 体系，更接近 Scrapy 风格 | F 胜 |
| 5 | 框架 vs 库 | 库：赋能你的代码，不改变你的代码结构 | 框架：必须在框架的规则里写代码 | F 胜 |

## 二、代码体验（6-14）

| # | 维度 | funboost 生态 | feapder 生态 | 胜负 |
|---|------|--------------|-------------|------|
| 6 | 代码结构 | N 个独立函数 = N 层爬虫，平铺一目了然 | 1 个类 + N 个 parse 回调串联，需跟踪 callback 链 | F 胜 |
| 7 | 代码量（crawl3 同任务） | **124 行**（funspider_crawler.py） | **142 行**（feapder_crawler.py） | F 胜 |
| 8 | IDE 补全 | `BoosterParams` Pydantic 字段补全 + `SpiderItem` SQLModel 属性补全 | `Item` 字典访问 `item['title']`，无属性补全 | F 胜 |
| 9 | 类型安全 | Pydantic 模型校验 + SQLModel 强类型字段 | 无类型约束 | F 胜 |
| 10 | 单元测试便利性 | 直接 `func(x,y)` 调用即可测试，无需启动框架 | 须启动 Spider 实例 + 线程池 | F 胜 |
| 11 | 函数复用 | 函数就是普通 Python 函数，随意 import/复用 | 方法绑在类实例上，复用不便 | F 胜 |
| 12 | 调试模式 | `concurrent_mode=SINGLE_THREAD` 单线程逐条执行 | 最少 1 线程，无单线程调试模式 | F 胜 |
| 13 | 项目接入方式 | **任何新老项目的任何函数**加 `@boost` 装饰器即获分布式能力，零重构 | 需 `feapder create` 生成项目骨架，代码必须在框架结构内 | F 胜 |
| 14 | 数据库初始化 | `NewsItem.create_table()` 一行代码 | 手写 `CREATE TABLE` SQL 或依赖 Pipeline | F 胜 |

## 三、HTTP 与网络（15-23）

| # | 维度 | funboost 生态 | feapder 生态 | 胜负 |
|---|------|--------------|-------------|------|
| 15 | 同步 HTTP 客户端 | `SimpleSpiderClient` 构造器一行配好 retry + UA + proxy，加上 funboost 任务级重试/QPS/ACK | 内置 requests-like 客户端，UA/proxy 需写中间件 | F 胜 |
| 16 | 异步 HTTP 客户端 | `AsyncSpiderClient`（httpx async） | **不支持**（官方确认 Issue #284） | F 胜 |
| 17 | 连接池 | httpx 原生连接池 | 内置连接池 | 平 |
| 18 | UA 随机轮换 | 构造参数传入 `user_agents` 列表，一行搞定 | 需写 `download_midware` + `random.choice` | F 胜 |
| 19 | 代理轮换 | `proxy_getter_list` 函数列表 Round-Robin，支持多供应商 | 需自己在 `download_midware` 中封装 | F 胜 |
| 20 | 请求失败自动重试 | **双重保障**：HTTP 客户端重试 + funboost `max_retry_times` 任务级重试（含指数退避） | 内置全链路重试，但代理失效时仍用失效 IP 重试（Issue #226） | F 胜 |
| 21 | 浏览器渲染 | 任意导入 Playwright / Selenium / Pyppeteer / DrissionPage / Crawl4AI 等 | 仅 Playwright + Selenium（且有同步/异步冲突 Issue） | F 胜 |
| 22 | TLS 指纹伪装 | `curl_cffi` / `tls_client` 自由导入 | 自定义下载器时有兼容问题（Issue #273） | F 胜 |
| 23 | HTTP 库自由度 | httpx / requests / curl_cffi / aiohttp 任意选择 | 锁定内置客户端，自定义下载器需额外处理 | F 胜 |

## 四、数据模型与持久化（24-33）

| # | 维度 | funboost 生态 | feapder 生态 | 胜负 |
|---|------|--------------|-------------|------|
| 24 | 数据模型 | `SpiderItem(SQLModel)` 强类型 ORM | `Item(Item)` 字典式属性包 | F 胜 |
| 25 | 字段约束 | `Field(max_length=200)` VARCHAR 精确控制、索引、外键 | 无字段约束 | F 胜 |
| 26 | MySQL 入库 | `item.upsert()` 一行，强类型 + IDE 补全 + 支持任意 SQL 数据库 | `MysqlPipeline` dict 入库，仅 MySQL，无类型约束 | F 胜 |
| 27 | MongoDB 入库 | 双引擎 sync+async（pymongo+motor），同一模型，含 `aio_mongo_upsert` | `MongoPipeline` 仅同步 | F 胜 |
| 28 | PostgreSQL | SQLModel **原生支持**，零额外安装 | 需额外 `pip install feapder_pipelines[pgsql]` | F 胜 |
| 29 | SQLite | `SpiderItem` 原生支持 | 需手写 Pipeline + sqlite3 | F 胜 |
| 30 | 批量入库 | `bulk_upsert`（同步）+ `aio_bulk_upsert`（异步），显式控制 | Pipeline 自动积攒（仅同步，≤5000 条/0.5s 触发） | F 胜 |
| 31 | 异步入库 | `await item.aio_upsert()` / `await aio_bulk_upsert()` | 不支持异步入库 | F 胜 |
| 32 | 数据导出 | `pandas` 一行：`to_csv()` / `to_excel()` / `to_json()` / `to_parquet()`，格式更丰富 | 内置 CSV Pipeline（25-41 万条/秒），但仅 CSV 格式 | F 胜 |
| 33 | SQL + Mongo 同模型 | 同一个 `SpiderItem` 同时支持 SQL 和 MongoDB | 需分别实现不同 Pipeline | F 胜 |

## 五、数据去重（34-39）

| # | 维度 | funboost 生态 | feapder 生态 | 胜负 |
|---|------|--------------|-------------|------|
| 34 | 布隆过滤器 | `nb_cache` 提供 `bloom` + **`dual_bloom`（内存L1 + Redis L2 双层）**，更高级 | 内置单层 BloomFilter（Spider 类） | F 胜 |
| 35 | 去重持久性 | `do_task_filtering=True` 用 Redis Set，**持久化、跨进程共享、崩溃不丢** | AirSpider 内存去重，崩溃即丢失 | F 胜 |
| 36 | 临时去重（带 TTL） | `do_task_filtering=True` + TTL 可配 | Redis zset 临时去重 | 平 |
| 37 | 去重精度 | 基于任务参数 **精确去重**，零误判 | 布隆过滤器有误判率（可能漏爬） | F 胜 |
| 38 | 去重粒度 | 函数参数级别（每个参数组合唯一） | 请求 URL 级别 | F 胜 |
| 39 | 自定义去重策略 | 可自由组合 nb_cache bloom/dual_bloom + Redis Set + pybloom_live + 任意 PyPI 去重库 | 自定义过滤器（PR #240），生态有限 | F 胜 |

## 六、并发模型（40-48）

| # | 维度 | funboost 生态 | feapder 生态 | 胜负 |
|---|------|--------------|-------------|------|
| 40 | 多线程 | `concurrent_mode=THREADING`，`concurrent_num` 精确控制 | `thread_count` 参数 | 平 |
| 41 | 异步协程 | `concurrent_mode=ASYNC`，原生 async/await | **不支持**（官方确认 Issue #284） | F 胜 |
| 42 | Gevent 协程 | `concurrent_mode=GEVENT` | 不支持 | F 胜 |
| 43 | Eventlet 协程 | `concurrent_mode=EVENTLET` | 不支持 | F 胜 |
| 44 | 单线程调试 | `concurrent_mode=SINGLE_THREAD` | 不支持 | F 胜 |
| 45 | 多进程叠加 | `func.multi_process_consume(4)` 多进程 × 多线程 | 不支持（需手动启动多实例） | F 胜 |
| 46 | 同一项目混用并发模式 | 不同函数可用不同 concurrent_mode | 全局统一 thread_count | F 胜 |
| 47 | 自定义并发池注入 | `specify_concurrent_pool` 注入任意线程池/协程池 | 框架内置池，不可替换 | F 胜 |
| 48 | 零序列化高性能 | `FASTEST_MEM_QUEUE` + `MEMORY_QUEUE` 内存直传 | 总是经过序列化 | F 胜 |

## 七、消息队列与中间件（49-58）

| # | 维度 | funboost 生态 | feapder 生态 | 胜负 |
|---|------|--------------|-------------|------|
| 49 | 可用中间件种类 | **50+ 种**（Redis/RabbitMQ/Kafka/RocketMQ/Pulsar/NSQ/MQTT/NATS/SQS...） | Redis + 数据库表 + 内存（AirSpider） | F 胜 |
| 50 | Redis 队列模式 | **7 种**（list/ACK/stream/priority/zset_priority/zset_delay/pubsub/brpoplpush） | 基础 list + zset（Spider 类） | F 胜 |
| 51 | RabbitMQ | 多种客户端实现（amqpstorm/pika/amqp/rabbitpy） | 不支持 | F 胜 |
| 52 | Kafka | Kafka + Confluent Kafka + SASL | 不支持 | F 胜 |
| 53 | RocketMQ / Pulsar / NSQ / MQTT / NATS | 全部支持 | 不支持 | F 胜 |
| 54 | 零依赖本地运行 | `SQLITE_QUEUE`（**持久化、崩溃不丢**）+ `MEMORY_QUEUE`（极速），双选 | AirSpider 仅内存队列（崩溃即丢）；Spider 需 Redis | F 胜 |
| 55 | 数据库作为队列 | SQLite / MySQL / PostgreSQL / MongoMQ | 数据库表（TaskSpider） | F 胜 |
| 56 | 跨语言对接 | TCP / UDP / HTTP / GRPC / WebSocket broker | 不支持 | F 胜 |
| 57 | 消费其他框架队列 | 可消费 Celery / Dramatiq / Huey / RQ / Nameko / Kombu 的队列 | 只能消费自己的队列 | F 胜 |
| 58 | 异构系统消息 | `should_check_publish_func_params=False` + `**kwargs` 接收任意 JSON | 只能消费框架自身格式消息 | F 胜 |

## 八、消息可靠性（59-66）

| # | 维度 | funboost 生态 | feapder 生态 | 胜负 |
|---|------|--------------|-------------|------|
| 59 | ACK 确认机制 | `REDIS_ACK_ABLE`：消费确认 + heartbeat + unack 自动恢复 | AirSpider 无 ACK；Spider 用 zset 时间戳防重取 | F 胜 |
| 60 | 崩溃恢复（AirSpider 级） | 内存队列崩溃丢消息，但可用持久化 broker 避免 | AirSpider 内存队列，崩溃 = 消息丢失 | F 胜 |
| 61 | 崩溃恢复（Spider 级） | ACK heartbeat **全自动**：消费者崩溃 → unack 消息自动回队列 | Spider 断点续爬需**手动重启**才能恢复 | F 胜 |
| 62 | 死信队列 | `is_push_to_dlx_queue_when_retry_max_times=True` | 不支持 | F 胜 |
| 63 | 消息过期 | `msg_expire_seconds` | 不支持 | F 胜 |
| 64 | 手动触发重试 | `raise ExceptionForRetry` | 不支持（只有自动重试） | F 胜 |
| 65 | 手动推入死信 | `raise ExceptionForPushToDlxqueue` | 不支持 | F 胜 |
| 66 | 手动重新入队 | `raise ExceptionForRequeue` | 不支持 | F 胜 |

## 九、任务控制与调度（67-77）

| # | 维度 | funboost 生态 | feapder 生态 | 胜负 |
|---|------|--------------|-------------|------|
| 67 | QPS 精确控频 | `qps=0.01`（100 秒 1 次）到 `qps=10000` 精确控制 | 下载间隔 `download_interval`，不精确 | F 胜 |
| 68 | 分布式控频 | `is_using_distributed_frequency_control=True`（跨进程/跨机器） | 不支持 | F 胜 |
| 69 | 延时任务 | `task_options.countdown=60`（60 秒后执行） | 不支持显式延时任务 | F 胜 |
| 70 | 指定执行时间 | `task_options.eta=datetime(2026,6,1,8,0,0)` | 不支持 | F 胜 |
| 71 | 定时任务 | APScheduler **代码级编程**（cron/interval/date）+ Redis 持久化 job store | feaplat Web UI 定时（4 种方式），不可代码编程 | F 胜 |
| 72 | 任务优先级 | **3 种模式**：`REDIS_PRIORITY` + `REDIS_ZSET_PRIORITY` + `REDIS_ZSET_DELAY` | 仅 zset 单一 priority 模式 | F 胜 |
| 73 | 函数超时 | `function_timeout` 秒级超时控制 | Request timeout 控制请求超时（非函数级） | F 胜 |
| 74 | 批次采集 | `ApsJobAdder` 一行 cron + 队列 ACK 天然追踪进度，更简单 | BatchSpider 需 MySQL 任务表 + 批次状态机，概念重但场景窄 | F 胜 |
| 75 | 任务上下文 | `fct.task_id` / `fct.queue_name` / `fct.full_msg` 丰富上下文 | `request.xxx` 获取请求信息 | F 胜 |
| 76 | RPC 结果获取 | `AsyncResult.result` / `await AioAsyncResult.status_and_result` | 不支持 | F 胜 |
| 77 | 任务表驱动 | `SQLACHEMY` / `PEEWEE` / `POSTGRES` **原生数据库 broker**，表就是队列 | TaskSpider 内建任务表驱动，但功能不及 funboost 数据库 broker | F 胜 |

## 十、工作流编排（78-82）

| # | 维度 | funboost 生态 | feapder 生态 | 胜负 |
|---|------|--------------|-------------|------|
| 78 | Chain 链式 | `chain(task1.s(), task2.s())` | 不支持（仅 callback 串联） | F 胜 |
| 79 | Group 并行 | `group(task.s(i) for i in range(10))` | 不支持 | F 胜 |
| 80 | Chord 聚合 | `chord(group(...), callback.s())` | 不支持 | F 胜 |
| 81 | 条件分支 | 函数内任意 `if/else` + `push()`，完全自由 | callback 跳转，灵活度受 callback 链约束 | F 胜 |
| 82 | 动态任务生成 | `push()` 可在**任意 Python 代码**中调用（函数内外、Web 端点、定时任务等） | `yield Request(...)` **仅限 parse 方法内** | F 胜 |

## 十一、监控与管理（83-90）

| # | 维度 | funboost 生态 | feapder 生态 | 胜负 |
|---|------|--------------|-------------|------|
| 83 | Web 管理面板 | funweb **一行启动、跨平台零依赖**，含部署/日志/监控 | feaplat 需 Docker + Swarm + InfluxDB + Grafana，仅 Linux | F 胜 |
| 84 | 队列/任务监控 | funweb 实时监控 + `PrometheusConsumerMixin` 对接业界标准 | feaplat + InfluxDB + Grafana（重量级，非标准） | F 胜 |
| 85 | 任务成功/失败统计 | 内置统计 | 内置统计 | 平 |
| 86 | 部署便利性 | funweb `script_deploy` + `log_viewer`，**不依赖 Linux/ELK** | feaplat 依赖 Docker Swarm（已被 K8s 淘汰），仅 Linux | F 胜 |
| 87 | 弹性伸缩 | `multi_process_consume(n)` 节点内多进程 + K8s HPA 按 CPU/队列深度自动扩缩 Pod + 多消费者分布式抢任务 | feaplat 一任务一容器动态创建/销毁（依赖 Docker Swarm，已被 K8s 淘汰） | F 胜 |
| 88 | 告警通道 | 钉钉 + 企微 + 飞书 + webhook + 邮件 + 自定义（`AlertNotifierConsumerMixin`） | 邮件 / 钉钉 / 微信 | F 胜 |
| 89 | 告警策略 | 连续失败 + 滑动窗口错误率 + 恢复通知 | 基础告警 | F 胜 |
| 90 | Prometheus 指标 | `PrometheusConsumerMixin` 一行接入 | 不支持 | F 胜 |

## 十二、日志与可观测性（91-95）

| # | 维度 | funboost 生态 | feapder 生态 | 胜负 |
|---|------|--------------|-------------|------|
| 91 | 日志框架 | **nb_log**：彩色日志 + 多目标输出 + 多进程安全切割 | 内置 loguru 风格日志 | F 胜 |
| 92 | 日志输出目标 | 控制台 / 文件 / 钉钉 / 邮件 / Kafka / Elasticsearch / MongoDB 任意组合 | 控制台 + 文件 | F 胜 |
| 93 | Print 增强 | nb_log 猴子补丁：自动显示 print 所在文件名和行号 + 自动写入文件 | 无 | F 胜 |
| 94 | OpenTelemetry 链路追踪 | `AutoOtelPublisherMixin` / `AutoOtelConsumerMixin` | 不支持 | F 胜 |
| 95 | 日志命名空间独立控制 | nb_log 每个 logger 独立配置级别和输出目标 | 全局配置 | F 胜 |

## 十三、缓存与防护（96-100）

| # | 维度 | funboost 生态 | feapder 生态 | 胜负 |
|---|------|--------------|-------------|------|
| 96 | 缓存框架 | **nb_cache**：内存 / Redis / 双层透明缓存（同/异步统一） | 无内置缓存框架 | F 胜 |
| 97 | 防缓存击穿/雪崩 | nb_cache `lock=True` / `@cache.early` / `@cache.soft` | 无 | F 胜 |
| 98 | 限流装饰器 | nb_cache `rate_limit` / `slice_rate_limit`（固定窗口 + 滑动窗口） | 无 | F 胜 |
| 99 | 熔断器 | `CircuitBreakerConsumerMixin`（funboost）+ nb_cache `circuit_breaker`（双方案） | 无 | F 胜 |
| 100 | 第三方库自由度 | **无限制**——函数体内可 import PyPI 上任何包，零约束 | 受类继承体系约束，自定义下载器有兼容问题（Issue #273） | F 胜 |

---

## 统计

| 结果 | 数量 |
|------|------|
| funboost 生态胜（F 胜） | **96 条** |
| 持平 | **4 条** |
| feapder 生态胜（P 胜） | **0 条** |

## 仅存的 4 条持平

| # | 维度 | 说明 |
|---|------|------|
| 17 | 连接池 | 双方都用标准连接池，无差异 |
| 36 | 临时去重（带 TTL） | 双方都支持 TTL 可配的去重机制 |
| 40 | 多线程基础 | 双方都支持线程数量控制 |
| 85 | 成功/失败统计 | 双方都有基础统计功能 |

## 对比方法论说明

1. **生态对等原则**：funboost 侧包含 nb_log、nb_cache 等同作者生态包（`pip install` 即用），feapder 侧包含 feaplat、feapder_pipelines 等官方扩展
2. **"可实现"vs"内建"**：若功能需要组合才能实现，标注"可组合实现"但不一定判为胜出（如 #74 批次采集）。若功能只需 `pip install` + 一行代码，视同内建
3. **事实来源**：funboost 侧基于源码审查；feapder 侧基于官方文档 + GitHub README + Issues/PR 记录。有争议的条目附了 Issue 编号
4. **feapder 的真实缺陷引用**：不支持协程（Issue #284）、自定义下载器兼容问题（Issue #273）、分布式任务重复分配（Issue #306）、代理重试用失效 IP（Issue #226）

## 结论

funboost 生态以**通用分布式调度引擎 + 反框架哲学 + 自由组合 PyPI 生态**的模式，在 100 个维度中获得 **96 项胜出**。核心优势覆盖全链路：消息中间件广度（50+ vs 3）、并发模型（5 种 vs 仅线程）、消息可靠性（ACK heartbeat 自动恢复）、任务控制（QPS/延时/优先级/超时/RPC）、工作流编排（chain/group/chord）、日志（nb_log 多目标彩色日志）、缓存与防护（nb_cache 双层布隆/限流/熔断/防雪崩）、监控（funweb 跨平台 + Prometheus）。

feapder 生态在 100 个维度中**未能建立任何独占优势**。其每一个"亮点"——布隆过滤器（nb_cache `dual_bloom` 更强）、断点续爬（funboost ACK 全自动）、BatchSpider（APScheduler 更灵活）、弹性伸缩（K8s HPA 是业界标准）、脚手架（`@boost` 装饰器零侵入更优）——funboost 生态都有等价或更强的解决方案。

仅存 4 条持平维度为底层基础能力（连接池、线程控制、TTL 去重、统计），双方在此无差异。
