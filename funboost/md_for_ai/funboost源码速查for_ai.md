# funboost 源码速查 for AI

> 本文档专为 AI 设计，用于快速定位 funboost 源码中的类、函数、模块位置。
>
> 生成时间: 2026-05-13 （请注意时间，部分代码文件的行号有可能会随时间发生小幅变化）
>
> 源码根目录: `funboost/funboost/`
>
> 所有路径均相对于 `funboost/funboost/` 目录。

## AI 使用指南

**当你收到用户关于 funboost 源码的提问时，请按以下优先级查找：**

1. **先查"第十八章 用户自然语言问题路由表"** — 根据用户问题中的关键词，直接跳转到对应源码文件和行号
2. **再查"第十九章 按实现层面快速检索"** — 如果用户使用技术术语（类名、函数名），在此表中精确定位
3. **需要了解全貌时查"第一章 目录总览"** — 获取整体架构感知
4. **需要了解某个 broker 时查"第十五章 Broker映射表"** — 50种broker的Consumer/Publisher类和文件一一对应
5. **需要了解公共 API 时查"第十六章 导出清单"** — 确认哪些名字可以从 `funboost` 直接 import

**关键约定：**
- 所有行号 `(Lxx)` 均为源码中经过验证的精确行号，可直接用 `Read(file, offset=xx)` 跳转
- 文件路径相对于 `funboost/funboost/` 目录，例如 `core/booster.py` 实际是 `funboost/funboost/core/booster.py`
- 第十七章第四节列出了文件名中的拼写特殊之处，搜索文件时请注意

> **必读！配套 AI 编程指南**：`md_for_ai/funboost_ai_coding_编程指南_rules_and_skills.md`
> 包含 BoosterParams 全量字段定义（Skill 100）、AI 行为铁律（禁止臆造参数、正确使用 `fct`、push vs publish 区别等）和 12 个标准代码技能模板。
> **生成任何 funboost 代码前须先读此文件。**

---
## 一、目录总览

