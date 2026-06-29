# AGENTS.md — Funboost 项目全貌（AI 专用指南）


> **Funboost = 一行 `@boost` 装饰器，让你的任意 Python 函数瞬间获得分布式调度 + FaaS 微服务 + 50 种消息队列 + 5种并发模式 + 30+ 种任务控制功能 + 工作流编排的能力。**

| 属性 | 值 |
|------|-----|
| 核心入口 | `@boost(BoosterParams(...))` 装饰器 |
| 源码根目录 | `funboost/funboost/` |
| 设计哲学 | **反框架**：零代码侵入。`func(x, y)` 直接运行，`func.push(x, y)` 才发到队列 |

> **AI 在回答 funboost 相关问题前，必须先阅读以下文件：**
> - @funboost/md_for_ai/funboost_ai_coding_编程指南_rules_and_skills.md （AI 编码铁律 + BoosterParams 全量字段 + 12 个技能模板）
> - @funboost/md_for_ai/funboost源码速查for_ai.md （源码定位 + 行号速查 + Broker 映射表）
> - @funboost/md_for_ai/funboost教程速查for_ai.md （教程文档速查）
> - @funboost/md_for_ai/如何扩展增加新的中间件.md （Broker 扩展指南）
> - @funboost_all_docs_and_codes.md （最高事实标准，完整教程 + 源码 + 示例，AI 生成代码前应优先检索此文件以消除幻觉）

---

## 二、核心 API

### 2.1 核心语法

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

### 2.2 发布消息

| 方法 | 场景 | 说明 |
|------|------|------|
| `func.push(*args, **kwargs)` | 只需传递业务参数 | 返回 `AsyncResult` |
| `func.publish(msg_dict, task_options=TaskOptions(...))` | 需要框架控制参数（`task_id`, `countdown`, `eta`, `priority`） | 返回 `AsyncResult` |
| `await func.aio_push(...)` | 异步环境 | 返回 `AioAsyncResult` |
| `await func.aio_publish(...)` | 异步环境 + 控制参数 | 返回 `AioAsyncResult` |

### 2.3 消费启动

| 方法 | 说明 |
|------|------|
| `func.consume()` | 启动消费（非阻塞），可连续调用多个：`func1.consume(); func2.consume()` |
| `func.multi_process_consume(n)` / `func.mp_consume(n)` | 多进程 + 多线程叠加并发 |
| `BoostersManager.consume_group("group_name")` | 按分组启动多个消费函数 |
| `enable_ctrl_c_quit_on_windows()` | 阻塞主线程，让 Ctrl+C 能在windows系统上 方便的停止程序（非必需，不加也可关窗口或 kill 进程） |

**注意**：
- 连续启动多个消费者：`func1.consume(); func2.consume()` 即可，**不要**用 `threading.Thread` 包装
- AI 调用 funboost 脚本后必须及时 kill 进程（否则被无限消费循环阻塞），应使用 `subprocess.run(['python', 'script.py'], timeout=30)` 自动终止

### 2.4 任务上下文获取

```python
from funboost import fct

fct.task_id                        # 当前任务 ID
fct.queue_name                     # 队列名
fct.function_result_status.run_times                     # 运行次数（含重试）
fct.full_msg                       # 完整消息体
fct.function_result_status.function_params                # 函数参数
fct.function_result_status         # FunctionResultStatus 对象
fct.logger                         # 当前任务 logger
```

> **禁止在函数参数中用 `self` 或 `bind=True` 取上下文（那是 Celery 的思维）**

### 2.5 RPC 模式（获取消费结果）

```python
# 同步
async_result = my_task.push(10, 20)
print(async_result.result)         # 阻塞等待结果

# 异步
aio_result = await my_task.aio_push("http://example.com")
result_status = await AioAsyncResult(aio_result.task_id).status_and_result
```

**条件**：`BoosterParams` 中需设置 `is_using_rpc_mode=True` ,必须切记这条规则。

### 2.6 定时任务

```python
from funboost import ApsJobAdder

ApsJobAdder(func, job_store_kind='redis').add_push_job(
    trigger='cron', hour=2, minute=0, kwargs={"type": "daily"}, id='job1'
)
ApsJobAdder(func, job_store_kind='redis').add_push_job(
    trigger='interval', seconds=30, args=(1, 2), id='job2'
)
```

> **禁止直接使用 `apscheduler.add_job` 去执行消费函数，必须使用 `ApsJobAdder`**

### 2.7 工作流编排

