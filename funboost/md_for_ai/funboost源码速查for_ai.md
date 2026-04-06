# funboost 源码速查 for AI

> 本文档由 AI 智能分析生成，包含 funboost 核心源码的类、函数、入参及功能说明
> 
> 生成时间: 2026-04-06
> 
> 用途: 帮助 AI 快速定位代码位置，理解功能实现

---

## 目录结构

```
funboost/
├── __init__.py                 # 包入口，导出所有公共 API
├── constant.py                 # 常量定义（BrokerEnum, ConcurrentModeEnum）
├── funboost_config_deafult.py  # 默认配置
├── core/                       # 核心模块
│   ├── booster.py             # 核心装饰器 Booster 类
│   ├── func_params_model.py   # 参数模型 BoosterParams
│   ├── current_task.py        # 当前任务上下文 fct
│   ├── funboost_time.py       # 时间处理 FunboostTime
│   ├── msg_result_getter.py   # 异步结果获取 AsyncResult
│   ├── active_cousumer_info_getter.py  # 活跃消费者信息
│   └── ...
├── consumers/                  # 消费者实现
│   ├── base_consumer.py       # 消费者基类 AbstractConsumer
│   └── ...
├── publishers/                 # 发布者实现
│   ├── base_publisher.py      # 发布者基类 AbstractPublisher
│   └── ...
├── faas/                       # FaaS 微服务
│   ├── fastapi_adapter.py     # FastAPI 集成
│   ├── flask_adapter.py       # Flask 集成
│   └── ...
└── ...
```

---

## 快速开始（AI 生成代码模板）

### 最简示例

```python
from funboost import boost, BoosterParams, BrokerEnum, ctrl_c_recv

@boost(BoosterParams(queue_name="test_queue", broker_kind=BrokerEnum.MEMORY_QUEUE))
def add(x, y):
    print(f"{x} + {y} = {x + y}")
    return x + y

if __name__ == '__main__':
    # 发布任务
    add.push(1, 2)
    
    # 启动消费
    add.consume()
    ctrl_c_recv()
```

### 生产级示例

```python
import asyncio
from funboost import boost, BoosterParams, BrokerEnum, fct, ctrl_c_recv

@boost(BoosterParams(
    queue_name="production_task",
    broker_kind=BrokerEnum.REDIS_ACK_ABLE,  # 可靠消息
    qps=10,                                  # 每秒 10 次
    max_retry_times=3,                       # 失败重试 3 次
    is_using_rpc_mode=True,                  # 支持获取结果
    is_send_consumer_heartbeat_to_redis=True, # 心跳监控
))
async def process_data(user_id: str, action: str):
    """异步消费函数示例"""
    print(f"[task_id={fct.task_id}] 处理用户 {user_id} 的 {action}")
    await asyncio.sleep(1)
    return {"user_id": user_id, "status": "success"}

if __name__ == '__main__':
    # RPC 调用
    result = process_data.push("user_123", "login")
    print(f"任务ID: {result.task_id}")
    print(f"结果: {result.result}")  # 阻塞等待结果
    
    # 启动消费
    process_data.consume()
    ctrl_c_recv()
```

### 多层级爬虫示例

```python
from funboost import boost, BoosterParams, BrokerEnum, ctrl_c_recv
from boost_spider import RequestClient

# 第一层：列表页
@boost(BoosterParams(
    queue_name="list_page",
    broker_kind=BrokerEnum.REDIS_ACK_ABLE,
    qps=2,  # 列表页慢，防封
))
def crawl_list(page_num: int):
    client = RequestClient(is_change_ua_every_request=True)
    resp = client.get(f"https://example.com/list?page={page_num}")
    for url in resp.xpath('//a/@href').extract():
        crawl_detail.push(detail_url=url)  # 推送到第二层

# 第二层：详情页
@boost(BoosterParams(
    queue_name="detail_page",
    broker_kind=BrokerEnum.REDIS_ACK_ABLE,
    qps=5,  # 详情页快
))
def crawl_detail(detail_url: str):
    client = RequestClient(proxy_name_list=['kuai'])
    resp = client.get(detail_url)
    data = {
        'title': resp.xpath('//h1/text()').extract_first(),
        'url': detail_url,
    }
    print(f"抓取: {data}")
    return data

if __name__ == '__main__':
    crawl_list.consume()
    crawl_detail.consume()
    
    # 发布初始任务
    for i in range(1, 11):
        crawl_list.push(page_num=i)
    
    ctrl_c_recv()
```

---

## 一、核心装饰器与入口

### 1.1 `funboost/core/booster.py`

**文件作用**: funboost 最核心的装饰器实现，`@boost` 装饰器的本质就是 `Booster` 类。

#### 类: `Booster`

**位置**: Line 38-270+

**功能**: 将普通函数转换为分布式任务函数，集成 Consumer 和 Publisher 能力。

**核心机制**:
- `__init__`: 接收 `BoosterParams` 或字符串队列名
- `__call__`: 装饰器逻辑，第一次调用绑定消费函数，后续调用直接执行函数
- `__getstate__/__setstate__`: 支持 pickle 序列化（用于 apscheduler）

**关键属性** (装饰后函数获得):

| 属性 | 类型 | 说明 |
|------|------|------|
| `push` / `delay` | method | 发布消息（传函数参数） |
| `publish` / `pub` / `apply_async` | method | 发布消息（传字典+TaskOptions） |
| `aio_push` / `aio_publish` | method | 异步发布 |
| `consume` / `start_consuming_message` | method | 启动消费 |
| `multi_process_consume` / `mp_consume` | method | 多进程消费 |
| `pause` / `pause_consume` | method | 暂停消费 |
| `continue_consume` | method | 恢复消费 |
| `clear` / `clear_queue` | method | 清空队列 |
| `get_message_count` | method | 获取消息数量 |
| `fabric_deploy` | method | 远程部署 |