```
funboost/
├── __init__.py                    # 包入口，导出所有公共 API
├── __main__.py                    # CLI 入口: fire.Fire(BoosterFire)
├── constant.py                    # BrokerEnum, ConcurrentModeEnum 等常量
├── funboost_config_deafult.py     # BrokerConnConfig, FunboostCommonConfig 默认配置
├── set_frame_config.py            # 加载用户 funboost_config.py，合并配置
├── core/                          # 核心模块
│   ├── booster.py                 # Booster 装饰器、BoosterRegistry
│   ├── func_params_model.py       # BoosterParams 参数模型
│   ├── current_task.py            # fct 当前任务上下文
│   ├── msg_result_getter.py       # AsyncResult / AioAsyncResult RPC结果
│   ├── function_result_status_saver.py  # FunctionResultStatus 运行状态
│   ├── serialization.py           # 序列化
│   ├── exceptions.py              # 所有异常类
│   ├── helper_funs.py             # MsgGenerater 消息工具
│   ├── funboost_pool.py           # FunboostPool 进程池封装
│   ├── kill_remote_task.py        # RemoteTaskKiller 远程杀任务
│   ├── consuming_func_input_params_check.py  # 消费函数入参校验
│   ├── active_cousumer_info_getter.py  # 活跃消费者信息
│   ├── loggers.py                 # 日志器
│   ├── task_id_logger.py          # TaskIdLogger
│   ├── funboost_time.py           # FunboostTime 时间处理
│   ├── funboost_config_getter.py  # 用户配置加载
│   ├── lazy_impoter.py            # 懒加载可选依赖
│   ├── pydantic_compatible_base.py # Pydantic v1/v2 兼容
│   ├── muliti_process_enhance.py  # 多进程增强
│   ├── fabric_deploy_helper.py    # 远程部署
│   ├── mongo_alert_monitor.py     # Mongo 报警监控
│   ├── broker_kind__exclusive_config_default_define.py  # broker专属配置默认值
│   └── cli/                       # 命令行
│       ├── funboost_fire.py       # BoosterFire CLI命令
│       ├── discovery_boosters.py  # BoosterDiscovery 自动发现
│       └── funboost_cli_user_templ.py  # 用户CLI模板
├── consumers/                     # 消费者实现 (49个py文件)
│   ├── __init__.py                # 包入口
│   ├── base_consumer.py           # AbstractConsumer 消费者基类
│   ├── confirm_mixin.py           # Redis心跳ACK mixin
│   ├── empty_consumer.py          # EmptyConsumer 空实现
│   ├── redis_consumer.py          # Redis List
│   ├── redis_consumer_simple.py   # Redis 简单实现
│   ├── redis_consumer_ack_able.py # Redis ACK
│   ├── redis_consumer_ack_using_timeout.py  # Redis ACK超时实现
│   ├── redis_consumer_priority.py # Redis 优先级
│   ├── redis_stream_consumer.py   # Redis Stream
│   ├── redis_brpoplpush_consumer.py # Redis 双队列
│   ├── redis_pubsub_consumer.py   # Redis PubSub
│   ├── redis_filter.py            # Redis 过滤
│   ├── rabbitmq_amqpstorm_consumer.py  # RabbitMQ (amqpstorm, 推荐)
│   ├── rabbitmq_pika_consumer.py  # RabbitMQ (pika)
│   ├── rabbitmq_rabbitpy_consumer.py   # RabbitMQ (rabbitpy)
│   ├── rabbitmq_amqp_consumer.py  # RabbitMQ (amqp)
│   ├── rabbitmq_complex_routing_consumer.py  # RabbitMQ 复杂路由
│   ├── kafka_consumer.py          # Kafka (kafka-python, 自动提交)
│   ├── kafka_consumer_manually_commit.py  # Kafka (confluent, 手动提交)
│   ├── rocketmq_consumer.py       # RocketMQ 4
│   ├── rocketmq5_consumer.py      # RocketMQ 5
│   ├── pulsar_consumer.py         # Pulsar
│   ├── nsq_consumer.py            # NSQ
│   ├── mqtt_consumer.py           # MQTT
│   ├── zeromq_consumer.py         # ZeroMQ
│   ├── mongomq_consumer.py        # MongoDB
│   ├── persist_queue_consumer.py  # SQLite (persistqueue)
│   ├── sqlachemy_consumer.py      # SQLAlchemy
│   ├── postgres_consumer.py       # PostgreSQL
│   ├── peewee_consumer.py         # Peewee ORM
│   ├── tcp_consumer.py            # TCP
│   ├── udp_consumer.py            # UDP
│   ├── http_consumer.py           # HTTP
│   ├── http_consumer_aiohttp_old.py  # HTTP (aiohttp旧版)
│   ├── grpc_consumer.py           # gRPC
│   ├── sqs_consumer.py            # AWS SQS
│   ├── httpsqs_consumer.py        # HTTPSQS
│   ├── txt_file_consumer.py       # 文本文件
│   ├── local_python_queue_consumer.py   # Python queue.Queue
│   ├── fastest_mem_queue_consumer.py    # collections.deque
│   ├── memory_deque_consumer.py   # deque 变体
│   ├── celery_consumer.py         # Celery
│   ├── dramatiq_consumer.py       # Dramatiq
│   ├── huey_consumer.py           # Huey
│   ├── rq_consumer.py             # RQ
│   ├── nameko_consumer.py         # Nameko
│   ├── kombu_consumer.py          # Kombu
│   ├── mysql_cdc_consumer.py      # MySQL CDC
│   └── faststream_consumer.py     # FastStream
├── publishers/                    # 发布者实现 (45个py文件)
│   ├── __init__.py                # 包入口
│   ├── base_publisher.py          # AbstractPublisher 发布者基类
│   ├── empty_publisher.py         # EmptyPublisher 空实现
│   ├── redis_publisher.py         # Redis List
│   ├── redis_publisher_simple.py  # Redis 简单实现
│   ├── redis_publisher_lpush.py   # Redis LPUSH
│   ├── redis_publisher_priority.py # Redis 优先级
│   ├── redis_stream_publisher.py  # Redis Stream
│   ├── redis_pubsub_publisher.py  # Redis PubSub
│   ├── redis_queue_flush_mixin.py # FlushRedisQueueMixin
│   ├── rabbitmq_amqpstorm_publisher.py  # RabbitMQ (amqpstorm, 推荐)
│   ├── rabbitmq_pika_publisher.py       # RabbitMQ (pika)
│   ├── rabbitmq_rabbitpy_publisher.py   # RabbitMQ (rabbitpy)
│   ├── rabbitmq_amqp_publisher.py       # RabbitMQ (amqp)
│   ├── rabbitmq_complex_routing_publisher.py  # RabbitMQ 复杂路由
│   ├── kafka_publisher.py         # Kafka (kafka-python)
│   ├── confluent_kafka_publisher.py # Kafka (confluent)
│   ├── rocketmq_publisher.py      # RocketMQ 4
│   ├── rocketmq5_publisher.py     # RocketMQ 5
│   ├── pulsar_publisher.py        # Pulsar
│   ├── nsq_publisher.py           # NSQ
│   ├── mqtt_publisher.py          # MQTT
│   ├── zeromq_publisher.py        # ZeroMQ
│   ├── mongomq_publisher.py       # MongoDB
│   ├── persist_queue_publisher.py # SQLite (persistqueue)
│   ├── sqla_queue_publisher.py    # SQLAlchemy
│   ├── postgres_publisher.py      # PostgreSQL
│   ├── peewee_publisher.py        # Peewee ORM
│   ├── tcp_publisher.py           # TCP
│   ├── udp_publisher.py           # UDP
│   ├── http_publisher.py          # HTTP
│   ├── grpc_publisher.py          # gRPC
│   ├── sqs_publisher.py           # AWS SQS
│   ├── httpsqs_publisher.py       # HTTPSQS
│   ├── txt_file_publisher.py      # 文本文件
│   ├── local_python_queue_publisher.py   # Python queue.Queue
│   ├── fastest_mem_queue_publisher.py    # collections.deque
│   ├── memory_deque_publisher.py # deque 变体
│   ├── celery_publisher.py        # Celery
│   ├── dramatiq_publisher.py      # Dramatiq
│   ├── huey_publisher.py          # Huey
│   ├── rq_publisher.py            # RQ
│   ├── nameko_publisher.py        # Nameko
│   ├── kombu_publisher.py         # Kombu
│   ├── mysql_cdc_publisher.py     # MySQL CDC
│   └── faststream_publisher.py    # FastStream
├── factories/                     # 工厂模块
│   ├── broker_kind__publsiher_consumer_type_map.py  # broker→类映射 + register_custom_broker
│   ├── consumer_factory.py        # get_consumer 工厂
│   └── publisher_factory.py      # get_publisher 工厂
├── concurrent_pool/               # 并发池
│   ├── readme.md                  # 并发池说明文档
│   ├── __init__.py                # 导出所有池类
│   ├── base_pool_type.py          # FunboostBaseConcurrentPool 基类
│   ├── pool_commons.py            # ConcurrentPoolBuilder
│   ├── flexible_thread_pool.py    # FlexibleThreadPool 弹性线程池
│   ├── custom_threadpool_executor.py  # ThreadPoolExecutorShrinkAble 可收缩线程池
│   ├── fixed_thread_pool.py       # FixedThreadPool
│   ├── bounded_threadpoolexcutor.py   # BoundedThreadPoolExecutor
│   ├── single_thread_executor.py  # SoloExecutor 单线程
│   ├── async_pool_executor.py     # AsyncPoolExecutor
│   ├── custom_gevent_pool_executor.py  # GeventPoolExecutor
│   ├── custom_evenlet_pool_executor.py # EventletPoolExecutor
│   ├── concurrent_pool_with_multi_process.py  # ConcurrentPoolWithProcess
│   └── async_helper.py            # get_or_create_event_loop
├── timing_job/                    # 定时任务 (APScheduler)
│   ├── __init__.py                # 导出 funboost_aps_scheduler, ApsJobAdder 等
│   ├── timing_job_base.py         # FunboostBackgroundScheduler 全局调度器
│   ├── timing_push.py             # ApsJobAdder 定时推送
│   ├── apscheduler_use_redis_store.py  # Redis jobstore
│   └── apscheduler_use_mysql_store.py  # MySQL jobstore
├── faas/                          # FaaS HTTP接口
│   ├── README.md                  # FaaS说明文档
│   ├── __init__.py                # 懒加载导出
│   ├── fastapi_adapter.py         # fastapi_router FastAPI路由
│   ├── flask_adapter.py           # flask_blueprint Flask蓝图
│   ├── django_adapter.py          # Django视图
│   └── faas_util.py               # gen_aps_job_adder
├── workflow/                      # 工作流编排 (chain/group/chord)
│   ├── README.md                  # 工作流说明文档
│   ├── __init__.py                # 导出 + 给Booster打补丁 .s()/.si()
│   ├── signature.py               # Signature 签名
│   ├── primitives.py              # Chain, Group, Chord
│   ├── workflow_mixin.py          # WorkflowPublisherMixin, WorkflowConsumerMixin
│   ├── params.py                  # WorkflowBoosterParams
│   └── examples/                   # 工作流示例
│       ├── __init__.py
│       └── video_pipeline.py
├── contrib/                       # 扩展贡献模块
│   ├── funboost框架的额外贡献功能.md  # 扩展功能说明
│   ├── api_publish_msg.py         # Pydantic MsgItem/PublishResponse
│   ├── queue2queue.py             # 队列转发
│   ├── django_db_deco.py          # Django DB兼容装饰器
│   ├── redis_consume_latest_msg_broker.py  # 只消费最新消息
│   ├── cdc/mysql2mysql.py         # MySql2Mysql CDC同步
│   ├── cdc/mysql_cdc_binlog_listener.py  # MySQL binlog 监听器
│   ├── override_publisher_consumer_cls/   # Mixin扩展
│   │   ├── README.md                      # Mixin扩展说明
│   │   ├── circuit_breaker_mixin.py       # 熔断器
│   │   ├── funboost_micro_batch_mixin.py  # 微批消费
│   │   ├── funboost_promethus_mixin.py    # Prometheus
│   │   ├── funboost_otel_mixin.py         # OpenTelemetry
│   │   ├── otel_tree_span_exporter.py     # OTel TreeSpan
│   │   ├── periodic_quota_mixin.py        # 周期额度
│   │   └── alert_notifier_mixin.py        # 告警通知
│   ├── register_custom_broker_contrib/    # 自定义broker
│   │   ├── watchdog_broker.py     # WatchdogPublisher/Consumer 文件监控
│   │   ├── websocket_broker.py    # WebSocketPublisher/Consumer
│   │   ├── nats_core_broker.py    # NATS Core Publisher/Consumer
│   │   ├── nats_jetstream_broker.py # NATS JetStream Publisher/Consumer
│   │   ├── redis_zset_broker.py   # Redis ZSet Publisher/Consumer
│   │   ├── redis_hash_update_broker.py  # Redis HASH 可更新覆盖
│   │   └── celery_pool_as_funboost_broker.py  # CeleryPool 作为 funboost broker
│   ├── funspider/                         # 爬虫辅助扩展(httpx+SQLModel)
│   │   ├── __init__.py            # 导出 SimpleSpiderClient, AsyncSpiderClient, SpiderItem
│   │   ├── http.py                # SpiderResponse, SimpleSpiderClient, AsyncSpiderClient
│   │   ├── item.py                # SpiderItem (SQLModel ORM, sync/async insert/upsert)
│   │   ├── README.md              # funspider说明文档
│   │   └── funspider_demos/       # 爬虫示例
│   │       ├── funspider_demo1.py # 新闻爬虫完整示例(同步+异步混用)
│   │       └── fake_news_site.py  # 模拟新闻网站(FastAPI)
│   └── save_function_result_status/       # 结果持久化
│       ├── readme.md                      # 结果持久化说明
│       ├── save_result_status_to_sqldb.py
│       └── save_result_status_use_dataset.py
├── queues/                        # 队列实现
│   ├── memory_queues_map.py       # PythonQueues 内存队列映射
│   ├── fastest_mem_queue.py       # FastestMemQueue / FastestMemQueues
│   ├── sqla_queue.py              # SqlaQueue SQLAlchemy队列
│   ├── peewee_queue.py            # PeeweeQueue
│   └── postgres_queue.py          # PostgresQueue (SKIP LOCKED + NOTIFY)
├── assist/                        # 第三方框架集成辅助
│   ├── celery_helper.py           # CeleryHelper
│   ├── celery_pool.py             # CeleryPool 封装为 concurrent.futures.Executor 兼容接口
│   ├── dramatiq_helper.py         # DramatiqHelper
│   ├── huey_helper.py             # HueyHelper
│   ├── rq_helper.py               # RqHelper
│   ├── rq_windows_worker.py       # WindowsWorker
│   ├── faststream_helper.py       # get_broker, app
│   ├── taskiq_helper.py           # (空文件占位)
│   └── grpc_helper/               # gRPC proto + 生成代码 + 示例
│       ├── funboost_grpc.proto
│       ├── funboost_grpc_pb2.py
│       ├── funboost_grpc_pb2_grpc.py
│       ├── client_sample.py
│       ├── server_sample.py
│       └── generate_pb.py
├── funweb/                        # Web管理界面 (Flask)
│   ├── README.md                  # Web管理说明文档
│   ├── app.py                     # Flask app, start_funboost_web_manager
│   ├── functions.py               # Mongo 查询辅助
│   ├── flask_bps/                 # Flask蓝图
│   │   ├── web_helper.py          # IP/hostname
│   │   ├── system_monitor.py      # 系统监控API
│   │   ├── script_deploy.py       # 脚本部署CRUD
│   │   ├── log_viewer.py          # 日志查看器
│   │   └── queue_alerts.py        # 队列告警系统(积压/QPS/掉线/失败率/耗时)
│   ├── templates/                 # 15个HTML模板
│   │   ├── index.html             # 首页
│   │   ├── login.html             # 登录页
│   │   ├── about.html             # 关于页
│   │   ├── fun_result_table.html  # 函数运行结果表
│   │   ├── conusme_speed.html     # 消费速度图表
│   │   ├── queue_op.html          # 队列操作
│   │   ├── rpc_call.html          # RPC调用
│   │   ├── timing_jobs_management.html  # 定时任务管理
│   │   ├── running_consumer_by_queue_name.html  # 按队列名查消费者
│   │   ├── running_consumer_by_ip.html  # 按IP查消费者
│   │   ├── care_project_name.html # 项目名筛选
│   │   ├── deploy_list.html       # 部署列表
│   │   ├── deploy_detail.html     # 部署详情
│   │   ├── log_viewer.html        # 日志查看器
│   │   ├── system_monitor.html    # 系统监控
│   │   ├── queue_alerts.html      # 告警配置页面(规则CRUD+告警记录+测试通知)
│   │   └── app.py中仍在使用的路由.md  # 路由参考文档
│   ├── _ai_do_tasks_md/           # AI任务备忘
│   │   ├── ai写web必须遵守的.md
│   │   └── 增加日志查看.md
│   └── static/                    # CSS/JS/字体/图片
├── funboost_web_manager/          # (旧名, 转发到funweb)
│   ├── README.md
│   ├── app.py
│   └── functions.py
├── README.md                      # 包README
├── __init__old.py                 # 旧版init (兼容保留)
├── utils/                         # 工具模块
│   ├── README.md                  # 工具模块说明
│   ├── decorators.py              # keep_circulating, singleton, timer等
│   ├── redis_manager.py           # RedisManager, RedisMixin, AioRedisMixin
│   ├── mongo_util.py              # MongoMixin
│   ├── class_utils.py             # ClsHelper
│   ├── str_utils.py               # PwdEnc, StrHelper
│   ├── json_helper.py             # JSON兼容
│   ├── un_strict_json_dumps.py    # 宽松JSON
│   ├── time_util.py               # 时间工具
│   ├── uuid7.py                   # UUID7
│   ├── system_util.py             # 系统信息
│   ├── ctrl_c_end.py              # ctrl_c_recv
│   ├── block_exit.py              # 阻止退出
│   ├── task_dispatcher.py         # LocalFunctionsDispatcher
│   ├── bulk_operation.py          # 批量Mongo/ES/Redis写入
│   ├── expire_lock.py             # 过期锁
│   ├── notify_util.py             # Notifier
│   ├── paramiko_util.py           # ParamikoFolderUploader SSH上传
│   ├── rabbitmq_factory.py        # Pika/RabbitPy客户端
│   ├── mqtt_util.py               # MqttHttpHelper
│   ├── resource_monitoring.py     # ResourceMonitor
│   ├── restart_python.py          # 重启Python
│   ├── apscheduler_monkey.py      # APScheduler补丁
│   ├── monkey_color_log.py        # 日志着色
│   ├── monkey_patches.py          # Python 3.10+兼容补丁
│   ├── simple_data_class.py       # DataClassBase
│   ├── func_timeout/              # 函数超时控制
│   │   ├── __init__.py            # func_timeout, func_set_timeout
│   │   ├── StoppableThread.py
│   │   └── exceptions.py
│   ├── dependency_packages/       # 内嵌第三方包
│   │   └── mongomq/               # MongoQueue, Job, MongoLock
│   └── dependency_packages_in_pythonpath/  # 加入PYTHONPATH的内嵌包
│       ├── readme.md
│       ├── add_to_pythonpath.py   # 将此目录加入sys.path
│       ├── aioredis/              # 内嵌aioredis异步Redis客户端
│       │   ├── readme.md
│       │   ├── client.py          # Redis, PubSub, Pipeline
│       │   ├── connection.py      # 连接管理
│       │   ├── exceptions.py      # 异常
│       │   ├── lock.py            # 分布式锁
│       │   ├── sentinel.py        # 哨兵
│       │   ├── compat.py          # 兼容层
│       │   ├── log.py             # 日志
│       │   └── utils.py           # 工具
│       └── func_timeout/          # 内嵌func_timeout (同utils/func_timeout)
├── beggar_version_implementation/  # 乞丐版实现
│   ├── README.md
│   └── beggar_redis_consumer.py   # BeggarRedisConsumer 极简Redis消费者
└── md_for_ai/                     # AI参考文档
    ├── funboost源码速查for_ai.md   # (本文档)
    ├── funboost教程速查for_ai.md
    ├── funboost_ai_coding_编程指南_rules_and_skills.md
    └── 如何扩展增加新的中间件.md
```

