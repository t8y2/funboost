# AGENTS.md — Funboost 项目全貌（AI 专用指南）

> 本文档专为 AI 代理设计，基于 `funboost/md_for_ai/` 目录下的所有资料综合编写。
> 如果你是开发者调试或阅读源码，请优先参考 `funboost/md_for_ai/funboost源码速查for_ai.md`（含精确行号）。

---

## 一、项目概况

| 属性 | 值 |
|------|-----|
| 项目 | Funboost — Python 分布式函数调度平台 |
| 核心入口 | `@boost(BoosterParams(...))` 装饰器 |
| 源码根目录 | `funboost/funboost/` |
| 核心结构 | 单包非 monorepo |
| 设计哲学 | **反框架**：零代码侵入，即插即用。`func(x, y)` 直接运行，`func.push(x, y)` 才发到队列 |

### 一句话本质

> **Funboost = 一行 `@boost` 装饰器，让你的任意 Python 函数瞬间获得分布式调度 + FaaS 微服务 + 50 种消息队列 + 30+ 种任务控制功能 + 工作流编排 + CDC 事件驱动 + OpenTelemetry 链路追踪的能力。**

---

## 二、AI 必读：`md_for_ai/` 目录索引

这是专门为 AI 准备的参考文档目录，**所有关于 funboost 的代码生成和问题回答，应优先查阅以下文件**：

| 文件 | 内容 | 用途 |
|------|------|------|
| `funboost源码速查for_ai.md` | 完整源码目录、类/函数/模块的精确行号、Broker映射表、自然语言路由表 | **源码定位首选** |
| `funboost教程速查for_ai.md` | 教程文档速查（**当前为空文件，暂不可用**） | 教程查阅 |
| `funboost_ai_coding_编程指南_rules_and_skills.md` | **AI 行为铁律 + 12 个标准代码技能模板** | **AI 代码生成必读！含 BoosterParams 全量字段定义** |
| `如何扩展增加新的中间件.md` | 3 种扩展 Broker 的方式（静态/register_custom_broker/override_cls） | 扩展开发指南 |

> **重要**：`funboost_all_docs_and_codes.md`（约 2.9 MB）包含完整教程 + 源码 + 示例，是最高事实标准。
> AI 生成任何 funboost 代码前，应优先检索该文档以消除幻觉。

---

## 三、核心 API

### 3.1 核心语法

```python
# ✅ 推荐（必须）—— 使用 BoosterParams 对象传参
@boost(BoosterParams(queue_name="my_queue", qps=5, ...))
def my_task(x, y):
    return x + y

# ❌ 禁止使用老式写法
@boost("queue_name", qps=5)       # 过时写法，无代码补全
```

- `BoosterParams` 是一个 Pydantic 模型，**绝对禁止臆造不存在的字段**（如 `timeout`→正确的是 `function_timeout`；如 `max_retries`→正确的是 `max_retry_times`）
- 支持**继承** `BoosterParams` 减少重复配置（详见 `md_for_ai` 中 Skills[8]）

### 3.2 发布消息

| 方法 | 场景 | 说明 |
|------|------|------|
| `func.push(*args, **kwargs)` | 只需传递业务参数 | 返回 `AsyncResult` |
| `func.publish(msg_dict, task_options=TaskOptions(...))` | 需要框架控制参数（`task_id`, `countdown`, `eta`, `priority`） | 返回 `AsyncResult` |
| `await func.aio_push(...)` | 异步环境 | 返回 `AioAsyncResult` |
| `await func.aio_publish(...)` | 异步环境 + 控制参数 | 返回 `AioAsyncResult` |

### 3.3 消费启动

| 方法 | 说明 |
|------|------|
| `func.consume()` | 基础启动消费（非阻塞） |
| `func.multi_process_consume(n)` / `func.mp_consume(n)` | 多进程 + 多线程叠加并发 |
| `BoostersManager.consume_group("group_name")` | 按分组启动多个消费函数 |
| `ctrl_c_recv()` | 阻塞主线程，让 Ctrl+C 能方便停止程序（非必需，不加也可关窗口或 kill 进程） |