**关键方法**:

```python
def __init__(
    self,
    queue_name: Union[BoosterParams, str] = None,
    *,
    boost_params: BoosterParams = None,
    **kwargs
)

def multi_process_consume(self, process_num=1):
    """超高速多进程消费，线程/协程叠加多进程"""

def multi_process_pub_params_list(self, params_list, process_num=16):
    """多进程快速发布大量任务"""

def fabric_deploy(self, host, port, user, password, ...):
    """远程部署到服务器并启动消费"""
```

#### 类: `BoosterRegistry`

**位置**: Line 270+

**功能**: 享元模式管理所有 Booster 实例，支持按名称分组管理。

**关键方法**:

```python
def get_or_create_booster_by_queue_name(self, queue_name: str) -> Booster
    """根据队列名获取或创建 Booster"""

def get_all_boosters(self) -> List[Booster]
    """获取所有注册的 Booster"""

def consume_all(self)
    """启动所有 Booster 的消费"""

def consume_group(self, booster_group: str)
    """按分组启动消费"""
```

---

## 二、参数模型（掌握 funboost 的 90%）

### 2.1 `funboost/core/func_params_model.py`

**文件作用**: 定义所有 pydantic 参数模型，`BoosterParams` 是核心。

#### 类: `BoosterParams`

**位置**: Line 72-350+

**核心字段** (52 个):

**基础配置**:
```python
queue_name: str                              # 队列名（必填）
broker_kind: str = BrokerEnum.SQLITE_QUEUE   # 中间件类型
project_name: Optional[str] = None           # 项目名（管理分组）
```

**并发配置**:
```python
concurrent_mode: str = ConcurrentModeEnum.THREADING  # 并发模式
concurrent_num: int = 50                             # 并发数量
specify_concurrent_pool: Optional[FunboostBaseConcurrentPool] = None  # 指定线程池
specify_async_loop: Optional[asyncio.AbstractEventLoop] = None        # 指定事件循环
is_auto_start_specify_async_loop_in_child_thread: bool = True
```

**频率控制**:
```python
qps: Union[float, int, None] = None                    # QPS 限制
is_using_distributed_frequency_control: bool = False   # 分布式控频
```

**重试配置**:
```python
max_retry_times: int = 3                    # 最大重试次数
is_using_advanced_retry: bool = False       # 高级重试（指数退避）
advanced_retry_config: dict = {             # 高级重试配置
    'retry_mode': 'sleep',                  # 'sleep' 或 'requeue'
    'retry_base_interval': 1.0,             # 基础间隔
    'retry_multiplier': 2.0,                # 退避倍数
    'retry_max_interval': 60.0,             # 最大间隔
    'retry_jitter': False,                  # 随机抖动
}
is_push_to_dlx_queue_when_retry_max_times: bool = False  # 死信队列
```

**超时与监控**:
```python
function_timeout: Union[int, float, None] = None     # 函数超时
is_support_remote_kill_task: bool = False            # 远程杀死任务
is_send_consumer_heartbeat_to_redis: bool = False    # 发送心跳
```

**日志配置**:
```python
log_level: int = logging.DEBUG
logger_prefix: str = ''
create_logger_file: bool = True
logger_name: Union[str, None] = ''
log_filename: Union[str, None] = None
is_show_message_get_from_broker: bool = False
is_print_detail_exception: bool = True
```

**消息控制**:
```python
msg_expire_seconds: Union[float, int, None] = None   # 消息过期时间
do_task_filtering: bool = False                      # 任务去重
task_filtering_expire_seconds: int = 0               # 去重过期时间
```

**RPC 模式**:
```python
is_using_rpc_mode: bool = False              # 启用 RPC
rpc_result_expire_seconds: int = 1800        # RPC 结果过期时间
rpc_timeout: int = 1800                      # RPC 超时时间
```

**定时任务**:
```python
delay_task_apscheduler_jobstores_kind: str = 'redis'  # 定时任务存储
allow_run_time_cron: Optional[str] = None             # 允许运行时间
```

**启动控制**:
```python
schedule_tasks_on_main_thread: bool = False
is_auto_start_consuming_message: bool = False
booster_group: Union[str, None] = None       # 消费分组
```

**中间件专属配置**:
```python
broker_exclusive_config: dict = {}           # 各中间件特有配置
```

**自定义扩展**:
```python
user_options: dict = {}                      # 用户自定义配置
consumer_override_cls: Optional[Type] = None     # 自定义消费者
publisher_override_cls: Optional[Type] = None    # 自定义发布者
```

#### 类: `FunctionResultStatusPersistanceConfig`

**功能**: 函数执行结果持久化配置

```python
is_save_status: bool = False                 # 保存运行状态
is_save_result: bool = False                 # 保存运行结果
expire_seconds: int = 7 * 24 * 3600          # 过期时间
is_use_bulk_insert: bool = False             # 批量插入
table_name: Optional[str] = None             # 表名
```

#### 类: `TaskOptions`

**功能**: 单次任务的优先级配置

```python
class TaskOptions(BaseModel):
    task_id: Optional[str] = None
    publish_time: Optional[float] = None
    max_retry_times: Optional[int] = None
    is_using_rpc_mode: Optional[bool] = None
    rpc_timeout: Optional[int] = None
    priority: Optional[int] = None             # 消息优先级
    filter_str: Optional[str] = None           # 去重指纹
    do_task_filtering: Optional[bool] = None
```

---

## 三、常量定义

### 3.1 `funboost/constant.py`

**文件作用**: 定义所有枚举常量。

#### 类: `BrokerEnum`

**位置**: Line 11-300+

**50 种消息队列中间件**:

**正经 MQ**:
- `RABBITMQ_AMQPSTORM` / `RABBITMQ` - RabbitMQ（推荐）
- `RABBITMQ_COMPLEX_ROUTING` - RabbitMQ 复杂路由
- `REDIS` - Redis List（高性能，不保证）
- `REDIS_ACK_ABLE` - Redis List + ACK（推荐）
- `REDIS_STREAM` - Redis Stream
- `KAFKA` / `KAFKA_CONFLUENT` - Kafka
- `ROCKETMQ` / `ROCKETMQ5` - RocketMQ
- `PULSAR` - Apache Pulsar
- `NSQ` - NSQ
- `MQTT` - MQTT

**内存/文件**:
- `MEMORY_QUEUE` - Python queue.Queue（超一等公民）
- `FASTEST_MEM_QUEUE` - collections.deque（更快）
- `SQLITE_QUEUE` / `PERSISTQUEUE` - SQLite 持久化
- `TXT_FILE` - 文本文件

**数据库**:
- `MONGOMQ` - MongoDB
- `SQLACHEMY` - SQLAlchemy（MySQL/Oracle/SQLServer）
- `POSTGRES` - PostgreSQL（原生 LISTEN/NOTIFY）
- `PEEWEE` - Peewee ORM

**Socket/协议**:
- `TCP` / `UDP` / `HTTP` / `GRPC` / `WEBSOCKET`
- `ZEROMQ` - ZeroMQ
- `NATS` - NATS

**其他框架**:
- `CELERY` - Celery 作为 broker
- `DRAMATIQ` - Dramatiq 作为 broker
- `HUEY` - Huey 作为 broker
- `RQ` - RQ 作为 broker
- `NAMEKO` - Nameko 微服务
- `KOMBU` - Kombu（Celery 底层）

**特殊**:
- `MYSQL_CDC` - MySQL binlog CDC
- `WATCHDOG` - 文件系统监控
- `SQS` - AWS SQS
- `EMPTY` - 空实现（自定义扩展）

#### 类: `ConcurrentModeEnum`

```python
THREADING = 'threading'          # 多线程
GEVENT = 'gevent'                # Gevent 协程
EVENTLET = 'eventlet'            # Eventlet 协程
ASYNC = 'async'                  # asyncio
SINGLE_THREAD = 'single_thread'  # 单线程
```

---

## 四、消费者基类

### 4.1 `funboost/consumers/base_consumer.py`

**文件作用**: 所有消费者的抽象基类，实现 20+ 种运行控制。

#### 类: `AbstractConsumer`

**位置**: Line 101-1400+

**核心功能**:
- 消息获取与分发
- QPS 控频
- 重试机制（含高级指数退避）
- 超时控制
- 分布式统计
- 定时任务调度

**关键方法**:

```python
def start_consuming_message(self)
    """启动消费（非阻塞）"""

def _submit_task(self, msg: dict)
    """提交任务到并发池，核心调度方法"""

def pause_consume(self)
    """暂停消费（从 Redis 读取标志）"""

def continue_consume(self)
    """恢复消费"""

def wait_for_possible_has_finish_all_tasks(self, minutes: int = 3)
    """等待所有任务完成"""

def clear_filter_tasks(self)
    """清空任务过滤器"""
```

**关键属性**:

```python
publisher_of_same_queue: AbstractPublisher      # 同队列发布者
publisher_of_dlx_queue: AbstractPublisher       # 死信队列发布者
concurrent_pool: Any                             # 并发池
```

#### 类: `ConcurrentModeDispatcher`

**位置**: Line 1298+

**功能**: 根据 `concurrent_mode` 构建对应的并发池。

#### 类: `DistributedConsumerStatistics`

**位置**: Line 1495+

**功能**: 分布式消费者统计，用于：
1. 分布式 QPS 控频（统计活跃消费者数量）
2. 检测掉线消费者（心跳超时）
3. 远程暂停/恢复消费

---

## 五、发布者基类

### 5.1 `funboost/publishers/base_publisher.py`

**文件作用**: 所有发布者的抽象基类。

#### 类: `AbstractPublisher`

**位置**: Line 51-420+

**核心功能**:
- 消息发布（同步/异步）
- 消息序列化
- 参数校验
- RPC 结果存储

**关键方法**:

```python
def publish(
    self,
    msg: Union[str, dict],
    task_id=None,
    task_options: TaskOptions = None
) -> AsyncResult
    """发布消息，返回 AsyncResult 用于 RPC"""

def push(self, *func_args, **func_kwargs) -> AsyncResult
    """简化发布，直接传函数参数"""

def aio_publish(self, msg, task_id=None, task_options=None) -> AioAsyncResult
    """异步发布"""

def aio_push(self, *func_args, **func_kwargs) -> AioAsyncResult
    """异步简化发布"""

def clear(self)
    """清空队列"""

def get_message_count(self) -> int
    """获取消息数量"""
```

---

## 六、异步结果获取

### 6.1 `funboost/core/msg_result_getter.py`

**文件作用**: RPC 模式下获取消费结果。

#### 类: `AsyncResult`

**位置**: Line 46-148

**功能**: 同步方式获取 RPC 结果（基于 Redis）。

```python
def __init__(self, task_id, timeout=1800)

def get(self) -> Any
    """获取结果（阻塞等待）"""

def is_success(self) -> bool
    """是否成功"""

def is_pending(self) -> bool
    """是否还在执行"""

def set_callback(self, callback_func: Callable)
    """设置回调函数"""

def wait_rpc_data_or_raise(self) -> FunctionResultStatus
    """等待结果或抛出异常"""

@property
def result(self) -> Any
    """结果属性（阻塞获取）"""

@property
def status_and_result(self) -> dict
    """状态和结果字典"""
```

#### 类: `AioAsyncResult`

**位置**: Line 149-253

**功能**: 异步方式获取 RPC 结果。