---
## 二、核心模块精确定位

### 2.1 `core/booster.py` — 核心装饰器

| 行号 | 定义 | 说明 |
|------|------|------|
| **38** | `class Booster` | 核心装饰器，将函数变为分布式任务。`__init__` 接收 `BoosterParams`；`__call__` 装饰消费函数 |
| **263** | `boost = Booster` | `boost` 是 `Booster` 的别名 |
| **264** | `task_deco = boost` | `task_deco` 是 `boost` 的另一别名 |
| **267** | `def gen_pid_queue_name_key()` | 生成进程+队列名的Redis key |
| **271** | `class BoosterRegistry` | 享元模式管理所有 Booster 实例，支持分组消费 |
| **514** | `booster_registry_default` | 默认 BoosterRegistry 实例 |
| **520** | `BoostersManager = booster_registry_default` | 别名 |

**Booster 装饰后函数获得的关键属性/方法:**

| 属性/方法 | 说明 |
|-----------|------|
| `.push(*args, **kwargs)` / `.delay(...)` | 发布消息(传函数参数) |
| `.publish(msg_dict, task_id=, task_options=)` / `.pub(...)` / `.apply_async(...)` | 发布消息(传字典) |
| `.aio_push(...)` / `.aio_publish(...)` | 异步发布 |
| `.consume()` / `.start_consuming_message()` | 启动消费 |
| `.multi_process_consume(process_num)` / `.mp_consume(n)` | 多进程消费 |
| `.multi_process_pub_params_list(params_list, process_num)` | 多进程批量发布 |
| `.pause()` / `.pause_consume()` | 暂停消费 |
| `.continue_consume()` | 恢复消费 |
| `.clear()` / `.clear_queue()` | 清空队列 |
| `.get_message_count()` | 获取消息数量 |
| `.fabric_deploy(host, port, user, password, ...)` | 远程部署 |

---

### 2.2 `core/func_params_model.py` — 参数模型

| 行号 | 定义 | 说明 |
|------|------|------|
| **27** | `class FunctionResultStatusPersistanceConfig` | 函数结果持久化配置 |
| **44** | `class BoosterParamsFieldsAssit` | 字段辅助类 |
| **60** | `class BoosterParams` | **核心参数模型**，50+字段，控制所有行为 |
| **334** | `class BoosterParamsComplete` | 完整参数(含运行时填充) |
| **354** | `class TaskOptions` | 单次任务选项(task_id, priority, filter_str等) |
| **409** | `class PublisherParams` | 发布者参数 |

**BoosterParams 关键字段分类:**

```
基础: queue_name, broker_kind, project_name
并发: concurrent_mode, concurrent_num, specify_concurrent_pool, specify_async_loop
控频: qps, is_using_distributed_frequency_control
重试: max_retry_times, is_using_advanced_retry, advanced_retry_config, is_push_to_dlx_queue_when_retry_max_times
超时: function_timeout, is_support_remote_kill_task
监控: is_send_consumer_heartbeat_to_redis
日志: log_level, logger_prefix, create_logger_file, logger_name, log_filename
消息: msg_expire_seconds, do_task_filtering, task_filtering_expire_seconds
RPC:  is_using_rpc_mode, rpc_result_expire_seconds, rpc_timeout
定时: delay_task_apscheduler_jobstores_kind, allow_run_time_cron
启动: schedule_tasks_on_main_thread, is_auto_start_consuming_message, booster_group
扩展: broker_exclusive_config, user_options, consumer_override_cls, publisher_override_cls
```

---

### 2.3 `constant.py` — 常量枚举

| 行号 | 定义 | 说明 |
|------|------|------|
| **5** | `class BrokerEnum` | 50种消息队列中间件枚举 |
| **201** | `class ConcurrentModeEnum` | 并发模式: THREADING/GEVENT/EVENTLET/ASYNC/SINGLE_THREAD |
| **219** | `class FunctionKind` | 函数类型标识 |
| **230** | `class ConstStrForClassMethod` | 类方法常量 |
| **238** | `class RedisKeys` | Redis key命名空间(暂停/停止/计数/心跳/unack等) |
| **302** | `class ConsumingFuncInputParamsCheckerField` | 入参检查常量 |
| **311** | `class MongoDbName` | MongoDB数据库名 |
| **315** | `class StrConst` | 字符串常量 |
| **321** | `class EnvConst` | 环境变量常量 |

**BrokerEnum 按类别:**

| 类别 | 枚举值 |
|------|--------|
| Redis系列 | `REDIS`, `REDIS_ACK_ABLE`, `REIDS_ACK_USING_TIMEOUT`, `REDIS_STREAM`, `REDIS_PRIORITY`, `REDIS_BRPOP_LPUSH`, `REDIS_PUBSUB`, `REDIS_ZSET_PRIORITY`, `REDIS_ZSET_DELAY` |
| RabbitMQ | `RABBITMQ_AMQPSTORM`(=`RABBITMQ`), `RABBITMQ_COMPLEX_ROUTING`, `RABBITMQ_AMQP`, `RABBITMQ_PIKA`, `RABBITMQ_RABBITPY` |
| Kafka | `KAFKA`, `KAFKA_CONFLUENT`(=`CONFLUENT_KAFKA`), `KAFKA_CONFLUENT_SASlPlAIN` |
| RocketMQ | `ROCKETMQ`, `ROCKETMQ5` |
| 其他MQ | `PULSAR`, `NSQ`, `MQTT`, `NATS_CORE`, `NATS_JETSTREAM`, `ZEROMQ`, `SQS`, `HTTPSQS` |
| 内存/文件 | `MEMORY_QUEUE`, `FASTEST_MEM_QUEUE`, `SQLITE_QUEUE`(=`PERSISTQUEUE`), `TXT_FILE` |
| 数据库 | `MONGOMQ`, `SQLACHEMY`, `POSTGRES`, `PEEWEE` |
| 网络协议 | `TCP`, `UDP`, `HTTP`, `GRPC`, `WEBSOCKET` |
| 框架集成 | `CELERY`, `DRAMATIQ`, `HUEY`, `RQ`, `NAMEKO`, `KOMBU` |
| 特殊 | `MYSQL_CDC`, `WATCHDOG`, `EMPTY` |
| 自定义(不在此表中) | `REDIS_ZSET`, `REDIS_HASH_UPDATE`, `CELERY_POOL` 等由 `contrib/register_custom_broker_contrib/` 或 `register_custom_broker()` 动态注册 |

---

### 2.4 `consumers/base_consumer.py` — 消费者基类

| 行号 | 定义 | 说明 |
|------|------|------|
| **95** | `class GlobalVars` | 全局变量(如全局暂停标志) |
| **101** | `class AbstractConsumer` | **消费者抽象基类**，实现20+种运行控制(QPS/重试/超时/分布式统计/DLQ/cron等) |
| **1266** | `def wait_for_possible_has_finish_all_tasks()` | 等待任务完成(AbstractConsumer方法) |
| **1299** | `class ConcurrentModeDispatcher` | 根据concurrent_mode构建并发池 |
| **1390** | `def wait_for_possible_has_finish_all_tasks_by_conusmer_list()` | 等待多个消费者的任务完成(模块级函数) |
| **1405** | `class MetricCalculation` | 速度/QPS指标计算 |
| **1497** | `class DistributedConsumerStatistics` | 分布式消费者统计(心跳、掉线检测、分布式QPS) |

**AbstractConsumer 关键方法:**

```python
start_consuming_message()          # 启动消费(非阻塞)
_submit_task(msg: dict)            # 提交任务到并发池
_run_consuming_function(kw, ...)   # 执行消费函数
pause_consume()                    # 暂停消费
continue_consume()                 # 恢复消费
clear_filter_tasks()               # 清空去重过滤器
```

---

### 2.5 `publishers/base_publisher.py` — 发布者基类

| 行号 | 定义 | 说明 |
|------|------|------|
| **43** | `class PublishMsgContext` | 发布消息上下文 |
| **51** | `class AbstractPublisher` | **发布者抽象基类**，消息序列化、参数校验、RPC结果存储 |
| **205** | `def _execute_publish()` | 执行发布，调用 `_wrapped_publish_impl` + `_post_publish_log_and_count` |
| **211** | `def _post_publish_log_and_count()` | 发布后日志/计数/统计，子类覆写 `_execute_publish` 时调用此方法避免重复代码 |
| **228** | `def _after_publish()` | 发布后钩子方法 |
| **245** | `def generate_msg_context_for_push()` | push 调用的消息上下文生成 |
| **291** | `def generate_msg_context_for_publish()` | publish 调用的消息上下文生成 |
| **341** | `def _publish_impl()` | 子类实现的实际发布逻辑 |
| **417** | `def deco_mq_conn_error()` | MQ连接错误重试装饰器 |

**AbstractPublisher 关键方法:**

```python
publish(msg, task_id=, task_options=) -> AsyncResult     # 发布消息(传字典)
push(*func_args, **func_kwargs) -> AsyncResult           # 简化发布(传函数参数)
aio_publish(msg, ...) -> AioAsyncResult                  # 异步发布
aio_push(*args, **kwargs) -> AioAsyncResult              # 异步简化发布
_execute_publish(publish_msg_context) -> AsyncResult     # publish/push 的共同执行通路
_post_publish_log_and_count(t_start, ctx)                # 发布后日志/计数(子类复用)
_publish_impl(msg: str)                                  # 子类实现的broker写入
clear()                                                  # 清空队列
get_message_count() -> int                               # 获取消息数量
```

---

### 2.6 `core/msg_result_getter.py` — RPC结果获取

| 行号 | 定义 | 说明 |
|------|------|------|
| **30** | `def _judge_rpc_function_result_status_obj()` | 判断RPC结果状态 |
| **46** | `class AsyncResult` | 同步方式获取RPC结果(基于Redis) |
| **149** | `class AioAsyncResult` | 异步方式获取RPC结果 |
| **254** | `class MongoResultGetter` | 从MongoDB获取结果 |
| **288** | `class ResultFromMongo` | 从MongoDB获取结果(别名) |
| **290** | `class FutureStatusResult` | Future状态结果 |

**AsyncResult 关键接口:**

```python
.get() -> Any                      # 阻塞获取结果
.result -> Any                     # 结果属性(阻塞)
.is_success() -> bool              # 是否成功
.is_pending() -> bool              # 是否还在执行
.status_and_result -> dict         # 状态+结果字典
.set_callback(callback_func)       # 设置回调
.wait_rpc_data_or_raise()          # 等待结果或抛异常
```

---

### 2.7 `core/current_task.py` — 当前任务上下文