**注意**：
- 连续启动多个消费者：`func1.consume(); func2.consume()` 即可，**不要**用 `threading.Thread` 包装
- AI 调用 funboost 脚本后必须及时 kill 进程（否则被无限消费循环阻塞），应使用 `subprocess.run(['python', 'script.py'], timeout=30)` 自动终止

### 3.4 任务上下文获取

```python
from funboost import fct

fct.task_id                        # 当前任务 ID
fct.queue_name                     # 队列名
fct.run_times                      # 运行次数（含重试）
fct.full_msg                       # 完整消息体
fct.function_params                # 函数参数
fct.function_result_status         # FunctionResultStatus 对象
fct.logger                         # 当前任务 logger
```

> **禁止在函数参数中用 `self` 或 `bind=True` 取上下文（那是 Celery 的思维）**

### 3.5 RPC 模式（获取消费结果）

```python
# 同步
async_result = my_task.push(10, 20)
print(async_result.result)         # 阻塞等待结果

# 异步
aio_result = await my_task.aio_push("http://example.com")
result_status = await AioAsyncResult(aio_result.task_id).status_and_result
```

**条件**：`BoosterParams` 中需设置 `is_using_rpc_mode=True`

### 3.6 定时任务

```python
from funboost import ApsJobAdder

ApsJobAdder(func, job_store_kind='redis').add_push_job(
    trigger='cron', hour=2, minute=0, kwargs={"type": "daily"}, id='job1'
)
ApsJobAdder(func, job_store_kind='redis').add_push_job(
    trigger='interval', seconds=30, args=(1, 2), id='job2'
)
ApsJobAdder(func, job_store_kind='redis').add_push_job(
    trigger='date', run_date='2025-06-30 16:25:40', args=(7, 8), id='job3'
)
```

> **禁止直接使用 `apscheduler.add_job` 去执行消费函数，必须使用 `ApsJobAdder`**

### 3.7 工作流编排

```python
from funboost.workflow import chain, group, chord, WorkflowBoosterParams

# Chain（串行）、Group（并行）、Chord（并行+回调）
workflow = chain(
    download.s("video.mp4"),
    chord(
        group(process.s(resolution=r) for r in ['360p', '720p', '1080p']),
        notify.s(user_id=1001)
    )
)
result = workflow.apply()
```

### 3.8 FaaS 微服务

```python
from fastapi import FastAPI
from funboost.faas import fastapi_router

app = FastAPI()
app.include_router(fastapi_router)   # 一键获得 /funboost/publish 等接口

# Flask 版本
from funboost.faas import flask_blueprint
```

**接口一览**：
- `POST /funboost/publish` — 发布消息
- `GET /funboost/get_result?task_id=xxx` — 获取 RPC 结果
- `POST /funboost/add_timing_job` — 添加定时任务
- `GET /funboost/get_msg_count?queue_name=xxx` — 获取消息数量
- `POST /funboost/pause_consume` / `POST /funboost/resume_consume` — 暂停/恢复消费
- `POST /funboost/clear_queue` — 清空队列
- `GET /funboost/get_all_queues` — 获取所有队列

## 四、BoosterParams 核心字段速览（50+ 字段）

### 基础
| 字段 | 类型 | 说明 |
|------|------|------|
| `queue_name` | `str` | **必填**，队列名（每个函数应使用不同队列名） |
| `broker_kind` | `str` | 中间件类型，默认 `BrokerEnum.SQLITE_QUEUE` |
| `project_name` | `Optional[str]` | 项目标签（Web 管理用） |

### 并发
| 字段 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `concurrent_mode` | `str` | `THREADING` | THREADING/GEVENT/EVENTLET/ASYNC/SINGLE_THREAD |
| `concurrent_num` | `int` | 50 | 并发数量 |
| `specify_concurrent_pool` | 池对象 | None | 指定线程池/协程池，多消费者可共用一个 |

### 控频
| 字段 | 类型 | 说明 |
|------|------|------|
| `qps` | `float/int/None` | 每秒执行次数（可设小数如 0.01 = 100秒1次） |
| `is_using_distributed_frequency_control` | `bool` | 分布式控频（需 Redis） |