```python
async def get(self) -> Any
async def is_success(self) -> bool
async def is_pending(self) -> bool
```

---

## 七、当前任务上下文

### 7.1 `funboost/core/current_task.py`

**文件作用**: 在消费函数内部获取当前任务信息。

#### 类: `FctContext`

```python
function_result_status: FunctionResultStatus
logger: logging.Logger
```

#### 类: `_FctProxy`

**功能**: 代理类，自动获取当前线程/协程的上下文。

```python
@property
def task_id(self) -> str                    # 当前任务 ID
@property
def queue_name(self) -> str                 # 队列名
@property
def function_result_status(self) -> FunctionResultStatus  # 完整状态
@property
def run_times(self) -> int                  # 运行次数（重试计数）
@property
def full_msg(self) -> dict                  # 完整消息
@property
def function_params(self) -> dict           # 函数参数
@property
def logger(self) -> logging.Logger          # 当前任务 logger
```

#### 全局实例: `fct`

```python
from funboost import fct

@boost(BoosterParams(queue_name="test"))
def my_task(x, y):
    print(fct.task_id)          # 获取当前任务 ID
    print(fct.run_times)        # 第几次执行（含重试）
    print(fct.full_msg)         # 完整消息体
```

---

## 八、FaaS 微服务

### 8.1 `funboost/faas/fastapi_adapter.py`

**文件作用**: FastAPI 集成，将消费函数暴露为 HTTP 接口。

#### 对象: `fastapi_router`

**类型**: `APIRouter(prefix='/funboost', tags=['funboost'])`

**提供的 HTTP 接口**:

| 方法 | 路径 | 功能 |
|------|------|------|
| POST | `/publish` | 发布消息（支持 RPC） |
| GET | `/get_result` | 根据 task_id 获取结果 |
| GET | `/get_msg_count` | 获取队列消息数量 |
| POST | `/clear_queue` | 清空队列 |
| POST | `/pause_consume` | 暂停消费 |
| POST | `/resume_consume` | 恢复消费 |
| GET | `/get_all_queues` | 获取所有队列 |
| GET | `/get_queues_config` | 获取队列配置（含入参信息） |
| GET | `/get_queue_run_info` | 获取队列运行信息 |
| GET | `/get_all_queue_run_info` | 获取所有队列运行信息 |
| POST | `/add_timing_job` | 添加定时任务 |
| GET | `/get_timing_jobs` | 获取定时任务列表 |
| DELETE | `/delete_timing_job` | 删除定时任务 |
| POST | `/pause_timing_job` | 暂停定时任务 |
| POST | `/resume_timing_job` | 恢复定时任务 |
| POST | `/deprecate_queue` | 废弃队列 |

**使用方式**:

```python
from fastapi import FastAPI
from funboost.faas import fastapi_router

app = FastAPI()
app.include_router(fastapi_router)
# 访问 http://localhost:8000/docs 查看 Swagger 文档
```

---

## 九、活跃消费者信息

### 9.1 `funboost/core/active_cousumer_info_getter.py`

**文件作用**: 获取分布式环境中的消费者信息，用于监控面板。

#### 类: `ActiveCousumerProcessInfoGetter`

```python
def get_all_hearbeat_info_by_queue_name(self, queue_name) -> List[Dict]
    """根据队列名获取活跃消费者"""

def get_all_hearbeat_info_by_ip(self, ip=None) -> List[Dict]
    """根据 IP 获取消费者"""

def get_all_ips(self) -> List[str]
    """获取所有 IP"""
```

#### 类: `QueuesConusmerParamsGetter`

```python
def get_all_queue_names(self) -> List[str]
    """获取所有队列名"""

def get_queues_params(self) -> Dict[str, Dict]
    """获取所有队列配置"""

def get_queues_params_and_active_consumers(self) -> Dict
    """获取队列配置和活跃消费者"""
```

#### 类: `SingleQueueConusmerParamsGetter`

```python
def __init__(self, queue_name: str, ...)

def get_one_queue_params(self) -> Dict
    """获取单个队列配置"""

def gen_publisher_for_faas(self) -> AbstractPublisher
    """为 FaaS 生成发布者"""

def gen_booster_for_faas(self) -> Booster
    """为 FaaS 生成 Booster"""

def generate_aps_job_adder(self, job_store_kind='redis') -> ApsJobAdder
    """生成定时任务添加器"""
```

---

## 十、定时任务

### 10.1 `funboost/timing_job/timing_push.py`

**文件作用**: 基于 APScheduler 的定时任务。

#### 类: `ApsJobAdder`

```python
def __init__(
    self,
    booster: Booster,
    job_store_kind: str = 'redis',      # 'redis' 或 'memory'
    is_auto_start: bool = True,
    is_auto_paused: bool = True
)

def add_push_job(
    self,
    trigger: str,                       # 'date', 'interval', 'cron'
    args: List = None,                  # 位置参数
    kwargs: Dict = None,                # 关键字参数
    id: str = None,                     # 任务 ID
    replace_existing: bool = False,
    **trigger_args
) -> Job
    """添加定时推送任务"""

# trigger_args 根据 trigger 类型不同:
# date: run_date='2024-06-12 10:00:00'
# interval: seconds=10, minutes=5, hours=1
# cron: hour='*/2', minute='30', day_of_week='mon-fri'
```

---

## 十一、自定义 Broker 扩展

### 11.1 `funboost/factories/broker_kind__publsiher_consumer_type_map.py`

**文件作用**: 注册自定义 broker。

```python
def register_custom_broker(
    broker_kind: str,
    consumer_class: Type[AbstractConsumer],
    publisher_class: Type[AbstractPublisher]
)
    """注册自定义 broker 类型"""
```

### 11.2 自定义示例