| 行号 | 定义 | 说明 |
|------|------|------|
| **27** | `class FctContext` | 任务上下文数据(function_result_status, logger) |
| **40** | `def set_fct_context()` | 设置当前线程/协程上下文 |
| **45** | `def get_fct_context()` | 获取当前线程/协程上下文 |
| **50** | `class _FctProxy` | 代理类，自动获取当前线程/协程上下文 |
| **94** | `fct = _FctProxy()` | **全局实例**，在消费函数中直接使用 |
| **97** | `def funboost_current_task()` | 函数式获取当前任务(返回_FctProxy) |
| **107** | `def get_current_taskid()` | 获取当前task_id |
| **118** | `class FctContextThread` | 线程上下文 |

**fct 代理属性:**

```python
fct.task_id              # 当前任务ID
fct.queue_name           # 队列名
fct.run_times            # 运行次数(含重试)
fct.full_msg             # 完整消息体
fct.function_params      # 函数参数
fct.function_result_status  # FunctionResultStatus对象
fct.logger               # 当前任务的logger
```

---

### 2.8 `core/function_result_status_saver.py` — 函数运行状态

| 行号 | 定义 | 说明 |
|------|------|------|
| **24** | `class RunStatus` | 运行状态枚举 |
| **28** | `class FunctionResultStatus` | 函数运行结果状态(task_id, 参数, 结果, 异常, 耗时等) |
| **183** | `class ResultPersistenceHelper` | 结果持久化到MongoDB/SQL |

---

### 2.9 `core/exceptions.py` — 异常类

| 行号 | 异常类 | 说明 |
|------|--------|------|
| **9** | `FunboostException` | 基础异常 |
| **141** | `ExceptionForRetry` | 抛出此异常触发重试 |
| **145** | `ExceptionForRequeue` | 抛出此异常重新入队 |
| **148** | `FunboostWaitRpcResultTimeout` | RPC结果等待超时 |
| **151** | `FunboostRpcResultError` | RPC结果错误 |
| **154** | `HasNotAsyncResult` | 无异步结果 |
| **157** | `FunboostTaskExecutionError` | 任务执行错误 |
| **165** | `ExceptionForPushToDlxqueue` | 推送到死信队列 |
| **169** | `BoostDecoParamsIsOldVersion` | 装饰器参数旧版本警告 |
| **192** | `QueueNameNotExists` | 队列名不存在 |
| **196** | `FuncParamsError` | 函数参数错误 |

---

### 2.10 `core/serialization.py` — 序列化

| 行号 | 定义 | 说明 |
|------|------|------|
| **10** | `class Serialization` | JSON序列化(支持datetime等) |
| **51** | `class PickleHelper` | Pickle序列化辅助 |

---

### 2.11 `core/helper_funs.py` — 消息工具函数

| 行号 | 定义 | 说明 |
|------|------|------|
| **8** | `def get_publish_time()` | 获取发布时间戳 |
| **16** | `def get_publish_time_format()` | 格式化发布时间 |
| **23** | `def get_task_id()` | 生成task_id |
| **37** | `def get_func_only_params()` | 从消息中提取函数参数 |
| **47** | `def block_python_main_thread_exit()` | 阻止主线程退出 |
| **59** | `run_forever = block_python_main_thread_exit` | 别名 |
| **62** | `class MsgGenerater` | 消息生成器 |

---

### 2.12 `core/kill_remote_task.py` — 远程杀任务

| 行号 | 定义 | 说明 |
|------|------|------|
| **11** | `class ThreadKillAble` | 可杀死的线程 |
| **21** | `class TaskHasKilledError` | 任务已被杀死异常 |
| **25** | `def kill_fun_deco()` | 杀任务装饰器 |
| **54** | `def kill_thread_by_task_id()` | 根据task_id杀死线程 |
| **67** | `class RemoteTaskKillerZset` | 基于Redis ZSet的远程杀任务 |
| **111** | `class RemoteTaskKiller` | 远程任务杀手(对外使用) |

---

### 2.13 `core/consuming_func_input_params_check.py` — 入参校验

| 行号 | 定义 | 说明 |
|------|------|------|
| **10** | `class ConsumingFuncInputParamsChecker` | 消费函数入参检查器 |
| **117** | `class FakeFunGenerator` | 生成假函数(用于FaaS) |

---

### 2.14 `core/active_cousumer_info_getter.py` — 活跃消费者信息

| 行号 | 定义 | 说明 |
|------|------|------|
| **44** | `class CareProjectNameEnv` | 项目名环境变量管理 |
| **172** | `class ActiveCousumerProcessInfoGetter` | 获取活跃消费者进程信息 |
| **275** | `class QueuesConusmerParamsGetter` | 获取所有队列的消费者参数 |
| **399** | `class SingleQueueConusmerParamsGetter` | 获取单个队列的消费者参数、生成FaaS publisher/booster |

---

### 2.15 `core/loggers.py` — 日志

| 行号 | 定义 | 说明 |
|------|------|------|
| **11** | `def get_funboost_file_logger()` | 获取文件logger |
| **18** | `class FunboostFileLoggerMixin` | 文件日志Mixin |
| **33** | `class FunboostMetaTypeFileLogger` | 元类型文件日志 |
| **45** | `flogger` | 全局logger实例 |

---

### 2.16 `core/funboost_time.py` — 时间处理

| 行号 | 定义 | 说明 |
|------|------|------|
| **12** | `class FunboostTime(NbTime)` | 继承NbTime, 优先读取FunboostCommonConfig.TIMEZONE |
| **32** | `def fast_get_now_time_str()` | 快速获取当前时间字符串(百万次0.4秒) |

---

### 2.17 `core/muliti_process_enhance.py` — 多进程增强

| 行号 | 定义 | 说明 |
|------|------|------|
| **21** | `def run_consumer_with_multi_process()` | 多进程消费 |
| **59** | `def multi_process_pub_params_list()` | 多进程批量发布 |

---

### 2.18 `core/fabric_deploy_helper.py` — 远程部署

| 行号 | 定义 | 说明 |
|------|------|------|
| **17** | `def fabric_deploy()` | Fabric远程部署+启动消费 |

---

### 2.19 `core/broker_kind__exclusive_config_default_define.py` — broker专属配置

| 行号 | 定义 | 说明 |
|------|------|------|
| **11** | `broker_kind__exclusive_config_default_map` | broker专属配置默认值映射 |
| **14** | `def register_broker_exclusive_config_default()` | 注册broker的专属默认配置 |
| **21** | `def generate_broker_exclusive_config()` | 生成merged配置 |

每种broker有独立的默认dict (Celery task opts, Dramatiq actor opts, gRPC host/port, Kafka group等)

---

### 2.20 `core/pydantic_compatible_base.py` — Pydantic兼容

| 行号 | 定义 | 说明 |
|------|------|------|
| **35** | `def get_pydantic_major_version()` | 获取Pydantic主版本号 |
| **78** | `def compatible_root_validator()` | Pydantic v1/v2兼容的root_validator |
| **162** | `class BaseJsonAbleModel` | Pydantic v1/v2 兼容基类，所有参数模型的基类 |
| **227** | `def get_cant_json_serializable_fields()` | 获取不可JSON序列化的字段 |

---

## 三、工厂模块精确定位

### 3.1 `factories/broker_kind__publsiher_consumer_type_map.py`

| 行号 | 定义 | 说明 |
|------|------|------|
| **58** | `broker_kind__publsiher_consumer_type_map = {...}` | broker枚举 → (Publisher类, Consumer类) 映射表 |
| **91** | `def register_custom_broker()` | 注册自定义broker |
| **107** | `def regist_to_funboost()` | 懒注册(避免可选依赖import失败) |

### 3.2 `factories/consumer_factory.py`

| 行号 | 定义 | 说明 |
|------|------|------|
| **13** | `def get_consumer()` | 消费者工厂，支持consumer_override_cls合并MRO |
| **36** | `class ConsumerCacheProxy` | 消费者缓存代理(进程级单例) |

### 3.3 `factories/publisher_factory.py`

| 行号 | 定义 | 说明 |
|------|------|------|
| **15** | `def get_publisher()` | 发布者工厂，支持publisher_override_cls合并MRO |
| **47** | `class PublisherCacheProxy` | 发布者缓存代理(进程级单例) |

---

## 四、并发池精确定位

### 4.1 `concurrent_pool/pool_commons.py`

| 行号 | 定义 | 说明 |
|------|------|------|
| **10** | `class ConcurrentPoolBuilder` | 根据ConcurrentModeEnum构建并发池 |

### 4.2 `concurrent_pool/flexible_thread_pool.py`

| 行号 | 定义 | 说明 |
|------|------|------|
| **35** | `def run_sync_or_async_fun()` | 同步/异步函数自适应执行 |
| **43** | `def sync_or_async_fun_deco()` | 同步/异步函数自适应执行装饰器 |
| **78** | `class FlexibleThreadPool` | 弹性线程池(自适应伸缩, 空闲10秒退出, 性能高200%) |
| **180** | `class FlexibleThreadPoolMinWorkers0` | 最小线程数为0的变体 |
| **191** | `class FlexibleThreadPoolMinWorkers1` | 最小线程数为1的变体 |

### 4.3 `concurrent_pool/async_pool_executor.py`

| 行号 | 定义 | 说明 |
|------|------|------|
| **57** | `class AsyncPoolExecutor` | asyncio协程池 |

### 4.4 `concurrent_pool/custom_threadpool_executor.py`

| 行号 | 定义 | 说明 |
|------|------|------|
| **96** | `class ThreadPoolExecutorShrinkAble` | 可收缩线程池(空闲线程自动退出) |
| **163** | `CustomThreadpoolExecutor = CustomThreadPoolExecutor = ThreadPoolExecutorShrinkAble` | 别名 |
| **166** | `class ThreadPoolExecutorShrinkAbleNonDaemon` | 非守护线程版本 |
| **233** | `def show_current_threads_num()` | 显示当前线程数 |

### 4.5 并发模式 → 并发池对照表

| ConcurrentModeEnum | 池类 | 文件 |
|--------------------|------|------|
| `THREADING` | `FlexibleThreadPool` | `flexible_thread_pool.py` |
| `GEVENT` | `GeventPoolExecutor` | `custom_gevent_pool_executor.py` |
| `EVENTLET` | `EventletPoolExecutor` | `custom_evenlet_pool_executor.py` |
| `ASYNC` | `AsyncPoolExecutor` | `async_pool_executor.py` |
| `SINGLE_THREAD` | `SoloExecutor` | `single_thread_executor.py` |

---

## 五、定时任务精确定位

### 5.1 `timing_job/timing_job_base.py`

| 行号 | 定义 | 说明 |
|------|------|------|
| **29** | `def timing_publish_deco()` | 定时发布装饰器 |
| **42** | `def push_fun_params_to_broker()` | 推送函数参数到broker |
| **57** | `class ThreadPoolExecutorForAps` | APScheduler用的线程池 |
| **84** | `class FunboostBackgroundScheduler` | 全局后台调度器 |
| **198** | `class FsdfBackgroundScheduler` | 别名 |
| **206** | `funboost_aps_scheduler` | 全局实例 |