```python
from funboost.workflow import chain, group, chord, WorkflowBoosterParams

workflow = chain(
    download.s("video.mp4"),
    chord(
        group(process.s(resolution=r) for r in ['360p', '720p', '1080p']),
        notify.s(user_id=1001)
    )
)
result = workflow.apply()
```

### 2.8 FaaS 微服务

```python
from fastapi import FastAPI
from funboost.faas import fastapi_router

app = FastAPI()
app.include_router(fastapi_router)   # 一键获得 /funboost/publish 等接口

# Flask 版本
from funboost.faas import flask_blueprint
```

---

## 三、BoosterParams 核心字段速览（50+ 字段）

| 分类 | 字段 | 类型 | 说明 |
|------|------|------|------|
| **基础** | `queue_name` | `str` | **必填**，队列名 |
| | `broker_kind` | `str` | 中间件类型，默认 `BrokerEnum.SQLITE_QUEUE` |
| | `project_name` | `Optional[str]` | 项目标签（Web 管理用） |
| **并发** | `concurrent_mode` | `str` | THREADING/GEVENT/EVENTLET/ASYNC/SINGLE_THREAD |
| | `concurrent_num` | `int` | 并发数量（默认 50） |
| | `specify_concurrent_pool` | 池对象 | 指定线程池/协程池 |
| **控频** | `qps` | `float/int/None` | 每秒执行次数（0.01 = 100秒1次） |
| | `is_using_distributed_frequency_control` | `bool` | 分布式控频（需 Redis） |
| **重试** | `max_retry_times` | `int` | 最大重试次数（默认 3） |
| | `is_using_advanced_retry` | `bool` | 启用指数退避重试 |
| | `is_push_to_dlx_queue_when_retry_max_times` | `bool` | 重试耗尽推送死信队列 |
| **超时** | `function_timeout` | `int/float/None` | 函数超时秒数 |
| **消息** | `msg_expire_seconds` | `int/float/None` | 消息过期时间 |
| | `do_task_filtering` | `bool` | 任务入参去重 |
| **RPC** | `is_using_rpc_mode` | `bool` | 启用 RPC 模式 |
| **日志** | `log_level` | `int` | 日志级别（默认 DEBUG） |
| | `create_logger_file` | `bool` | 是否创建文件日志 |
| **其他** | `consumer_override_cls` | `Type` | 自定义消费者类（Mixin 混入） |
| | `publisher_override_cls` | `Type` | 自定义发布者类 |
| | `booster_group` | `str` | 消费分组名 |
| | `broker_exclusive_config` | `dict` | 中间件专有配置，**严禁臆造键名** |

> 以上为高频字段摘要。完整 50+ 字段定义见 @funboost/md_for_ai/funboost_ai_coding_编程指南_rules_and_skills.md

### 异步消费要点
- **推荐** `concurrent_mode=ConcurrentModeEnum.ASYNC`，**必须**用 `await func.aio_push()` 发布
- 异步 RPC 结果：必须用 `AioAsyncResult` + `await`，禁止用 `AsyncResult.result`

### 消费异构系统消息
- 设置 `should_check_publish_func_params=False`
- 消费函数定义为 `def task_fun(**kwargs):`（用 `**kwargs` 解包接收所有字段）
- **禁止**用单个 `msg` 参数接收整个 JSON（如 `def task_fun(msg):`），必须用 `**msg` 或 `**kwargs`

---

## 四、Broker 中间件

| 类别 | BrokerEnum 枚举值 |
|------|-------------------|
| Redis 系列 | `REDIS`, `REDIS_ACK_ABLE`, `REIDS_ACK_USING_TIMEOUT`, `REDIS_STREAM`, `REDIS_PRIORITY`, `REDIS_BRPOP_LPUSH`, `REDIS_PUBSUB`, `REDIS_ZSET_PRIORITY`, `REDIS_ZSET_DELAY` |
| RabbitMQ | `RABBITMQ_AMQPSTORM`(= `RABBITMQ`), `RABBITMQ_COMPLEX_ROUTING`, `RABBITMQ_AMQP`, `RABBITMQ_PIKA`, `RABBITMQ_RABBITPY` |
| Kafka | `KAFKA`, `KAFKA_CONFLUENT`(= `CONFLUENT_KAFKA`), `KAFKA_CONFLUENT_SASlPlAIN` |
| RocketMQ | `ROCKETMQ`, `ROCKETMQ5` |
| 其他 MQ | `PULSAR`, `NSQ`, `MQTT`, `NATS_CORE`, `NATS_JETSTREAM`, `ZEROMQ`, `SQS`, `HTTPSQS` |
| 内存/本地 | `MEMORY_QUEUE`（**零序列化开销**）, `FASTEST_MEM_QUEUE`, `SQLITE_QUEUE`, `TXT_FILE` |
| 数据库 | `MONGOMQ`, `SQLACHEMY`, `POSTGRES`, `PEEWEE` |
| 网络协议 | `TCP`, `UDP`, `HTTP`, `GRPC`, `WEBSOCKET` |
| 框架集成 | `CELERY`, `DRAMATIQ`, `HUEY`, `RQ`, `NAMEKO`, `KOMBU` |
| 特殊 | `MYSQL_CDC`（Binlog 事件驱动）, `WATCHDOG`（文件监控）, `EMPTY` |