```python
from funboost import register_custom_broker
from funboost.consumers.base_consumer import AbstractConsumer
from funboost.publishers.base_publisher import AbstractPublisher

class MyConsumer(AbstractConsumer):
    def start_consuming_message(self):
        # 实现消息获取逻辑
        while True:
            msg = self._get_msg_from_my_broker()
            self._submit_task(msg)
    
    def clear(self): ...
    def get_message_count(self) -> int: ...
    def close(self): ...

class MyPublisher(AbstractPublisher):
    def send_msg(self, msg):
        # 实现消息发送逻辑
        self._send_to_my_broker(msg)
    
    def clear(self): ...
    def get_message_count(self) -> int: ...
    def close(self): ...

register_custom_broker('MY_BROKER', MyConsumer, MyPublisher)

# 使用
@boost(BoosterParams(queue_name="test", broker_kind='MY_BROKER'))
def my_task(x): ...
```

---

## 十二、时间处理

### 12.1 `funboost/core/funboost_time.py`

**文件作用**: 基于 nb_time 的时间处理。

#### 类: `FunboostTime` (继承 `NbTime`)

```python
class FunboostTime(NbTime):
    default_formatter = NbTime.FORMATTER_DATETIME_NO_ZONE
    
    def get_time_zone_str(self, time_zone=None):
        # 优先从 FunboostCommonConfig.TIMEZONE 读取
        return time_zone or self.default_time_zone or FunboostCommonConfig.TIMEZONE
    
    def get_str_fast(self):
        # 快速格式化（字符串拼接，比 strftime 快）
```

#### 函数: `fast_get_now_time_str`

```python
def fast_get_now_time_str() -> str:
    """获取当前时间字符串（缓存优化，百万次 0.4 秒）"""
    return NowTimeStrCache.fast_get_now_time_str(FunboostCommonConfig.TIMEZONE)
```

---

## 十三、包入口导出

### 13.1 `funboost/__init__.py`

**导出列表**:

```python
# 核心装饰器
from funboost.core.booster import boost, Booster, BoostersManager

# 参数模型
from funboost.core.func_params_model import (
    BoosterParams, 
    FunctionResultStatusPersistanceConfig,
    TaskOptions, 
    PublisherParams
)

# 常量
from funboost.constant import BrokerEnum, ConcurrentModeEnum

# 消费者/发布者基类
from funboost.consumers.base_consumer import AbstractConsumer
from funboost.publishers.base_publisher import AbstractPublisher, AsyncResult, AioAsyncResult

# 结果获取
from funboost.core.msg_result_getter import HasNotAsyncResult, ResultFromMongo

# 当前任务上下文
from funboost.core.current_task import funboost_current_task, fct, get_current_taskid

# 定时任务
from funboost.timing_job.timing_push import ApsJobAdder

# 工具函数
from funboost.utils.ctrl_c_end import ctrl_c_recv
from funboost.utils.redis_manager import RedisMixin

# 自定义 broker 注册
from funboost.factories.broker_kind__publsiher_consumer_type_map import register_custom_broker

# 异常
from funboost.core.exceptions import (
    ExceptionForRetry, 
    ExceptionForRequeue, 
    ExceptionForPushToDlxqueue
)
```

---

## 十四、所有 Broker 消费者实现对照表

### 14.1 消费者文件映射