### 5.2 `timing_job/timing_push.py`

| 行号 | 定义 | 说明 |
|------|------|------|
| **11** | `class ApsJobAdder` | 定时任务添加器，支持 `date`/`interval`/`cron` 三种触发器 |

---

## 六、FaaS 微服务精确定位

### 6.1 `faas/fastapi_adapter.py`

| 行号 | 定义 | 说明 |
|------|------|------|
| **58** | `fastapi_router = APIRouter(prefix='/funboost')` | FastAPI路由器 |
| **356** | `async def publish_msg()` | 发布消息(支持RPC) |
| **412** | `async def get_result()` | 根据task_id获取结果 |
| **467** | `def pause_consume()` | 暂停消费接口 |
| **509** | `def resume_consume()` | 恢复消费接口 |
| **552** | `def get_msg_count()` | 获取消息数量接口 |
| **581** | `def clear_queue()` | 清空队列接口 |
| **628** | `def get_all_queues()` | 获取所有队列接口 |
| **1057** | `def add_timing_job()` | 添加定时任务接口 |
| **1148** | `def get_timing_jobs()` | 获取定时任务列表 |
| **1234** | `def get_timing_job()` | 获取单个定时任务 |
| **1288** | `def delete_timing_job()` | 删除定时任务 |

### 6.2 `faas/flask_adapter.py`

| 行号 | 定义 | 说明 |
|------|------|------|
| **30** | `flask_blueprint = Blueprint(...)` | Flask蓝图 |
| **33** | `def publish_msg()` | 发布消息接口 |
| **132** | `def get_result()` | 获取结果接口 |

---

## 七、工作流精确定位

### 7.1 `workflow/signature.py`

| 行号 | 定义 | 说明 |
|------|------|------|
| **19** | `def _update_workflow_context_after_task()` | 任务后更新工作流上下文 |
| **37** | `class Signature` | 任务签名(类似Celery signature) |
| **160** | `def signature()` | 创建签名的工厂函数 |

### 7.2 `workflow/primitives.py`

| 行号 | 定义 | 说明 |
|------|------|------|
| **45** | `class Chain` | 链式编排(串行) |
| **143** | `class Group` | 分组编排(并行) |
| **253** | `class Chord` | 和弦编排(并行+回调) |
| **320** | `def chain()` | 工厂函数 |
| **333** | `def group()` | 工厂函数 |
| **349** | `def chord()` | 工厂函数 |

### 7.3 `workflow/workflow_mixin.py`

| 行号 | 定义 | 说明 |
|------|------|------|
| **28** | `class WorkflowPublisherMixin` | 发布者工作流Mixin，覆写 `_execute_publish` 注入工作流上下文 |
| **115** | `class WorkflowConsumerMixin` | 消费者工作流Mixin |
| **183** | `def get_current_workflow_context()` | 获取当前工作流上下文 |

### 7.4 `workflow/params.py`

| 行号 | 定义 | 说明 |
|------|------|------|
| **25** | `class WorkflowBoosterParams` | 工作流版Booster参数 |

---

## 八、Contrib 扩展模块精确定位

### 8.1 Override Mixin 扩展 (`contrib/override_publisher_consumer_cls/`)

| 文件 | 核心类 | 功能 |
|------|--------|------|
| `circuit_breaker_mixin.py` | `CircuitBreakerConsumerMixin` | 熔断器(失败率达阈值自动熔断) |
| `funboost_micro_batch_mixin.py` | `MicroBatchConsumerMixin`, `MicroBatchBoosterParams` | 微批消费(凑批或超时触发) |
| `funboost_promethus_mixin.py` | `PrometheusConsumerMixin` | Prometheus指标采集 |
| `funboost_otel_mixin.py` | `AutoOtelPublisherMixin`, `AutoOtelConsumerMixin`, `OtelBoosterParams` | OpenTelemetry链路追踪 |
| `otel_tree_span_exporter.py` | `TreeSpanExporter` | OTel树形Span导出 |
| `periodic_quota_mixin.py` | `PeriodicQuotaConsumerMixin` | 周期额度限制 |
| `alert_notifier_mixin.py` | `AlertNotifierConsumerMixin` | 异常告警通知 |

### 8.2 自定义 Broker (`contrib/register_custom_broker_contrib/`)

| 文件 | 核心类 | 功能 |
|------|--------|------|
| `watchdog_broker.py` | `WatchdogPublisher`, `WatchdogConsumer`, `FunboostEventHandler` | 文件系统监控 |
| `websocket_broker.py` | `WebSocketPublisher`, `WebSocketConsumer`, `start_simple_ws_server` | WebSocket |
| `nats_core_broker.py` | `NatsPublisher`, `NatsConsumer` | NATS Core 无持久化 |
| `nats_jetstream_broker.py` | `NatsJetStreamPublisher`, `NatsJetStreamConsumer` | NATS JetStream 持久化 |
| `redis_zset_broker.py` | `RedisZSetPublisher`, `RedisZSetConsumer` | Redis ZSet 可更新覆盖(latest-wins) |
| `redis_hash_update_broker.py` | `RedisHashUpdatePublisher`, `RedisHashUpdateConsumer` | Redis HASH 可更新覆盖消息(latest-wins语义) |
| `celery_pool_as_funboost_broker.py` | `CeleryPoolPublisher`, `CeleryPoolConsumer` | 复用 CeleryPool 作为 funboost broker |

### 8.3 funspider 爬虫辅助扩展 (`contrib/funspider/`)

> 基于 httpx + SQLModel 的爬虫辅助组件，提供 ORM 模型与同步/异步双引擎客户端。
> 导入路径: `from funboost.contrib.funspider import SimpleSpiderClient, AsyncSpiderClient, SpiderItem, Field, create_engine, create_async_engine`

| 文件 | 核心类 | 功能 |
|------|--------|------|
| `http.py` | `SpiderResponse` | 统一封装 httpx 响应，内置 `.xpath()`/`.css()`/`.re()`/`.resp_dict` |
| `http.py` | `SimpleSpiderClient` | 同步爬虫客户端(httpx.Client)，支持重试+代理函数列表+随机UA |
| `http.py` | `AsyncSpiderClient` | 异步爬虫客户端(httpx.AsyncClient)，同上 |
| `item.py` | `SpiderItem` | SQLModel ORM 基类，`.insert()`/`.upsert()`/`.aio_insert()`/`.aio_upsert()` |

### 8.4 其他 Contrib

| 文件 | 功能 |
|------|------|
| `contrib/queue2queue.py` | `consume_and_push_to_another_queue`, `multi_prcocess_queue2queue` |
| `contrib/django_db_deco.py` | `close_old_connections_deco` Django连接管理 |
| `contrib/redis_consume_latest_msg_broker.py` | `RedisConsumeLatestPublisher/Consumer` 只消费最新消息 |
| `contrib/cdc/mysql2mysql.py` | `MySql2Mysql` MySQL CDC数据同步 |
| `contrib/cdc/mysql_cdc_binlog_listener.py` | `MySqlCdcBinlogListener` MySQL binlog 监听器 |

---

## 九、工具模块精确定位

### 9.1 `utils/redis_manager.py`

| 行号 | 定义 | 说明 |
|------|------|------|
| **56** | `class RedisManager` | Redis连接管理器(连接池) |
| **98** | `class RedisMixin` | Redis Mixin(提供self.redis_db_frame) |
| **123** | `class AioRedisMixin` | 异步Redis Mixin |

### 9.2 `utils/mongo_util.py`

| 行号 | 定义 | 说明 |
|------|------|------|
| **20** | `class MongoMixin` | MongoDB Mixin(提供self.mongo_client) |

### 9.3 `utils/decorators.py` — 装饰器工具箱

| 行号 | 定义 | 说明 |
|------|------|------|
| **41** | `def run_many_times()` | 运行多次 |
| **60** | `def handle_exception()` | 异常处理装饰器 |
| **102** | `def keep_circulating()` | **保持循环执行**(consumer消息循环的基础) |
| **139** | `def synchronized()` | 线程同步装饰器 |
| **151** | `def singleton()` | 单例装饰器(加锁) |
| **237** | `def flyweight()` | 享元装饰器 |
| **315** | `def timer()` | 计时装饰器 |
| **357** | `class RedisDistributedLockContextManager` | Redis分布式锁 |

### 9.4 其他工具文件

| 文件 | 核心 | 说明 |
|------|------|------|
| `utils/ctrl_c_end.py` | `ctrl_c_recv()` | 阻塞主线程，Ctrl+C优雅退出 |
| `utils/block_exit.py` | — | 阻止进程退出 |
| `utils/paramiko_util.py` | `ParamikoFolderUploader` | SSH文件夹上传 |
| `utils/bulk_operation.py` | — | 批量Mongo/ES/Redis写入 |
| `utils/expire_lock.py` | — | 过期锁上下文管理器 |
| `utils/notify_util.py` | `Notifier` | 通知工具 |
| `utils/resource_monitoring.py` | `ResourceMonitor` | 资源监控 |
| `utils/task_dispatcher.py` | `LocalFunctionsDispatcher` | 本地函数分发器 |
| `utils/func_timeout/` | `func_timeout`, `func_set_timeout`, `StoppableThread` | 函数超时控制 |

---

## 十、队列实现精确定位

| 文件 | 行号 | 类 | 说明 |
|------|------|-----|------|
| `queues/memory_queues_map.py` | **4** | `PythonQueues` | Python queue.Queue 映射 |
| `queues/fastest_mem_queue.py` | **22** | `FastestMemQueue` | collections.deque 队列 |
| `queues/fastest_mem_queue.py` | **134** | `FastestMemQueues` | FastestMemQueue 映射 |
| `queues/sqla_queue.py` | **27** | `TaskStatus` | 任务状态枚举 |
| `queues/sqla_queue.py` | **78** | `SqlaQueue` | SQLAlchemy 队列 |
| `queues/peewee_queue.py` | **22** | `PeeweeQueue` | Peewee ORM 队列 |
| `queues/postgres_queue.py` | **34** | `PostgresQueue` | PostgreSQL队列(SKIP LOCKED+NOTIFY) |

---

## 十一、配置模块精确定位

### 11.1 `funboost_config_deafult.py` (注意文件名拼写)

| 行号 | 定义 | 说明 |
|------|------|------|
| **22** | `class BrokerConnConfig` | 所有中间件连接配置(Redis/Mongo/RabbitMQ/Kafka/RocketMQ/MQTT等URL) |
| **115** | `class FunboostCommonConfig` | 通用配置(日志格式/时区/日志级别等) |

### 11.2 `set_frame_config.py`

| 行号 | 定义 | 说明 |
|------|------|------|
| **83** | `def show_frame_config()` | 显示当前配置 |
| **109** | `def use_config_form_funboost_config_module()` | 加载用户funboost_config.py合并到默认配置 |
| **155** | `def _auto_creat_config_file_to_project_root_path()` | 自动创建配置文件模板 |

---