### Redis 模式选型

| 模式 | 适用 |
|------|------|
| `REDIS` | 简单队列，允许丢数据 |
| `REDIS_ACK_ABLE` | **大部分场景推荐**，消费确认 |
| `REDIS_STREAM` | 消费者组、消息回溯 |

### Broker 扩展
- **`register_custom_broker`** — 注册全新中间件（`contrib/register_custom_broker_contrib/`）
- **`consumer_override_cls` / `publisher_override_cls`** — Mixin 混入定制现有 broker
- 详见 @funboost/md_for_ai/如何扩展增加新的中间件.md

---

## 五、扩展模块（Contrib）

| 类别 | 模块 | 说明 |
|------|------|------|
| Mixin 扩展 | `CircuitBreakerConsumerMixin` | 熔断器 |
| | `MicroBatchConsumerMixin` | 微批消费 |
| | `PrometheusConsumerMixin` | Prometheus 指标 |
| | `AutoOtelPublisherMixin` / `AutoOtelConsumerMixin` | OpenTelemetry 链路追踪 |
| | `PeriodicQuotaConsumerMixin` | 周期额度限制 |
| | `AlertNotifierConsumerMixin` | 异常告警通知 |
| 爬虫 | `contrib/funspider/` | httpx + SQLModel 爬虫辅助（`SimpleSpiderClient` / `AsyncSpiderClient` / `SpiderItem`） |
| CDC | `contrib/cdc/mysql2mysql.py` | MySQL Binlog → MySQL 同步 |

---

## 六、测试体系

| 项 | 说明 |
|------|------|
| **AI 写测试的位置** | 写入 `tests/ai_codes/` 下，可建子文件夹，文件名随意 |
| **AI写 回归测试** | 回归测试，放在 `tests/ai_codes/regression_testing/` 下 |
| **人工测试** | `test_frame/`（127 个子目录），AI 不用管 |
| **框架** | 无 pytest / CI，所有测试都是独立 `.py` 脚本 |
| **AI 运行测试** | 必须用 `subprocess.run(['python', 'tests/ai_codes/xxx.py'], cwd=项目根目录, timeout=30)`<br>原因：`consume()` 启动后永久循环不退出，不加 timeout 会卡死进程 |

> ⚠️ 禁止直接 `python script.py` 跑测试脚本，必须用 `subprocess.run` + `timeout` 自动终止。

---

## 七、配置机制

| 文件 | 说明 |
|------|------|
| `funboost/funboost_config_deafult.py` | 默认配置（`BrokerConnConfig` + `FunboostCommonConfig`） |
| `funboost/set_frame_config.py` | 配置加载器：首次运行自动生成 `funboost_config.py` |
| 项目根目录 `funboost_config.py` | 用户配置，覆盖默认值 |
| 项目根目录 `nb_log_config.py` | 日志配置（`nb_log` 自动生成） |

> 使用 `is_using_rpc_mode=True`、`is_using_distributed_frequency_control=True` 或 `do_task_filtering=True` 时**必须配置 Redis**

---

---

## 十、项目结构

```
funboost/
├── core/              # 核心引擎（booster.py / func_params_model.py / current_task.py）
├── consumers/         # 49 个消费者实现
├── publishers/        # 45 个发布者实现
├── factories/         # broker_kind → (Publisher, Consumer) 映射
├── concurrent_pool/   # 5 种并发池
├── workflow/          # Chain / Group / Chord
├── faas/              # FastAPI / Flask / Django 集成
├── timing_job/        # APScheduler 集成
├── contrib/           # 扩展（Mixin / 自定义 Broker / 爬虫 / CDC）
├── funweb/            # Web 管理界面（`python -m funboost.funweb.app` 启动）
└── md_for_ai/         # AI 参考文档
```

---

## 十一、给 AI 的特别提醒 for funboost

