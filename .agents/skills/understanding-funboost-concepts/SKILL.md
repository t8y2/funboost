---
name: understanding-funboost-concepts
description: 当 AI 首次接触 funboost 或需要建立正确心智模型时使用。触发场景：AI 准备编写 funboost 代码前、对框架设计理念不清楚时、容易把 funboost 当成 Celery 时。关键词：funboost 是什么, 怎么理解, 框架设计, BoosterParams, 配置文件, push vs publish, 消费模型, 入门概念。
compatibility: Python 3.7+, funboost
---

# 理解 Funboost 核心概念

## 一、框架哲学："反框架"设计

Funboost 的核心设计理念是**零代码侵入**：

```python
# 你的原始函数 — 直接调用，完全正常
def process(url, depth=1):
    return download(url)

process("http://example.com")  # 普通函数调用

# 加上 @boost — 函数本身不变，但获得了分布式能力
from funboost import boost, BoosterParams, BrokerEnum

@boost(BoosterParams(queue_name="spider", broker_kind=BrokerEnum.MEMORY_QUEUE))
def process(url, depth=1):
    return download(url)

process("http://example.com")      # 仍然可以直接调用！
process.push("http://example.com") # 发到队列，由消费者异步执行
```

**关键认知：**
- `func(x, y)` = 直接运行（同步、本地）
- `func.push(x, y)` = 发消息到队列（异步、分布式）
- 函数本身没有任何改变，不需要继承、不需要注册、不需要特殊签名

## 二、BoosterParams — 掌握 funboost 的重中之重

`BoosterParams` 是一个 Pydantic 模型，包含 **50+ 个字段**，控制着 funboost 的任务级行为。理解 funboost 等于理解 BoosterParams。

### 核心原则

1. **任务级配置在 BoosterParams** — 并发、重试、控频、超时等；**中间件连接配置**在 `funboost_config.py` 的 `BrokerConnConfig`
2. **Pydantic 严格校验** — 传了不存在的字段会直接报错，禁止臆造参数
3. **唯一必填字段是 `queue_name`** — 其他都有默认值

### 字段分类速记

| 类别 | 核心字段 | 作用 |
|------|----------|------|
| 基础 | `queue_name`, `broker_kind` | 队列名和中间件选择 |
| 并发 | `concurrent_mode`, `concurrent_num` | 并发模式和并发数 |
| 控频 | `qps` | 每秒执行次数限制 |
| 重试 | `max_retry_times`, `is_using_advanced_retry` | 失败重试策略 |
| 超时 | `function_timeout` | 单次执行超时 |
| RPC | `is_using_rpc_mode` | 是否获取执行结果 |
| 扩展 | `consumer_override_cls`, `user_options` | Mixin 混入和自定义配置 |

### 常见"臆造参数"纠正

| 错误写法 | 正确写法 |
|----------|----------|
| `timeout=30` | `function_timeout=30` |
| `max_retries=5` | `max_retry_times=5` |
| `workers=10` | `concurrent_num=10` |
| `backend="redis"` | `broker_kind=BrokerEnum.REDIS` |
| `retry_delay=5` | `is_using_advanced_retry=True` + `advanced_retry_config={...}` |

## 三、配置文件机制

Funboost 的中间件连接信息（Redis/RabbitMQ/Kafka 等的 host、port、password）不在 BoosterParams 中，而是在 `funboost_config.py` 配置文件中。

### 加载原理

```
set_frame_config.py 中：importlib.import_module('funboost_config')
        ↓
按 sys.path 顺序搜索（sys.path[0]=脚本目录, sys.path[1]=PYTHONPATH项目根）
        ↓
找到后通过 BrokerConnConfig.update_cls_attribute 覆盖默认值
        ↓
找不到时自动在 sys.path[1] 生成模板文件
```

### 关键规则

1. **设置 PYTHONPATH** — 运行脚本前必须将项目根目录加入 PYTHONPATH（`$env:PYTHONPATH="项目根"`）
2. **优先级** — `sys.path[0]`（脚本所在目录）> `sys.path[1]`（PYTHONPATH 项目根）> 默认值
3. **自动生成** — 首次运行时框架会在 `sys.path[1]` 自动生成模板 `funboost_config.py`
4. **按需配置** — 只需配置实际使用的中间件（用 Redis 就只配 Redis，不用管 RabbitMQ）

### 配置文件内容示例

```python
# funboost_config.py（项目根目录，框架首次运行自动生成）
from funboost.utils.simple_data_class import DataClassBase

class BrokerConnConfig(DataClassBase):
    REDIS_HOST = '127.0.0.1'
    REDIS_PORT = 6379
    REDIS_PASSWORD = 'your_password'
    REDIS_DB = 7
```