## 十二、CLI 命令行精确定位

### 12.1 `core/cli/funboost_fire.py`

| 行号 | 定义 | 说明 |
|------|------|------|
| **15** | `class BoosterFire` | Fire CLI命令集(discover/consume/publish/clear/pause等) |

### 12.2 `core/cli/discovery_boosters.py`

| 行号 | 定义 | 说明 |
|------|------|------|
| **64** | `class BoosterDiscovery` | 自动发现项目中的@boost消费函数 |

### 12.3 `__main__.py`

```python
fire.Fire(BoosterFire)    # 入口: python -m funboost --project_root_path=...
```

---

## 十三、Web管理界面精确定位

### 13.1 `funweb/app.py`

```
Flask app 主体
start_funboost_web_manager()   # 启动Web管理界面
路由: login, Mongo任务视图, 速度图表
```

### 13.2 `funweb/flask_bps/`

| 文件 | 功能 |
|------|------|
| `system_monitor.py` | Redis心跳采集, 系统监控API |
| `script_deploy.py` | 脚本部署CRUD, Git操作, 进程控制, 日志tail |
| `log_viewer.py` | 日志查看器(文件夹白名单, tail, grep, stream) |
| `queue_alerts.py` | 队列告警系统: 5种告警类型(积压/QPS骤降/消费者掉线/失败率飙升/耗时过高)，多通道通知(钉钉/企微/飞书/Webhook)，告警去抖，后台10秒轮询检查 |
| `web_helper.py` | IP/hostname辅助函数 |

---

## 十四、assist 第三方框架辅助

| 文件 | 核心类 | 说明 |
|------|--------|------|
| `assist/celery_helper.py` | `CeleryHelper` | CeleryHelper (realy_start_celery_worker 现在在非守护线程中启动 worker) |
| `assist/dramatiq_helper.py` | `DramatiqHelper` | Dramatiq集成辅助 |
| `assist/huey_helper.py` | `HueyHelper` | Huey集成辅助 |
| `assist/rq_helper.py` | `RqHelper`, `RandomWindowsWorker` | RQ集成辅助 |
| `assist/faststream_helper.py` | `get_broker()`, `app` | FastStream集成 |
| `assist/celery_pool.py` | `CeleryPool`, `CeleryFuture` | 将 Celery 封装为 concurrent.futures.Executor 兼容接口 |
| `assist/grpc_helper/` | proto + pb2 + servicer | gRPC服务定义和示例 |

---

## 十五、Broker Consumer/Publisher 完整映射表

| BrokerEnum | Consumer类 | Consumer文件 | Publisher类 | Publisher文件 |
|------------|-----------|--------------|-------------|---------------|
| `MEMORY_QUEUE` | `LocalPythonQueueConsumer` | `consumers/local_python_queue_consumer.py` | `LocalPythonQueuePublisher` | `publishers/local_python_queue_publisher.py` |
| `FASTEST_MEM_QUEUE` | `FastestMemQueueConsumer` | `consumers/fastest_mem_queue_consumer.py` | `FastestMemQueuePublisher` | `publishers/fastest_mem_queue_publisher.py` |
| `REDIS` | `RedisConsumer` | `consumers/redis_consumer.py` | `RedisPublisher` | `publishers/redis_publisher.py` |
| `REDIS_ACK_ABLE` | `RedisConsumerAckAble` | `consumers/redis_consumer_ack_able.py` | `RedisPublisher` | `publishers/redis_publisher.py` |
| `REIDS_ACK_USING_TIMEOUT` | `RedisConsumerAckUsingTimeout` | `consumers/redis_consumer_ack_using_timeout.py` | `RedisPublisher` | `publishers/redis_publisher.py` |
| `REDIS_STREAM` | `RedisStreamConsumer` | `consumers/redis_stream_consumer.py` | `RedisStreamPublisher` | `publishers/redis_stream_publisher.py` |
| `REDIS_PRIORITY` | `RedisPriorityConsumer` | `consumers/redis_consumer_priority.py` | `RedisPriorityPublisher` | `publishers/redis_publisher_priority.py` |
| `REDIS_BRPOP_LPUSH` | `RedisBrpopLpushConsumer` | `consumers/redis_brpoplpush_consumer.py` | `RedisPublisherLpush` | `publishers/redis_publisher_lpush.py` |
| `REDIS_PUBSUB` | `RedisPbSubConsumer` | `consumers/redis_pubsub_consumer.py` | `RedisPubSubPublisher` | `publishers/redis_pubsub_publisher.py` |
| `REDIS_ZSET_PRIORITY` / `REDIS_ZSET_DELAY` | `RedisZSetConsumer` | `contrib/register_custom_broker_contrib/redis_zset_broker.py` | `RedisZSetPublisher` | 同文件 |
| `RABBITMQ`(= `RABBITMQ_AMQPSTORM`) | `RabbitmqConsumerAmqpStorm` | `consumers/rabbitmq_amqpstorm_consumer.py` | `RabbitmqPublisherUsingAmqpStorm` | `publishers/rabbitmq_amqpstorm_publisher.py` |
| `RABBITMQ_COMPLEX_ROUTING` | `RabbitmqComplexRoutingConsumer` | `consumers/rabbitmq_complex_routing_consumer.py` | `RabbitmqComplexRoutingPublisher` | `publishers/rabbitmq_complex_routing_publisher.py` |
| `RABBITMQ_AMQP` | `RabbitmqAmqpConsumer` | `consumers/rabbitmq_amqp_consumer.py` | `RabbitmqAmqpPublisher` | `publishers/rabbitmq_amqp_publisher.py` |
| `RABBITMQ_PIKA` | `RabbitmqConsumer` | `consumers/rabbitmq_pika_consumer.py` | `RabbitmqPublisher` | `publishers/rabbitmq_pika_publisher.py` |
| `RABBITMQ_RABBITPY` | `RabbitmqConsumerRabbitpy` | `consumers/rabbitmq_rabbitpy_consumer.py` | `RabbitmqPublisherUsingRabbitpy` | `publishers/rabbitmq_rabbitpy_publisher.py` |
| `KAFKA` | `KafkaConsumer` | `consumers/kafka_consumer.py` | `KafkaPublisher` | `publishers/kafka_publisher.py` |
| `KAFKA_CONFLUENT` | `KafkaConsumerManuallyCommit` | `consumers/kafka_consumer_manually_commit.py` | `ConfluentKafkaPublisher` | `publishers/confluent_kafka_publisher.py` |
| `KAFKA_CONFLUENT_SASlPlAIN` | `SaslPlainKafkaConsumer` | `consumers/kafka_consumer_manually_commit.py` | `SaslPlainKafkaPublisher` | `publishers/confluent_kafka_publisher.py` |
| `ROCKETMQ` | `RocketmqConsumer` | `consumers/rocketmq_consumer.py` | `RocketmqPublisher` | `publishers/rocketmq_publisher.py` |
| `ROCKETMQ5` | `Rocketmq5Consumer` | `consumers/rocketmq5_consumer.py` | `Rocketmq5Publisher` | `publishers/rocketmq5_publisher.py` |
| `PULSAR` | `PulsarConsumer` | `consumers/pulsar_consumer.py` | `PulsarPublisher` | `publishers/pulsar_publisher.py` |
| `NSQ` | `NsqConsumer` | `consumers/nsq_consumer.py` | `NsqPublisher` | `publishers/nsq_publisher.py` |
| `MQTT` | `MqttConsumer` | `consumers/mqtt_consumer.py` | `MqttPublisher` | `publishers/mqtt_publisher.py` |
| `NATS_CORE` | `NatsConsumer` | `contrib/register_custom_broker_contrib/nats_core_broker.py` | `NatsPublisher` | 同文件 |
| `NATS_JETSTREAM` | `NatsJetStreamConsumer` | `contrib/register_custom_broker_contrib/nats_jetstream_broker.py` | `NatsJetStreamPublisher` | 同文件 |
| `ZEROMQ` | `ZeroMqConsumer` | `consumers/zeromq_consumer.py` | `ZeroMqPublisher` | `publishers/zeromq_publisher.py` |
| `SQLITE_QUEUE` | `PersistQueueConsumer` | `consumers/persist_queue_consumer.py` | `PersistQueuePublisher` | `publishers/persist_queue_publisher.py` |
| `MONGOMQ` | `MongoMqConsumer` | `consumers/mongomq_consumer.py` | `MongoMqPublisher` | `publishers/mongomq_publisher.py` |
| `SQLACHEMY` | `SqlachemyConsumer` | `consumers/sqlachemy_consumer.py` | `SqlachemyQueuePublisher` | `publishers/sqla_queue_publisher.py` |
| `POSTGRES` | `PostgresConsumer` | `consumers/postgres_consumer.py` | `PostgresPublisher` | `publishers/postgres_publisher.py` |
| `PEEWEE` | `PeeweeConsumer` | `consumers/peewee_consumer.py` | `PeeweePublisher` | `publishers/peewee_publisher.py` |
| `TXT_FILE` | `TxtFileConsumer` | `consumers/txt_file_consumer.py` | `TxtFilePublisher` | `publishers/txt_file_publisher.py` |
| `TCP` | `TCPConsumer` | `consumers/tcp_consumer.py` | `TCPPublisher` | `publishers/tcp_publisher.py` |
| `UDP` | `UDPConsumer` | `consumers/udp_consumer.py` | `UDPPublisher` | `publishers/udp_publisher.py` |
| `HTTP` | `HTTPConsumer` | `consumers/http_consumer.py` | `HTTPPublisher` | `publishers/http_publisher.py` |
| `GRPC` | `GrpcConsumer` | `consumers/grpc_consumer.py` | `GrpcPublisher` | `publishers/grpc_publisher.py` |
| `SQS` | `SqsConsumer` | `consumers/sqs_consumer.py` | `SqsPublisher` | `publishers/sqs_publisher.py` |
| `HTTPSQS` | `HttpsqsConsumer` | `consumers/httpsqs_consumer.py` | `HttpsqsPublisher` | `publishers/httpsqs_publisher.py` |
| `CELERY` | `CeleryConsumer` | `consumers/celery_consumer.py` | `CeleryPublisher` | `publishers/celery_publisher.py` |
| `DRAMATIQ` | `DramatiqConsumer` | `consumers/dramatiq_consumer.py` | `DramatiqPublisher` | `publishers/dramatiq_publisher.py` |
| `HUEY` | `HueyConsumer` | `consumers/huey_consumer.py` | `HueyPublisher` | `publishers/huey_publisher.py` |
| `RQ` | `RqConsumer` | `consumers/rq_consumer.py` | `RqPublisher` | `publishers/rq_publisher.py` |
| `NAMEKO` | `NamekoConsumer` | `consumers/nameko_consumer.py` | `NamekoPublisher` | `publishers/nameko_publisher.py` |
| `KOMBU` | `KombuConsumer` | `consumers/kombu_consumer.py` | `KombuPublisher` | `publishers/kombu_publisher.py` |
| `MYSQL_CDC` | `MysqlCdcConsumer` | `consumers/mysql_cdc_consumer.py` | `MysqlCdcPublisher` | `publishers/mysql_cdc_publisher.py` |
| `WATCHDOG` | `WatchdogConsumer` | `contrib/register_custom_broker_contrib/watchdog_broker.py` | `WatchdogPublisher` | 同文件 |
| `WEBSOCKET` | `WebSocketConsumer` | `contrib/register_custom_broker_contrib/websocket_broker.py` | `WebSocketPublisher` | 同文件 |
| `REDIS_HASH_UPDATE` | `RedisHashUpdateConsumer` | `contrib/register_custom_broker_contrib/redis_hash_update_broker.py` | `RedisHashUpdatePublisher` | 同文件 |
| `CELERY_POOL` | `CeleryPoolConsumer` | `contrib/register_custom_broker_contrib/celery_pool_as_funboost_broker.py` | `CeleryPoolPublisher` | 同文件 |
| `EMPTY` | `EmptyConsumer` | `consumers/empty_consumer.py` | `EmptyPublisher` | `publishers/empty_publisher.py` |