### 重试
| 字段 | 类型 | 说明 |
|------|------|------|
| `max_retry_times` | `int` | 最大重试次数（默认 3） |
| `is_using_advanced_retry` | `bool` | 启用指数退避重试 |
| `advanced_retry_config` | `dict` | 退避配置（retry_mode/retry_base_interval/retry_multiplier/retry_max_interval/retry_jitter） |
| `is_push_to_dlx_queue_when_retry_max_times` | `bool` | 重试耗尽后推送到死信队列 |

### 超时与熔断
| 字段 | 类型 | 说明 |
|------|------|------|
| `function_timeout` | `int/float/None` | 函数超时秒数（谨慎使用，会降低性能） |
| `is_support_remote_kill_task` | `bool` | 是否支持远程杀任务 |

### 消息控制
| 字段 | 类型 | 说明 |
|------|------|------|
| `msg_expire_seconds` | `int/float/None` | 消息过期时间 |
| `do_task_filtering` | `bool` | 是否对任务入参去重 |
| `task_filtering_expire_seconds` | `int` | 去重过滤的过期时间 |

### RPC
| 字段 | 类型 | 说明 |
|------|------|------|
| `is_using_rpc_mode` | `bool` | 是否启用 RPC 模式 |
| `rpc_result_expire_seconds` | `int` | RPC 结果过期时间 |
| `rpc_timeout` | `int` | RPC 等待超时 |

### 异步消费（async def）
- **推荐**设置 `concurrent_mode=ConcurrentModeEnum.ASYNC`（多线程模式也可兼容 async def，但不是最佳选择）
- **必须**使用 `await func.aio_push()` 发布
- 异步获取 RPC 结果：必须用 `AioAsyncResult` + `await`，禁止用 `AsyncResult.result`

### 消费异构系统消息
- 设置 `should_check_publish_func_params=False`
- 消费函数定义为 `def task_fun(**kwargs):`（用 `**kwargs` 接收所有字段）

### broker_exclusive_config
| 字段 | 类型 | 说明 |
|------|------|------|
| `broker_exclusive_config` | `dict` | 中间件专有配置（如 RabbitMQ 的 `x-max-priority`、Kafka 的 `group_id`、Redis 的 `pull_msg_batch_size`）。**严禁臆造键名**，支持的键见 `core/broker_kind__exclusive_config_default_define.py` |

### 日志
| 字段 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `log_level` | `int` | `DEBUG` | 日志级别 |
| `logger_prefix` | `str` | `''` | 日志名前缀 |
| `create_logger_file` | `bool` | `True` | 是否创建文件日志 |
| `logger_name` | `str` | `''` | 日志命名空间 |
| `log_filename` | `str` | `None` | 文件日志名（自动生成） |

### 其他
| `user_options` | `dict` | 用户自定义配置，自由发挥 |
| `consumer_override_cls` | `Type` | 自定义消费者类（Mixin 混入） |
| `publisher_override_cls` | `Type` | 自定义发布者类 |
| `booster_group` | `str` | 消费分组名（配合 `BoostersManager.consume_group`） |
| `allow_run_time_cron` | `str` | 允许运行的时间窗口（cron 表达式） |
| `is_auto_start_consuming_message` | `bool` | 是否定义后自动消费 |

## 五、Broker 中间件

### 5.1 核心分类

| 类别 | BrokerEnum 枚举值 |
|------|-------------------|
| Redis 系列 | `REDIS`, `REDIS_ACK_ABLE`, `REIDS_ACK_USING_TIMEOUT`, `REDIS_STREAM`, `REDIS_PRIORITY`, `REDIS_BRPOP_LPUSH`, `REDIS_PUBSUB`, `REDIS_ZSET_PRIORITY`, `REDIS_ZSET_DELAY` |
| RabbitMQ | `RABBITMQ_AMQPSTORM`(= `RABBITMQ`), `RABBITMQ_COMPLEX_ROUTING`, `RABBITMQ_AMQP`, `RABBITMQ_PIKA`, `RABBITMQ_RABBITPY` |
| Kafka | `KAFKA`, `KAFKA_CONFLUENT`(= `CONFLUENT_KAFKA`), `KAFKA_CONFLUENT_SASlPlAIN` |
| RocketMQ | `ROCKETMQ`, `ROCKETMQ5` |
| 其他 MQ | `PULSAR`, `NSQ`, `MQTT`, `NATS_CORE`, `NATS_JETSTREAM`, `ZEROMQ`, `SQS`, `HTTPSQS` |
| 内存/本地 | `MEMORY_QUEUE`（**最重要，零序列化开销**）, `FASTEST_MEM_QUEUE`, `SQLITE_QUEUE`, `TXT_FILE` |
| 数据库 | `MONGOMQ`, `SQLACHEMY`, `POSTGRES`, `PEEWEE` |
| 网络协议 | `TCP`, `UDP`, `HTTP`, `GRPC`, `WEBSOCKET` |
| 框架集成 | `CELERY`, `DRAMATIQ`, `HUEY`, `RQ`, `NAMEKO`, `KOMBU` |
| 特殊 | `MYSQL_CDC`（Binlog 事件驱动）, `WATCHDOG`（文件监控）, `EMPTY` |