| BrokerEnum | 消费者类 | 文件路径 | 说明 |
|------------|---------|----------|------|
| `MEMORY_QUEUE` | `LocalPythonQueueConsumer` | `consumers/local_python_queue_consumer.py` | Python queue.Queue |
| `FASTEST_MEM_QUEUE` | `FastestMemQueueConsumer` | `consumers/fastest_mem_queue_consumer.py` | collections.deque |
| `REDIS` | `RedisConsumer` | `consumers/redis_consumer.py` | Redis List（无ACK） |
| `REDIS_ACK_ABLE` | `RedisConsumerAckAble` | `consumers/redis_consumer_ack_able.py` | Redis List + ZSet（有ACK） |
| `REDIS_STREAM` | `RedisStreamConsumer` | `consumers/redis_stream_consumer.py` | Redis Stream |
| `REDIS_PRIORITY` | `RedisPriorityConsumer` | `consumers/redis_consumer_priority.py` | Redis 优先级队列 |
| `REDIS_BRPOP_LPUSH` | `RedisBrpopLpushConsumer` | `consumers/redis_brpoplpush_consumer.py` | Redis 双队列 |
| `REDIS_PUBSUB` | `RedisPubSubConsumer` | `consumers/redis_pubsub_consumer.py` | Redis 发布订阅 |
| `RABBITMQ` | `RabbitmqConsumer` | `consumers/rabbitmq_amqpstorm_consumer.py` | RabbitMQ（推荐） |
| `RABBITMQ_COMPLEX_ROUTING` | `RabbitmqComplexRoutingConsumer` | `consumers/rabbitmq_complex_routing_consumer.py` | RabbitMQ 复杂路由 |
| `KAFKA` | `KafkaConsumer` | `consumers/kafka_consumer.py` | Kafka（自动提交） |
| `KAFKA_CONFLUENT` | `KafkaConfluentConsumer` | `consumers/kafka_consumer_manually_commit.py` | Kafka（手动提交） |
| `ROCKETMQ` | `RocketmqConsumer` | `consumers/rocketmq_consumer.py` | RocketMQ |
| `ROCKETMQ5` | `Rocketmq5Consumer` | `consumers/rocketmq5_consumer.py` | RocketMQ 5.x |
| `PULSAR` | `PulsarConsumer` | `consumers/pulsar_consumer.py` | Apache Pulsar |
| `NSQ` | `NsqConsumer` | `consumers/nsq_consumer.py` | NSQ |
| `MQTT` | `MqttConsumer` | `consumers/mqtt_consumer.py` | MQTT |
| `NATS` | `NatsConsumer` | `consumers/nats_consumer.py` | NATS |
| `ZEROMQ` | `ZeromqConsumer` | `consumers/zeromq_consumer.py` | ZeroMQ |
| `TCP` | `TcpConsumer` | `consumers/tcp_consumer.py` | TCP Socket |
| `UDP` | `UdpConsumer` | `consumers/udp_consumer.py` | UDP Socket |
| `HTTP` | `HttpConsumer` | `consumers/http_consumer.py` | HTTP 协议 |
| `GRPC` | `GrpcConsumer` | `consumers/grpc_consumer.py` | gRPC |
| `SQLITE_QUEUE` | `PersistQueueConsumer` | `consumers/persist_queue_consumer.py` | SQLite 持久化 |
| `MONGOMQ` | `MongoMqConsumer` | `consumers/mongomq_consumer.py` | MongoDB |
| `SQLACHEMY` | `SqlachemyConsumer` | `consumers/sqlachemy_consumer.py` | SQLAlchemy |
| `POSTGRES` | `PostgresConsumer` | `consumers/postgres_consumer.py` | PostgreSQL |
| `PEEWEE` | `PeeweeConsumer` | `consumers/peewee_conusmer.py` | Peewee ORM |
| `TXT_FILE` | `TxtFileConsumer` | `consumers/txt_file_consumer.py` | 文本文件 |
| `HTTPSQS` | `HttpsqsConsumer` | `consumers/httpsqs_consumer.py` | HTTPSQS |
| `SQS` | `SqsConsumer` | `consumers/sqs_consumer.py` | AWS SQS |
| `CELERY` | `CeleryConsumer` | `consumers/celery_consumer.py` | Celery 框架 |
| `DRAMATIQ` | `DramatiqConsumer` | `consumers/dramatiq_consumer.py` | Dramatiq 框架 |
| `HUEY` | `HueyConsumer` | `consumers/huey_consumer.py` | Huey 框架 |
| `RQ` | `RqConsumer` | `consumers/rq_consumer.py` | RQ 框架 |
| `NAMEKO` | `NamekoConsumer` | `consumers/nameko_consumer.py` | Nameko 微服务 |
| `KOMBU` | `KombuConsumer` | `consumers/kombu_consumer.py` | Kombu |
| `MYSQL_CDC` | `MySqlCdcConsumer` | `consumers/mysql_cdc_consumer.py` | MySQL CDC |
| `WATCHDOG` | (contrib) | `contrib/register_custom_broker_contrib/watchdog_broker.py` | 文件监控 |
| `WEBSOCKET` | (contrib) | `contrib/register_custom_broker_contrib/websocket_broker.py` | WebSocket |
| `EMPTY` | `EmptyConsumer` | `consumers/empty_consumer.py` | 空实现（自定义） |

### 14.2 发布者文件映射（对应消费者）

| BrokerEnum | 发布者类 | 文件路径 |
|------------|---------|----------|
| `MEMORY_QUEUE` | `LocalPythonQueuePublisher` | `publishers/local_python_queue_publisher.py` |
| `REDIS` / `REDIS_ACK_ABLE` | `RedisPublisher` | `publishers/redis_publisher.py` |
| `RABBITMQ` | `RabbitmqPublisher` | `publishers/rabbitmq_amqpstorm_publisher.py` |
| `KAFKA` | `KafkaPublisher` | `publishers/kafka_publisher.py` |
| `SQLITE_QUEUE` | `PersistQueuePublisher` | `publishers/persist_queue_publisher.py` |
| ... | ... | ... |

**规律**: 发布者文件路径和消费者对应，`_consumer.py` 替换为 `_publisher.py`

### 14.3 关键消费者实现详解

#### `RedisConsumerAckAble` - 可靠的 Redis 消费者

**文件**: `consumers/redis_consumer_ack_able.py`

**核心机制**:
- 使用 Redis List + ZSet 实现 ACK
- 消息取出时同时放入 `unack_zset`，带时间戳
- 心跳检测过期未确认的消息，自动重回队列
- Lua 脚本保证原子性

**关键代码**:
```python
lua = '''
local task_list = redis.call("lrange", KEYS[1],0,N)
redis.call("ltrim", KEYS[1],N,-1)
if (#task_list > 0) then
    for task_index,task_value in ipairs(task_list)
    do
        redis.call('zadd',KEYS[2],ARGV[1],task_value)  -- 加入unack
    end
    return task_list
end
'''
```

#### `KafkaConsumer` vs `KafkaConfluentConsumer`

| 特性 | `KafkaConsumer` | `KafkaConfluentConsumer` |
|------|-----------------|-------------------------|
| 文件 | `kafka_consumer.py` | `kafka_consumer_manually_commit.py` |
| 客户端 | kafka-python | confluent-kafka |
| 性能 | 一般 | 高 10 倍 |
| 提交模式 | 自动提交 | 手动提交 |
| 可靠性 | 最多一次 | 至少一次 |
| 适用场景 | 高并发、可丢消息 | 高可靠、不可丢消息 |

#### `LocalPythonQueueConsumer` - 内存队列消费者

**文件**: `consumers/local_python_queue_consumer.py`

**超一等公民地位**:
- 不进行序列化/反序列化，支持任意类型参数
- 可当做超级装饰器使用（并发+重试+控频+超时）
- 支持 RPC 结果获取（不依赖 Redis）
- 同进程共享，性能最高

---

## 十五、并发池实现

### 15.1 并发池文件映射