---

## 十六、`__init__.py` 公共API导出清单

| 行号 | 导出名 | 来源模块 |
|------|--------|----------|
| **16** | `__version__` | — |
| **24** | `get_logger`, `get_funboost_file_logger`, `FunboostFileLoggerMixin`, `FunboostMetaTypeFileLogger`, `flogger` | `core.loggers` |
| **25** | `BoosterParams`, `BoosterParamsComplete`, `FunctionResultStatusPersistanceConfig`, `TaskOptions`, `PublisherParams` | `core.func_params_model` |
| **27** | `FunboostCommonConfig`, `BrokerConnConfig` | `funboost_config_deafult` |
| **30** | `wait_for_possible_has_finish_all_tasks_by_conusmer_list`, `FunctionResultStatus`, `AbstractConsumer` | `consumers.base_consumer`, `core.function_result_status_saver` |
| **33** | `ExceptionForRetry`, `ExceptionForRequeue`, `ExceptionForPushToDlxqueue` | `core.exceptions` |
| **34** | `ActiveCousumerProcessInfoGetter` | `core.active_cousumer_info_getter` |
| **35** | `HasNotAsyncResult`, `ResultFromMongo` | `core.msg_result_getter` |
| **36** | `TaskOptions`, `AbstractPublisher`, `AsyncResult`, `AioAsyncResult` | `publishers.base_publisher` (实现见 `core/msg_result_getter.py`) |
| **39** | `register_custom_broker` | `factories.broker_kind__publsiher_consumer_type_map` |
| **40** | `register_broker_exclusive_config_default` | `core.broker_kind__exclusive_config_default_define` |
| **41** | `get_publisher`, `get_consumer` | `factories` |
| **44** | `funboost_aps_scheduler`, `ApsJobAdder` | `timing_job` |
| **47** | `BrokerEnum`, `ConcurrentModeEnum` | `constant` |
| **49** | `boost`, `Booster`, `BoostersManager` | `core.booster` |
| **51** | `RemoteTaskKiller` | `core.kill_remote_task` |
| **52** | `BrokerConnConfig`, `FunboostCommonConfig` | `funboost_config_deafult` |
| **53** | `BoosterDiscovery` | `core.cli.discovery_boosters` |
| **56** | `run_forever` | `core.helper_funs` (= `block_python_main_thread_exit`) |
| **58** | `ctrl_c_recv` | `utils.ctrl_c_end` |
| **59** | `RedisMixin` | `utils.redis_manager` |
| **60** | `show_current_threads_num` | `concurrent_pool.custom_threadpool_executor` |
| **62** | `funboost_current_task`, `fct`, `get_current_taskid` | `core.current_task` |
| **64** | `MemoryFunboostPool`, `FunboostPool`, `FunboostPoolPickleFunc` | `core.funboost_pool` |

---

## 十七、架构设计要点

### 17.1 核心运行流程

```
用户定义函数 → @boost(BoosterParams) 装饰
  → Booster.__init__: 解析参数
  → Booster.__call__: 绑定消费函数

发布: booster.push(*args) 
  → get_publisher() 工厂创建 Publisher
  → AbstractPublisher.push() → generate_msg_context_for_push() → _execute_publish()
  → _wrapped_publish_impl() → _publish_impl()
  → _post_publish_log_and_count() → 返回 AsyncResult
  注意: push() 不再经过 publish()，两者共享 _execute_publish() 通路

消费: booster.consume()
  → get_consumer() 工厂创建 Consumer
  → AbstractConsumer.start_consuming_message()
  → ConcurrentModeDispatcher 构建并发池
  → 循环: 从broker取消息 → _submit_task() → 并发池执行消费函数
```

### 17.2 Broker注册机制

```
1. BrokerEnum (constant.py) 定义枚举值
2. broker_kind__publsiher_consumer_type_map (factories/) 维护 枚举→(Publisher, Consumer) 映射
3. regist_to_funboost() 懒注册可选依赖的broker
4. register_custom_broker() 用户注册自定义broker
5. get_publisher/get_consumer 工厂根据映射表实例化
```

### 17.3 Consumer/Publisher Override 机制

```
BoosterParams.consumer_override_cls = MyMixin
→ get_consumer() 中动态创建 type('MergedConsumer', (MyMixin, OriginalConsumer), {})
→ MyMixin 的方法优先级高于 OriginalConsumer
→ 所有contrib mixin都通过此机制工作
```

### 17.4 文件名拼写注意

以下文件名有拼写特殊之处（部分已在代码库中修复，`__pycache__` 中仍保留旧名），搜索时需注意：

| 当前实际文件名 | 拼写说明 | 位置 |
|-----------|---------|------|
| `funboost_config_deafult.py` | `deafult` 应为 `default` | `funboost/` |
| `broker_kind__publsiher_consumer_type_map.py` | `publsiher` 应为 `publisher` | `funboost/factories/` |
| `active_cousumer_info_getter.py` | `cousumer` 应为 `consumer` | `funboost/core/` |
| `muliti_process_enhance.py` | `muliti` 应为 `multi` | `funboost/core/` |
| ~~`publisher_factotry.py`~~ **已修复** | 现为 `publisher_factory.py` | `funboost/factories/` |
| ~~`peewee_conusmer.py`~~ **已修复** | 现为 `peewee_consumer.py` | `funboost/consumers/` |
| ~~`consuming_func_iniput_params_check.py`~~ **已修复** | 现为 `consuming_func_input_params_check.py` | `funboost/core/` |
| ~~`meomory_deque_publisher.py`~~ **已修复** | 现为 `memory_deque_publisher.py` | `funboost/publishers/` |

---

## 十八、用户自然语言问题 → 源码路由表

> AI 收到用户提问时，先在此表中匹配关键词/意图，即可直接跳转到对应源码。

### 18.1 基础使用类

| 用户可能怎么问 | 关键词 | 去看哪里 |
|---------------|--------|---------|
| 怎么用funboost / 怎么装饰函数 / 怎么创建任务 | boost, 装饰器, 装饰 | `core/booster.py` L38 `Booster` |
| 怎么发消息 / 怎么发布任务 / push怎么用 | push, publish, 发布, 发消息 | `publishers/base_publisher.py` L51 `AbstractPublisher.push/publish` |
| 怎么消费 / 怎么启动消费者 / consume怎么用 | consume, 消费, 启动 | `consumers/base_consumer.py` L101 `AbstractConsumer.start_consuming_message` |
| 有哪些参数可以配 / BoosterParams有什么字段 | 参数, 配置, BoosterParams | `core/func_params_model.py` L60 `BoosterParams` |
| 有哪些中间件/broker可以用 | broker, 中间件, 消息队列 | `constant.py` L5 `BrokerEnum` |
| 怎么切换并发模式 / 线程还是协程 | 并发, 线程, 协程, gevent, asyncio | `constant.py` L201 `ConcurrentModeEnum` + `concurrent_pool/pool_commons.py` L10 |

### 18.2 控制与调优类

| 用户可能怎么问 | 关键词 | 去看哪里 |
|---------------|--------|---------|
| 怎么限制消费速度 / 怎么限流 / QPS怎么设 | QPS, 限速, 限流, 速率 | `BoosterParams.qps` + `consumers/base_consumer.py` 内部QPS控制逻辑 |
| 分布式怎么控频 / 多机器怎么统一限速 | 分布式, 控频, 多机器 | `BoosterParams.is_using_distributed_frequency_control` + `base_consumer.py` L1497 `DistributedConsumerStatistics` |
| 失败了怎么重试 / 重试几次 / 指数退避 | 重试, retry, 退避 | `BoosterParams.max_retry_times` / `is_using_advanced_retry` / `advanced_retry_config` |
| 怎么手动触发重试 | ExceptionForRetry | `core/exceptions.py` L141 `ExceptionForRetry` |
| 消息失败了放到死信队列 | 死信, DLQ, dlx | `BoosterParams.is_push_to_dlx_queue_when_retry_max_times` + `core/exceptions.py` L165 `ExceptionForPushToDlxqueue` |
| 函数执行超时怎么办 | 超时, timeout | `BoosterParams.function_timeout` + `utils/func_timeout/` |
| async def消费函数怎么用 / 异步消费 | async, 异步, asyncio, 协程 | `BoosterParams.concurrent_mode=ConcurrentModeEnum.ASYNC` + `concurrent_pool/async_pool_executor.py` |
| 实例方法怎么加@boost / 类方法怎么加 | 实例方法, 类方法, classmethod, instance | `core/booster.py` + `constant.py` L219 `FunctionKind` |
| 怎么暂停/恢复消费 | 暂停, 恢复, pause | `Booster.pause_consume()` / `.continue_consume()` → `base_consumer.py` |
| 怎么消息去重 / 防止重复消费 | 去重, 过滤, filtering | `BoosterParams.do_task_filtering` / `task_filtering_expire_seconds` |
| 消息过期怎么设 | 过期, expire | `BoosterParams.msg_expire_seconds` |
| 怎么多进程消费 / 怎么提高吞吐量 | 多进程, 吞吐, mp_consume | `core/muliti_process_enhance.py` L21 + `Booster.mp_consume()` |

### 18.3 结果与监控类

| 用户可能怎么问 | 关键词 | 去看哪里 |
|---------------|--------|---------|
| 怎么获取消费结果 / RPC模式怎么用 | 结果, RPC, AsyncResult | `BoosterParams.is_using_rpc_mode` + `core/msg_result_getter.py` L46 `AsyncResult` |
| 怎么在函数里获取task_id / 当前任务信息 | task_id, fct, 当前任务 | `core/current_task.py` L94 `fct` |
| 怎么保存运行状态到数据库 | 保存结果, 持久化, 运行状态 | `core/function_result_status_saver.py` L28 `FunctionResultStatus` + `BoosterParams` 中 `FunctionResultStatusPersistanceConfig` |
| 怎么看消费者心跳/哪些消费者在线 | 心跳, 在线, 活跃, 监控 | `BoosterParams.is_send_consumer_heartbeat_to_redis` + `core/active_cousumer_info_getter.py` L172 |
| 怎么远程杀死任务 | 杀死, kill, 远程停止 | `core/kill_remote_task.py` L111 `RemoteTaskKiller` |