### 5.2 常用 Redis 模式选型

| 模式 | 适用 | 不适用 |
|------|------|--------|
| `REDIS` | 简单队列，允许丢数据 | 需要 ACK 确认的场景 |
| `REDIS_ACK_ABLE` | **大部分场景推荐**，消费确认 | 无 |
| `REDIS_STREAM` | 消费者组、消息回溯 | 单消费者简单场景 |

### 5.3 Broker 扩展方式

3 种方式：
1. **静态扩展**：在 `funboost/consumers` 和 `funboost/publishers` 中直接写死代码（仅限作者）
2. **`register_custom_broker`**：完全全新中间件，代码可放在 `contrib/register_custom_broker_contrib/`
3. **`consumer_override_cls` / `publisher_override_cls`**：Mixin 混入，定制现有 broker 行为

详见 `md_for_ai/如何扩展增加新的中间件.md`

## 六、扩展模块（Contrib）

### 6.1 Override Mixins（高性能扩展）
| Mixin | 文件 | 功能 |
|-------|------|------|
| `CircuitBreakerConsumerMixin` | `circuit_breaker_mixin.py` | 熔断器（失败率达阈值自动熔断） |
| `MicroBatchConsumerMixin` | `funboost_micro_batch_mixin.py` | 微批消费（凑批或超时触发） |
| `PrometheusConsumerMixin` | `funboost_promethus_mixin.py` | Prometheus 指标采集 |
| `AutoOtelPublisherMixin` / `AutoOtelConsumerMixin` | `funboost_otel_mixin.py` | OpenTelemetry 链路追踪 |
| `PeriodicQuotaConsumerMixin` | `periodic_quota_mixin.py` | 周期额度限制 |
| `AlertNotifierConsumerMixin` | `alert_notifier_mixin.py` | 异常告警通知 |

### 6.2 自定义 Broker
| Broker | 文件 | 说明 |
|--------|------|------|
| Watchdog | `watchdog_broker.py` | 文件系统监控 |
| WebSocket | `websocket_broker.py` | WebSocket 通信 |
| NATS Core | `nats_core_broker.py` | NATS 无持久化模式 |
| NATS JetStream | `nats_jetstream_broker.py` | NATS 持久化 + 消费确认 |
| Redis ZSet Priority/Delay | `redis_zset_broker.py` | 无级优先级 / 延迟队列 |
| Redis Hash Update | `redis_hash_update_broker.py` | 可更新覆盖消息（latest-wins） |
| CeleryPool | `celery_pool_as_funboost_broker.py` | 复用 Celery 连接池 |

### 6.3 爬虫辅助
| 模块 | 说明 |
|------|------|
| `contrib/funspider/` | 基于 httpx + SQLModel 的爬虫辅助（内置 `funboost`） |
| `pip install boost_spider` | 独立 PyPI 包，自由至上、极简字典流 |

**funspider 核心组件**：
- `SimpleSpiderClient` — 同步爬虫客户端，支持自动重试 + 随机 UA + 可插拔代理
- `AsyncSpiderClient` — 异步爬虫客户端（httpx.AsyncClient）
- `SpiderResponse` — 内置 `.xpath()` / `.css()` / `.re()` / `.resp_dict`
- `SpiderItem` — SQLModel ORM 基类，`.insert()` / `.upsert()` / `.aio_upsert()` + MongoDB 支持