| 并发模式 | 类 | 文件 | 说明 |
|---------|-----|------|------|
| Threading | `FlexibleThreadPool` | `concurrent_pool/flexible_thread_pool.py` | 弹性线程池（推荐） |
| Threading | `ThreadPoolExecutorShrinkAble` | `concurrent_pool/custom_threadpool_executor.py` | 可收缩线程池 |
| Threading | `FixedThreadPool` | `concurrent_pool/fixed_thread_pool.py` | 固定线程池 |
| Gevent | `GeventPoolExecutor` | `concurrent_pool/custom_gevent_pool_executor.py` | Gevent 协程池 |
| Eventlet | `EvenletPoolExecutor` | `concurrent_pool/custom_evenlet_pool_executor.py` | Eventlet 协程池 |
| Asyncio | `AsyncPoolExecutor` | `concurrent_pool/async_pool_executor.py` | Asyncio 协程池 |
| Single Thread | `SingleThreadExecutor` | `concurrent_pool/single_thread_executor.py` | 单线程 |

### 15.2 `FlexibleThreadPool` - 弹性线程池

**文件**: `concurrent_pool/flexible_thread_pool.py`

**核心特性**:
- 自适应伸缩：任务多自动扩容，空闲自动缩容
- 支持同步和 async def 函数混合执行
- 无返回值设计，性能比标准库高 200%
- 线程空闲 10 秒自动退出

**关键参数**:
```python
class FlexibleThreadPool:
    KEEP_ALIVE_TIME = 10      # 线程空闲存活时间（秒）
    MIN_WORKERS = 1           # 最小线程数
    
    def __init__(self, max_workers: int = None, work_queue_maxsize=10)
```

**自适应逻辑**:
```python
# 提交任务时判断
if self.threads_free_count <= MIN_WORKERS and self._threads_num < max_workers:
    启动新线程()

# 线程空闲时判断
if 超过 KEEP_ALIVE_TIME 秒无任务 and threads_free_count > MIN_WORKERS:
    退出当前线程()
```

---

## 十六、Contrib 扩展模块

### 16.1 扩展功能列表

| 功能 | 文件路径 | 说明 |
|------|---------|------|
| **微批消费** | `contrib/override_publisher_consumer_cls/funboost_micro_batch_mixin.py` | 批量聚合消费 |
| **熔断器** | `contrib/override_publisher_consumer_cls/circuit_breaker_mixin.py` | 失败率熔断 |
| **周期额度** | `contrib/override_publisher_consumer_cls/periodic_quota_mixin.py` | 周期次数限制 |
| **Prometheus** | `contrib/override_publisher_consumer_cls/funboost_promethus_mixin.py` | 指标监控 |
| **OpenTelemetry** | `contrib/override_publisher_consumer_cls/funboost_otel_mixin.py` | 链路追踪 |
| **告警通知** | `contrib/override_publisher_consumer_cls/alert_notifier_mixin.py` | 异常告警 |
| **CDC MySQL** | `contrib/cdc/mysql2mysql.py` | MySQL 数据同步 |
| **队列转发** | `contrib/queue2queue.py` | 队列间消息转发 |
| **Django DB** | `contrib/django_db_deco.py` | Django 数据库兼容 |
| **Watchdog** | `contrib/register_custom_broker_contrib/watchdog_broker.py` | 文件监控 Broker |
| **WebSocket** | `contrib/register_custom_broker_contrib/websocket_broker.py` | WebSocket Broker |

### 16.2 微批消费 Mixin

**文件**: `contrib/override_publisher_consumer_cls/funboost_micro_batch_mixin.py`

**使用方式**:
```python
from funboost.contrib.override_publisher_consumer_cls.funboost_micro_batch_mixin import (
    MicroBatchConsumerMixin, MicroBatchBoosterParams
)

@boost(MicroBatchBoosterParams(
    queue_name='batch_queue',
    user_options={
        'micro_batch_size': 10,      # 凑满10条触发
        'micro_batch_timeout': 3.0,  # 或3秒超时触发
    }
))
def batch_insert(items: list):  # 注意：入参是 list
    print(f"批量处理 {len(items)} 条")
```

### 16.3 周期额度 Mixin

**文件**: `contrib/override_publisher_consumer_cls/periodic_quota_mixin.py`

**功能**: 在指定周期内限制执行次数，不同于 QPS 控频。

```python
# 场景：每天只能调用 ChatGPT API 24 次，不是均匀分布，而是一次用完
user_options={
    'periodic_quota_config': {
        'quota': 24,
        'period_seconds': 86400,  # 24小时
    }
}
```

---

## 十七、快速检索索引

### 按功能检索

| 功能 | 文件 | 类/函数 |
|------|------|---------|
| 装饰器核心 | `core/booster.py` | `Booster` |
| 参数配置 | `core/func_params_model.py` | `BoosterParams` |
| 消费者基类 | `consumers/base_consumer.py` | `AbstractConsumer` |
| 发布者基类 | `publishers/base_publisher.py` | `AbstractPublisher` |
| RPC 结果 | `core/msg_result_getter.py` | `AsyncResult`, `AioAsyncResult` |
| 任务上下文 | `core/current_task.py` | `fct` |
| 定时任务 | `timing_job/timing_push.py` | `ApsJobAdder` |
| FaaS FastAPI | `faas/fastapi_adapter.py` | `fastapi_router` |
| 消费者信息 | `core/active_cousumer_info_getter.py` | `SingleQueueConusmerParamsGetter` |
| 自定义 broker | `factories/broker_kind__publsiher_consumer_type_map.py` | `register_custom_broker` |
| 时间处理 | `core/funboost_time.py` | `FunboostTime` |
| 常量 | `constant.py` | `BrokerEnum`, `ConcurrentModeEnum` |
| 弹性线程池 | `concurrent_pool/flexible_thread_pool.py` | `FlexibleThreadPool` |
| Redis ACK | `consumers/redis_consumer_ack_able.py` | `RedisConsumerAckAble` |
| Kafka | `consumers/kafka_consumer.py` | `KafkaConsumer` |
| 微批消费 | `contrib/override_publisher_consumer_cls/funboost_micro_batch_mixin.py` | `MicroBatchConsumerMixin` |