### 18.4 定时与编排类

| 用户可能怎么问 | 关键词 | 去看哪里 |
|---------------|--------|---------|
| 怎么定时执行任务 / cron表达式 | 定时, cron, 周期, interval, schedule | `timing_job/timing_push.py` L11 `ApsJobAdder` |
| 怎么做任务链 / 串行执行多个任务 | 链, chain, 串行, 工作流 | `workflow/primitives.py` L45 `Chain` |
| 怎么并行执行一批任务再汇总 | 并行, group, chord, 汇总 | `workflow/primitives.py` L143 `Group` / L253 `Chord` |
| 发布时怎么设置延时/优先级/自定义task_id | countdown, eta, priority, TaskOptions | `core/func_params_model.py` L354 `TaskOptions` + `base_publisher.py` L51 `AbstractPublisher.publish` |

### 18.5 集成与扩展类

| 用户可能怎么问 | 关键词 | 去看哪里 |
|---------------|--------|---------|
| 怎么通过HTTP接口发任务 / FastAPI集成 | HTTP, API, FastAPI, REST | `faas/fastapi_adapter.py` L58 `fastapi_router` |
| FaaS接口有哪些 (publish/get_result/get_msg_count/clear_queue/pause/resume等) | FaaS接口大全 | `faas/fastapi_adapter.py` 所有路由函数一览 |
| 怎么用Flask | Flask | `faas/flask_adapter.py` L30 `flask_blueprint` |
| 怎么自定义broker / 怎么扩展新中间件 | 自定义, 扩展, 新broker | `factories/broker_kind__publsiher_consumer_type_map.py` L91 `register_custom_broker` |
| 怎么用Celery作为broker | Celery | `consumers/celery_consumer.py` + `assist/celery_helper.py` |
| 怎么批量消费 / 凑够N条再处理 | 批量, batch, 微批 | `contrib/override_publisher_consumer_cls/funboost_micro_batch_mixin.py` |
| 怎么加熔断 / 失败率太高自动停 | 熔断, circuit breaker | `contrib/override_publisher_consumer_cls/circuit_breaker_mixin.py` |
| 怎么接Prometheus / 监控指标 | Prometheus, 指标, metrics | `contrib/override_publisher_consumer_cls/funboost_promethus_mixin.py` |
| 怎么接OpenTelemetry / 链路追踪 | OpenTelemetry, tracing, 链路 | `contrib/override_publisher_consumer_cls/funboost_otel_mixin.py` |
| 怎么监听文件变化触发任务 | 文件监控, watchdog, 文件变化 | `contrib/register_custom_broker_contrib/watchdog_broker.py` |
| 怎么用WebSocket | WebSocket, ws | `contrib/register_custom_broker_contrib/websocket_broker.py` |
| 怎么用NATS Core / NATS无持久化 | NATS, nats-py, Core | `contrib/register_custom_broker_contrib/nats_core_broker.py` |
| 怎么用NATS JetStream / NATS持久化 | NATS, JetStream, nats-py, 持久化 | `contrib/register_custom_broker_contrib/nats_jetstream_broker.py` |
| 怎么用Redis ZSet覆盖消息 | ZSet, 覆盖, latest-wins | `contrib/register_custom_broker_contrib/redis_zset_broker.py` |
| 怎么用funboost做爬虫 / 爬虫辅助 | 爬虫, spider, 爬取, httpx, funspider | `contrib/funspider/` (SimpleSpiderClient, AsyncSpiderClient, SpiderItem) |
| 怎么用boost_spider (独立PyPI包) | boost_spider, RequestClient | PyPI包 `boost_spider` (不在此仓库, 需 `pip install boost_spider`) |
| 怎么配置队列告警 / 积压告警 / 掉线告警 | 告警, alert, 积压, 掉线, 通知 | `funweb/flask_bps/queue_alerts.py` |
| 怎么远程部署 | 部署, deploy, fabric | `core/fabric_deploy_helper.py` L17 `fabric_deploy` |
| Web管理界面怎么启动 | web, 管理界面, funweb, 后台 | `funweb/app.py` → `start_funboost_web_manager` |

### 18.6 配置类

| 用户可能怎么问 | 关键词 | 去看哪里 |
|---------------|--------|---------|
| Redis/Mongo/RabbitMQ连接地址怎么配 | 连接, 地址, URL, 配置文件 | `funboost_config_deafult.py` L22 `BrokerConnConfig` |
| funboost_config.py怎么写 | funboost_config, 配置文件 | `set_frame_config.py` L109 `use_config_form_funboost_config_module` |
| 日志怎么配 / 日志级别 | 日志, log, logger | `core/loggers.py` + `BoosterParams.log_level` |
| 时区怎么设 | 时区, timezone | `funboost_config_deafult.py` L115 `FunboostCommonConfig.TIMEZONE` |

---

## 十九、按实现层面快速检索

| 需求 | 定位 |
|------|------|
| 核心装饰器 | `core/booster.py` → `Booster` (L38) |
| 参数配置 | `core/func_params_model.py` → `BoosterParams` (L60) |
| 消费者基类 | `consumers/base_consumer.py` → `AbstractConsumer` (L101) |
| 发布者基类 | `publishers/base_publisher.py` → `AbstractPublisher` (L51) |
| RPC结果 | `core/msg_result_getter.py` → `AsyncResult` (L46) / `AioAsyncResult` (L149) |
| 任务上下文 | `core/current_task.py` → `fct` (L94) |
| 定时任务 | `timing_job/timing_push.py` → `ApsJobAdder` (L11) |
| FaaS FastAPI | `faas/fastapi_adapter.py` → `fastapi_router` (L58) |
| FaaS Flask | `faas/flask_adapter.py` → `flask_blueprint` (L30) |
| 消费者信息 | `core/active_cousumer_info_getter.py` → `SingleQueueConusmerParamsGetter` (L399) |
| 自定义broker | `factories/broker_kind__publsiher_consumer_type_map.py` → `register_custom_broker` (L91) |
| broker映射表 | `factories/broker_kind__publsiher_consumer_type_map.py` → `broker_kind__publsiher_consumer_type_map` (L58) |
| 工厂-消费者 | `factories/consumer_factory.py` → `get_consumer` (L13) |
| 工厂-发布者 | `factories/publisher_factory.py` → `get_publisher` (L15) |
| 常量/枚举 | `constant.py` → `BrokerEnum` (L5) / `ConcurrentModeEnum` (L201) |
| 连接配置 | `funboost_config_deafult.py` → `BrokerConnConfig` (L22) |
| 通用配置 | `funboost_config_deafult.py` → `FunboostCommonConfig` (L115) |
| 配置加载 | `set_frame_config.py` → `use_config_form_funboost_config_module` (L109) |
| 弹性线程池 | `concurrent_pool/flexible_thread_pool.py` → `FlexibleThreadPool` (L78) |
| 异步池 | `concurrent_pool/async_pool_executor.py` → `AsyncPoolExecutor` (L57) |
| 并发池构建 | `concurrent_pool/pool_commons.py` → `ConcurrentPoolBuilder` (L10) |
| 序列化 | `core/serialization.py` → `Serialization` (L10) |
| 异常类 | `core/exceptions.py` → `ExceptionForRetry` (L141) 等 |
| 远程杀任务 | `core/kill_remote_task.py` → `RemoteTaskKiller` (L111) |
| 入参校验 | `core/consuming_func_input_params_check.py` → `ConsumingFuncInputParamsChecker` (L10) |
| 运行状态 | `core/function_result_status_saver.py` → `FunctionResultStatus` (L28) |
| 多进程增强 | `core/muliti_process_enhance.py` → `run_consumer_with_multi_process` (L21) |
| 远程部署 | `core/fabric_deploy_helper.py` → `fabric_deploy` (L17) |
| CLI命令 | `core/cli/funboost_fire.py` → `BoosterFire` (L15) |
| 自动发现 | `core/cli/discovery_boosters.py` → `BoosterDiscovery` (L64) |
| 工作流 | `workflow/primitives.py` → `Chain` (L45) / `Group` (L143) / `Chord` (L253) |
| 签名 | `workflow/signature.py` → `Signature` (L37) |
| FunboostPool / MemoryFunboostPool | `core/funboost_pool.py` → `FunboostPool`, `MemoryFunboostPool` |
| 微批消费 | `contrib/override_publisher_consumer_cls/funboost_micro_batch_mixin.py` |
| 熔断器 | `contrib/override_publisher_consumer_cls/circuit_breaker_mixin.py` |
| Prometheus | `contrib/override_publisher_consumer_cls/funboost_promethus_mixin.py` |
| OpenTelemetry | `contrib/override_publisher_consumer_cls/funboost_otel_mixin.py` |
| 周期额度 | `contrib/override_publisher_consumer_cls/periodic_quota_mixin.py` |
| 告警通知 | `contrib/override_publisher_consumer_cls/alert_notifier_mixin.py` |
| Watchdog broker | `contrib/register_custom_broker_contrib/watchdog_broker.py` |
| WebSocket broker | `contrib/register_custom_broker_contrib/websocket_broker.py` |
| NATS Core broker | `contrib/register_custom_broker_contrib/nats_core_broker.py` |
| NATS JetStream | `contrib/register_custom_broker_contrib/nats_jetstream_broker.py` |
| Redis ZSet broker(p/delay) | `contrib/register_custom_broker_contrib/redis_zset_broker.py` |
| Redis HASH Update | `contrib/register_custom_broker_contrib/redis_hash_update_broker.py` |
| CeleryPool broker | `contrib/register_custom_broker_contrib/celery_pool_as_funboost_broker.py` |
| 爬虫辅助(funspider) | `contrib/funspider/` → `SimpleSpiderClient`, `AsyncSpiderClient`, `SpiderItem` |
| 队列告警 | `funweb/flask_bps/queue_alerts.py` → `alert_bp`, `_check_rules_once` |
| Pydantic兼容 | `core/pydantic_compatible_base.py` → `BaseJsonAbleModel` (L162) |
| Web管理 | `funweb/app.py` → `start_funboost_web_manager` |
| 脚本部署 | `funweb/flask_bps/script_deploy.py` |
| MySQL binlog监听 | `contrib/cdc/mysql_cdc_binlog_listener.py` → `MySqlCdcBinlogListener` |
| 队列实现 | `queues/sqla_queue.py` (L78) / `postgres_queue.py` (L34) / `peewee_queue.py` (L22) |

---

*本文档由 AI 分析 funboost 源码生成，用于快速检索源码位置。*
*配套教程文档: `funboost/md_for_ai/funboost教程速查for_ai.md`*
*AI 编程指南（铁律 + 代码技能模板 + BoosterParams 全量字段）: `funboost/md_for_ai/funboost_ai_coding_编程指南_rules_and_skills.md`*
*终极上下文文档（完整教程 + 源码 + 示例，可投喂给 LLM）: `funboost_all_docs_and_codes.md`*