**安装**：`pip install sqlmodel httpx parsel`

### 6.4 CDC 数据同步
| 模块 | 说明 |
|------|------|
| `contrib/cdc/mysql2mysql.py` | `MySql2Mysql` — MySQL Binlog → MySQL |

### 6.5 其他
| 模块 | 说明 |
|------|------|
| `contrib/queue2queue.py` | 队列转发 |
| `contrib/django_db_deco.py` | Django DB 连接管理 |
| `contrib/api_publish_msg.py` | Pydantic 消息模型 |
| `contrib/save_function_result_status/` | 结果持久化到 SQL |

---

## 七、Web 管理界面（funweb）

启动方式：
```python
from funboost.funweb.app import start_funboost_web_manager
start_funboost_web_manager(port=27018, care_project_name="my_project")

# 或命令行
python -m funboost.funweb.app
```

### 功能模块
| 蓝图 | 功能 |
|------|------|
| `system_monitor.py` | Redis 心跳采集，系统监控 API |
| `script_deploy.py` | 脚本部署 CRUD，Git 操作，进程控制，日志 tail |
| `log_viewer.py` | 日志查看器（文件夹白名单，tail，grep，stream） |
| `queue_alerts.py` | **5 种告警类型**：积压 / QPS 骤降 / 掉线 / 失败率飙升 / 耗时过高 |
| `web_helper.py` | IP/hostname 辅助 |

---

## 九、测试体系

| 目录 | 说明 |
|------|------|
| `tests/ai_codes/` | AI 生成的测试脚本 |
| `tests/ai_codes/regression_testing/` | 回归测试 |
| `test_frame/` | 127 个子目录，每个目录含独立测试脚本 |
| 运行方式 | `python tests/ai_codes/<脚本>.py` 或 `python test_frame/<目录>/<脚本>.py` |

> **项目无 pytest / CI 配置**，所有测试都是独立 `.py` 脚本。
> **AI 运行测试时**：使用 `subprocess.run(['python', 'script.py'], timeout=30)` 确保超时后自动 kill。

## 十、配置机制

| 文件 | 说明 |
|------|------|
| `funboost/funboost_config_deafult.py` | 默认配置（`BrokerConnConfig` + `FunboostCommonConfig`） |
| `funboost/set_frame_config.py` | 配置加载器：首次运行自动在项目根目录生成 `funboost_config.py` |
| 项目根目录下的 `funboost_config.py` | 用户配置，会覆盖默认配置 |
| 项目根目录下的 `nb_log_config.py` | 日志配置（`nb_log` 自动生成） |

**关键配置项**：
- `BrokerConnConfig` — Redis/Mongo/RabbitMQ/Kafka 等连接地址
- `FunboostCommonConfig` — 时区、日志格式等
- 如果使用 `is_using_rpc_mode=True`、`is_using_distributed_frequency_control=True` 或 `do_task_filtering=True`，**必须**配置 Redis

---

## 十一、代码风格与约定

| 项 | 值 |
|----|-----|
| 缩进 | 4 空格 |
| 最大行宽 | 400 |
| 换行符 | CRLF（Windows） |
| 类型注解 | 使用但不强制（无 mypy） |
| 参数模型 | Pydantic（`BoosterParams` 等继承 `BaseJsonAbleModel`） |
| Pydantic 版本 | v1/v2 兼容（`core/pydantic_compatible_base.py`） |
| 日志 | `nb_log`（配置文件在项目根目录 `nb_log_config.py`） |
| 序列化 | JSON（支持 datetime 等），可选 Pickle |

---

## 十三、异常类

| 异常 | 说明 |
|------|------|
| `ExceptionForRetry` | 手动触发重试（函数内抛出即可） |
| `ExceptionForRequeue` | 消息重新入队 |
| `ExceptionForPushToDlxqueue` | 推送消息到死信队列 |
| `FunboostWaitRpcResultTimeout` | RPC 结果等待超时 |
| `FunboostTaskExecutionError` | 任务执行错误 |

---

## 十四、快速命令速查