## 四、push vs publish — 本质区别

| 方法 | 用途 | 参数方式 |
|------|------|----------|
| `func.push(x, y, z=1)` | 只传业务参数 | 与函数签名一致 |
| `func.publish({"x":1, "y":2}, task_options=TaskOptions(...))` | 需要框架控制参数 | 字典 + TaskOptions |

**什么时候用 publish？**
- 需要指定 `task_id`（幂等/追踪）
- 需要设置 `countdown`（延迟执行）
- 需要设置 `eta`（定时执行）

**90% 的场景用 `push` 就够了。**

## 五、消费模型

### 为什么 `consume()` 不阻塞？

`func.consume()` 在子线程中启动消费循环，主线程继续执行：

```python
func1.consume()  # 启动消费（非阻塞）
func2.consume()  # 可以紧接着启动另一个
func3.consume()  # 多个消费者共存

# 主线程到达末尾后，进程不会退出（因为有子线程在跑）
```

### 为什么永不自动停止？

Funboost 设计为**长期运行的服务**，消费者会无限循环拉取消息。这不是 bug，而是核心设计：
- 生产环境中消费者 7x24 运行
- AI 测试时必须用 `timeout` 或 `os._exit(66)` 强制终止

### 5 种并发模式

| 模式 | 适用场景 |
|------|----------|
| `THREADING`（默认） | IO 密集型任务（HTTP 请求、数据库读写） |
| `GEVENT` | 超高并发 IO（爬虫、大量网络请求） |
| `EVENTLET` | 类似 gevent，兼容某些特殊库 |
| `ASYNC` | 原生 asyncio（async def 消费函数） |
| `SINGLE_THREAD` | 严格顺序执行（无并发） |

## 六、fct 上下文 — 禁止 Celery 思维

**Celery 做法（禁止）：**
```python
@app.task(bind=True)
def my_task(self, x):
    self.request.id  # Celery 方式
```

**Funboost 做法（正确）：**
```python
from funboost import fct

@boost(BoosterParams(queue_name="xxx"))
def my_task(x):
    fct.task_id                         # 当前任务 ID
    fct.queue_name                      # 队列名
    fct.function_result_status.run_times # 执行次数（含重试）
    fct.full_msg                        # 完整消息体
    fct.logger                          # 当前任务 logger
```

`fct` 是线程安全的全局上下文对象，**仅在消费函数执行期间**自动注入当前任务信息。在消费函数外部或直接调用 `func()` 时，`fct` 无上下文，访问属性会报错。

## 七、Broker 与配置的三层关系

```
BrokerConnConfig（funboost_config.py）
  └── 中间件连接信息：host, port, password, url
       ↓ 框架自动使用

BoosterParams.broker_kind
  └── 选择使用哪种中间件类型（BrokerEnum.REDIS / RABBITMQ / ...）

BoosterParams.broker_exclusive_config
  └── 该 broker 的独有动态配置（如 Redis 的 maxsize、Kafka 的 group_id）
```

**区分：**
- `BrokerConnConfig` = 全局固定连接信息（所有队列共用）
- `broker_kind` = 选择中间件类型
- `broker_exclusive_config` = 单个队列的 broker 专属配置

> **SSS 级推荐：`BrokerEnum.MEMORY_QUEUE`**
>
> 很多场景不需要分布式 MQ。`MEMORY_QUEUE` 让 `@boost` 成为**超级装饰器**：
> 零中间件、无 JSON/pickle 序列化（同进程直传对象）、自带 QPS/并发/重试/超时——完美替代 `ThreadPoolExecutor`。
> 后续需要分布式时只改 `broker_kind` 一行。详见 skill：`funboost-memory-queue-pool`

## 八、AI 编码前的自检清单

在编写 funboost 代码前，确认以下几点：

- [ ] 使用 `@boost(BoosterParams(...))` 而非老式写法
- [ ] 所有参数名从文档中查找，不要臆造
- [ ] 获取上下文用 `fct`，不用 `self` 或 `bind=True`
- [ ] `push` 传业务参数，`publish` 传字典 + `TaskOptions`
- [ ] 需要获取结果必须设置 `is_using_rpc_mode=True`
- [ ] 异步函数必须设置 `concurrent_mode=ConcurrentModeEnum.ASYNC`
- [ ] 运行前设置 `PYTHONPATH=项目根目录`
- [ ] 测试脚本必须有退出机制（`timeout` 或 `os._exit(66)`）

## 相关 Skill

- `using-funboost-basics` — 基础使用入门
- `funboost-broker-selection` — Broker 中间件选型