### 按问题检索

**Q: 怎么实现分布式控频？**
→ `BoosterParams.is_using_distributed_frequency_control = True`
→ `consumers/base_consumer.py: DistributedConsumerStatistics`

**Q: 怎么自定义 broker？**
→ `factories/broker_kind__publsiher_consumer_type_map.py: register_custom_broker()`
→ 继承 `AbstractConsumer` + `AbstractPublisher`

**Q: 怎么获取 RPC 结果？**
→ `publishers/base_publisher.py: AbstractPublisher.publish()` 返回 `AsyncResult`
→ `core/msg_result_getter.py: AsyncResult.result`

**Q: 怎么在函数内获取任务 ID？**
→ `from funboost import fct`
→ `fct.task_id`

**Q: 怎么启动 FaaS？**
→ `from funboost.faas import fastapi_router`
→ `app.include_router(fastapi_router)`

---

## 十八、版本兼容性说明

### 18.1 重要版本变更

**v40.0+ 重大变更**:
- 强烈推荐使用 `BoosterParams` 传参，旧方式（直接在 `@boost` 传参）仍然兼容但会警告
- `BoostersManager` 更名为 `BoosterRegistry`（旧名称仍兼容）
- 新增 `booster_group` 参数替代部分 `BoostersManager` 功能

**当前版本**: `__version__ = "54.8"` (from `funboost/__init__.py`)

### 18.2 新旧写法对比

| 功能 | 旧写法（仍兼容） | 新写法（推荐） |
|------|----------------|---------------|
| 装饰器 | `@boost('queue', qps=0.5)` | `@boost(BoosterParams(queue_name='queue', qps=0.5))` |
| 管理器 | `BoostersManager` | `BoosterRegistry` |
| 分组启动 | `BoostersManager.consume_group('g1')` | `BoosterRegistry('default').consume_group('g1')` |

---

## 十九、AI 编程铁律（必须遵守）

### 19.1 代码生成规则

**Rule 1: 永远使用 BoosterParams 传参**
```python
# ✅ 正确
@boost(BoosterParams(queue_name='test', qps=0.5))
def my_task(x, y): ...

# ❌ 错误（兼容但绝不推荐）
@boost('test', qps=0.5)
def my_task(x, y): ...
```

**Rule 2: 发布消息用 push，不要用 publish（除非需要 TaskOptions）**
```python
# ✅ 简单场景
my_task.push(1, 2)

# ✅ 需要指定 task_id 或 RPC
my_task.publish({'x': 1, 'y': 2}, task_id='xxx', task_options=TaskOptions(is_using_rpc_mode=True))
```

**Rule 3: 不要在消费函数上叠加装饰器（除非在 BoosterParams 中指定）**
```python
# ❌ 错误 - 会破坏参数解析
@my_decorator
@boost(BoosterParams(queue_name='test'))
def my_task(x, y): ...

# ✅ 正确 - 通过 BoosterParams 指定装饰器
@boost(BoosterParams(queue_name='test', consuming_function_decorator=my_decorator))
def my_task(x, y): ...
```

**Rule 4: 获取当前任务信息必须用 fct，不要用其他方式**
```python
from funboost import fct

@boost(BoosterParams(queue_name='test'))
def my_task(x, y):
    # ✅ 正确
    print(fct.task_id)
    print(fct.run_times)
    
    # ❌ 错误 - 不要自己传参或全局变量
    print(threading.current_thread().name)  # 不可靠
```

**Rule 5: 多进程消费用 mp_consume，不要自己写 Process**
```python
# ✅ 正确
my_task.mp_consume(8)

# ❌ 错误 - 不要自己管理进程
for i in range(8):
    Process(target=my_task.consume).start()
```

### 19.2 常见错误避免

| 错误 | 原因 | 正确做法 |
|------|------|---------|
| `AttributeError: 'function' has no attribute 'push'` | 装饰器没生效，函数还是普通函数 | 检查 `@boost` 是否在函数定义正上方，中间没有其他装饰器 |
| `NotRegistered: Queue not found` | 队列名拼写错误或消费者未启动 | 检查队列名一致性，先启动 consume 再发布 |
| `RPC timeout` | RPC 结果过期或消费端未启动 | 检查 `rpc_result_expire_seconds`，确保消费端运行 |
| `JSON serialization error` | 消息体包含不可序列化对象 | 使用 MEMORY_QUEUE 或自定义序列化 |
| `QPS 不生效` | 并发数设置不合理 | 设置 `qps` 时让 `concurrent_num` 自动调整（默认 500） |

### 19.3 性能优化建议

1. **高吞吐场景**: 使用 `FASTEST_MEM_QUEUE` 或 `REDIS`，设置 `pull_msg_batch_size`
2. **高可靠场景**: 使用 `REDIS_ACK_ABLE` 或 `RABBITMQ`
3. **延迟敏感**: 使用 `MEMORY_QUEUE`，避免网络 IO
4. **海量任务**: 使用 `multi_process_pub_params_list` 快速发布，再慢慢消费

---

## 二十、设计理念总结

1. **函数至上**: `@boost` 一个装饰器搞定一切，普通函数变成分布式任务
2. **万物皆 Broker**: 50 种中间件，统一抽象，无缝切换
3. **自由组合**: 并发模式叠加（线程/协程 + 多进程）
4. **链式上下文**: `fct` 对象自动线程/协程隔离
5. **FaaS 升级**: Worker → Service，函数即接口
6. **零约束**: 目录结构、启动方式完全自由

**核心哲学**: "函数是最高级的抽象，框架应该服务函数，而不是奴役函数"

---

*本文档由 AI 分析 funboost 源码生成，用于快速检索和理解代码结构。*
*结合教程文档：D:\codes\funboost\funboost_all_docs_and_codes.md*