```bash
# 安装
pip install funboost
pip install funboost[all]            # 安装所有可选中间件依赖

# 运行 funboost 脚本
python your_task_script.py

# 启动 Web 管理
python -m funboost.funweb.app

# 发布到 PyPI
python setup.py sdist bdist_wheel && twine upload dist/*
```

---

## 十五、文件拓扑速览

```
funboost/
├── __init__.py                 # 包入口，导出所有公共 API
├── constant.py                 # BrokerEnum / ConcurrentModeEnum
├── funboost_config_deafult.py  # 默认配置
├── set_frame_config.py         # 配置加载
├── core/                       # 核心引擎
│   ├── booster.py              # Booster 装饰器 + BoostersManager
│   ├── func_params_model.py    # BoosterParams（50+ 字段）
│   ├── current_task.py         # fct 任务上下文
│   ├── msg_result_getter.py    # AsyncResult / AioAsyncResult RPC 结果
│   ├── function_result_status_saver.py  # FunctionResultStatus
│   ├── exceptions.py           # 异常类
│   ├── serialization.py        # 序列化
│   ├── pydantic_compatible_base.py # Pydantic v1/v2 兼容基类
│   ├── funboost_pool.py        # FunboostPool / MemoryFunboostPool
│   ├── loggers.py              # 日志器
│   ├── helper_funs.py          # MsgGenerater / run_forever
│   ├── kill_remote_task.py     # RemoteTaskKiller
│   ├── active_cousumer_info_getter.py  # 活跃消费者信息
│   ├── broker_kind__exclusive_config_default_define.py  # broker 专属配置默认值
│   ├── consuming_func_input_params_check.py  # 入参校验
│   ├── funboost_time.py        # 时间处理
│   ├── muliti_process_enhance.py  # 多进程增强
│   ├── fabric_deploy_helper.py # 远程部署
│   ├── mongo_alert_monitor.py  # Mongo 报警监控
│   ├── lazy_impoter.py         # 懒加载可选依赖
│   ├── funboost_config_getter.py  # 用户配置加载
│   ├── task_id_logger.py       # TaskIdLogger
│   └── cli/                    # 命令行
├── consumers/                  # 49 个消费者实现
├── publishers/                 # 45 个发布者实现
├── factories/                  # broker_kind → (Publisher, Consumer) 映射
├── concurrent_pool/            # 5 种并发池
├── timing_job/                 # APScheduler 集成
├── faas/                       # FastAPI / Flask / Django 集成
├── workflow/                   # Chain / Group / Chord
├── contrib/                    # 扩展模块
│   ├── funspider/              # 爬虫辅助
│   ├── cdc/                    # CDC 同步
│   ├── override_publisher_consumer_cls/  # Mixin 扩展
│   └── register_custom_broker_contrib/   # 自定义 Broker
├── funweb/                     # Web 管理界面
├── queues/                     # 队列实现
├── utils/                      # 工具模块
├── assist/                     # 第三方框架集成
├── beggar_version_implementation/  # 乞丐版实现
└── md_for_ai/                  # AI 参考文档
    ├── funboost源码速查for_ai.md
    ├── funboost教程速查for_ai.md
    ├── funboost_ai_coding_编程指南_rules_and_skills.md
    └── 如何扩展增加新的中间件.md
```

---

## 十六、给 AI 的特别提醒

1. **`funboost_all_docs_and_codes.md` 是最高事实标准** — 生成任何代码前，先检索它
2. **禁止臆造参数名** — `BoosterParams` 的所有字段都是固定的，必须从 Skill 100 的字典中取值
3. **禁止使用 Celery 思维** — 获取上下文用 `fct`，不要用 `self` 或 `bind=True`
4. **消费启动后不会自动结束** — AI 运行测试必须用 `subprocess.run(['python', 'script.py'], timeout=30)` 自动终止
5. **`push` 和 `publish` 的区别** — `push` 传业务参数，`publish` 传字典 + 框架控制参数
6. **实例方法的 push 语法特殊** — 必须写成 `ClassName.method.push(obj, args)`，第一个参数传对象实例
7. **关系型数据库 vs MongoDB** — `SpiderItem` 同时支持 SQL（通过 SQLModel）和 MongoDB