1. **`funboost_all_docs_and_codes.md` 是最高事实标准** — 生成任何代码前，先检索它
2. **禁止臆造参数名** — `BoosterParams` 的所有字段都是固定的，必须从 `md_for_ai` 中查找正确字段名
3. **禁止使用 Celery 思维** — 获取上下文用 `fct`，不要用 `self` 或 `bind=True`
5. **`push` 和 `publish` 的区别** — `push` 传业务参数，`publish` 传字典 + 框架控制参数
6. **实例方法的 push 语法特殊** — 必须写成 `ClassName.method.push(obj, args)`，第一个参数传对象实例

## 十二、 ai自己启动运行脚本的注意事项
1. **消费启动后不会自动结束** — 有两种方式运行和检查：
   - **第一种方式（CMD/PowerShell + timeout）**：AI 直接用命令行运行，靠 timeout 超时自动终止进程，**脚本里不需要手写 `os._exit`**。AI 通过检查控制台输出内容判断是否符合预期。
     - **CMD 语法**：`set PYTHONPATH=项目根目录 & cmd /c "timeout /t 30 /nobreak >nul & python script.py"`
     - **PowerShell 语法**：`$env:PYTHONPATH="项目根目录"; cmd /c "timeout /t 30 /nobreak >nul & python script.py"`
     - **timeout 时间评估**：AI 应自行评估合理时间，**一般要大于 10 秒**（框架启动需要一定时间）。根据消息个数、qps、并发数量、函数耗时预估：
       - **默认值**：`concurrent_num=50`，`qps=None`（不限制）
       - 不设置 qps：`实际吞吐量 ≈ concurrent_num / 函数耗时`
       - 设置 qps：`实际吞吐量 ≈ min(qps, concurrent_num / 函数耗时)`
       - `合理时间 ≈ 框架启动时间(5-10秒) + (消息个数 / 实际吞吐量) + 缓冲时间(2-5秒)`
       - timeout 最大不超过 50 秒。
   - **第二种方式（推荐，参考 for_ai_run_demo.py）**：脚本开头设置 `LOG_PATH`、`PRINT_WRTIE_FILE_NAME`、`SYS_STD_FILE_NAME` 三个环境变量，脚本末尾写 `time.sleep(休眠秒数); os._exit(66)` 自动退出。AI 运行后主动去读取 `D:\pythonlogs\ai_console_outs` 下生成的 print 和 std 文件来检查输出，**这种方式不需要用 subprocess.run + timeout**。
     - **运行前必须设置**：`$env:PYTHONPATH="项目根目录"`（PowerShell）或 `set PYTHONPATH=项目根目录`（CMD）
     - **重要**：每次运行时，`PRINT_WRTIE_FILE_NAME` 和 `SYS_STD_FILE_NAME` 必须设置不同的文件名后缀（如加时间戳或序号），防止 AI 读取到上一次的老日志内容。
     - **time.sleep 时间评估**：AI 应自行评估合理休眠时间，**一般要大于 10 秒**（框架启动需要一定时间）。根据消息个数、qps、并发数量、函数耗时预估：
       - **默认值**：`concurrent_num=50`，`qps=None`（不限制）
       - 不设置 qps：`实际吞吐量 ≈ concurrent_num / 函数耗时`
       - 设置 qps：`实际吞吐量 ≈ min(qps, concurrent_num / 函数耗时)`
       - `合理时间 ≈ 框架启动时间(5-10秒) + (消息个数 / 实际吞吐量) + 缓冲时间(2-5秒)`
2. **ai启动funboost任何脚本之前，一定先设置 PYTHONPATH=当前项目根目录**
   - **CMD 语法**：`set PYTHONPATH=D:\codes\funboost`
   - **PowerShell 语法**：`$env:PYTHONPATH="D:\codes\funboost"`

## 十三、 ai 新写代码位置规范
1. ai如果是被要求修改项目框架，写完后，请写单元测试/回归测试，请放在tests/ai_codes/regression_testing文件件下面，ai要运行和修改相关的测试用例
2. 如果是让ai写demo或者例子或者测试验证脚本，而不是修改项目和框架本身，ai要把代码写到 tests/ai_codes/ai_demos/ ，并且是在 ai_demos文件夹下新建合理的子文件夹，在子文件夹里面新增例子脚本。


## 十四、 ai禁止行为
1. 禁止ai flush redis，ai不要主动去清空redis。

## 十五 funboost文档仓库
D:/codes/funboost_docs/  ,文档在 source/articles 目录下