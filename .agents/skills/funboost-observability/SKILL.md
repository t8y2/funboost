---
name: funboost-observability
description: 当需要为 funboost 任务添加监控、链路追踪或告警时使用。触发场景：Prometheus 指标、OpenTelemetry 链路追踪、异常告警通知、周期额度限制、函数结果持久化。关键词：Prometheus, OpenTelemetry, OTel, 告警, 监控, metrics, tracing, AlertNotifier, PeriodicQuota。
---

# Funboost 可观测性配置

## 概述

Funboost 通过 **Mixin 机制**（`consumer_override_cls` / `publisher_override_cls`）和 **BoosterParams 内置字段**，为任务队列提供生产级可观测性能力，无需修改 broker 源码。

**核心原则：**
- 监控/追踪/告警均通过 Mixin 或 BoosterParams 声明式配置
- Mixin 专属参数统一放在 `user_options` 字典中
- 各 Mixin 位于 `funboost/contrib/override_publisher_consumer_cls/`，**不在** `from funboost import ...` 顶层导出

## 适用场景

| 需求 | 方案 |
|------|------|
| Grafana 运维大盘 | `PrometheusConsumerMixin` |
| 跨队列/跨服务链路追踪 | `AutoOtelConsumerMixin` + `AutoOtelPublisherMixin` |
| 连续失败/错误率即时告警 | `AlertNotifierConsumerMixin` |
| 周期内限制总执行次数 | `PeriodicQuotaConsumerMixin` |
| 任务状态/结果持久化 + Web 查询 | `function_result_status_persistance_conf` |
| 分布式聚合告警（无需 Mixin） | `MongoAlertMonitor`（需开启 `is_save_status=True`） |

## 导入路径速查

```python
# 顶层导出（funboost/__init__.py）
from funboost import (
    boost, BoosterParams, BrokerEnum,
    FunctionResultStatusPersistanceConfig,  # 函数结果持久化配置
)

# Mixin 需从 contrib 子模块导入
from funboost.contrib.override_publisher_consumer_cls.funboost_promethus_mixin import (
    PrometheusConsumerMixin,
    PrometheusPublisherMixin,
    PrometheusBoosterParams,
    PrometheusPushGatewayBoosterParams,
    start_prometheus_http_server,
)
from funboost.contrib.override_publisher_consumer_cls.funboost_otel_mixin import (
    AutoOtelConsumerMixin,
    AutoOtelPublisherMixin,
    OtelBoosterParams,
)
from funboost.contrib.override_publisher_consumer_cls.alert_notifier_mixin import (
    AlertNotifierConsumerMixin,
    AlertNotifierBoosterParams,
)
from funboost.contrib.override_publisher_consumer_cls.periodic_quota_mixin import (
    PeriodicQuotaConsumerMixin,
    PeriodicQuotaBoosterParams,
)
from funboost.core.mongo_alert_monitor import MongoAlertMonitor  # 基于 MongoDB 的聚合告警
```

---

## 1. Prometheus 指标监控

### 工作原理

- `PrometheusPublisherMixin`：在 `_after_publish` 钩子记录 `funboost_publish_total`
- `PrometheusConsumerMixin`：在 `_both_sync_and_aio_frame_custom_record_process_info_func` 钩子记录任务计数、耗时、重试、队列积压

### 两种部署模式

| 模式 | 适用场景 | 关键步骤 |
|------|----------|----------|
| HTTP Server（单进程） | 单消费者进程 | 调用 `start_prometheus_http_server(port=8000)`，Prometheus 主动拉取 `/metrics` |
| Push Gateway（多进程） | `multi_process_consume` 等多进程 | 配置 `user_options` 中的 Pushgateway 地址，后台线程定期推送 |

### 指标说明

| 指标名 | 类型 | Labels | 说明 |
|--------|------|--------|------|
| `funboost_task_total` | Counter | queue, status | 任务计数（status: success/fail/requeue/dlx） |
| `funboost_task_latency_seconds` | Histogram | queue | 任务执行耗时 |
| `funboost_task_retries_total` | Counter | queue | 重试次数 |
| `funboost_queue_msg_count` | Gauge | queue | 队列剩余消息数 |
| `funboost_publish_total` | Counter | queue | 发布消息计数 |

### user_options 配置（Push Gateway 模式）

| 键名 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `prometheus_pushgateway_url` | str | **必填** | Pushgateway 地址，如 `'localhost:9091'` |
| `prometheus_push_interval` | float | `10.0` | 推送间隔（秒） |
| `prometheus_job_name` | str | `'funboost'` | Prometheus job 名称 |

### 代码示例

```python
# ── 方式1：HTTP Server 模式（单进程） ──
from funboost import boost
from funboost.contrib.override_publisher_consumer_cls.funboost_promethus_mixin import (
    PrometheusBoosterParams,
    start_prometheus_http_server,
)

start_prometheus_http_server(port=8000)  # 访问 http://0.0.0.0:8000/metrics

@boost(PrometheusBoosterParams(queue_name='my_task'))
def my_task(x):
    return x * 2

if __name__ == '__main__':
    my_task.consume()
    my_task.push(10)


# ── 方式2：Push Gateway 模式（多进程推荐） ──
from funboost import boost
from funboost.contrib.override_publisher_consumer_cls.funboost_promethus_mixin import (
    PrometheusPushGatewayBoosterParams,
)

@boost(PrometheusPushGatewayBoosterParams(
    queue_name='my_task',
    user_options={
        'prometheus_pushgateway_url': 'localhost:9091',
        'prometheus_push_interval': 10.0,
        'prometheus_job_name': 'my_app',
    },
))
def my_task_mp(x):
    return x * 2

if __name__ == '__main__':
    my_task_mp.multi_process_consume(4)
```

### 手动指定 Mixin（不用预配置 Params 类）

```python
from funboost import boost, BoosterParams, BrokerEnum
from funboost.contrib.override_publisher_consumer_cls.funboost_promethus_mixin import (
    PrometheusConsumerMixin,
    PrometheusPublisherMixin,
    start_prometheus_http_server,
)

start_prometheus_http_server(port=8000)

@boost(BoosterParams(
    queue_name='my_task',
    broker_kind=BrokerEnum.REDIS,
    consumer_override_cls=PrometheusConsumerMixin,
    publisher_override_cls=PrometheusPublisherMixin,
))
def my_task(x):
    return x * 2
```

---

## 2. OpenTelemetry 链路追踪

### 工作原理

- `AutoOtelPublisherMixin`：重写 `_execute_publish`，创建 PRODUCER span，将 trace context **注入**到 `msg['extra']['otel_context']`
- `AutoOtelConsumerMixin`：重写 `_run` / `_async_run`，从消息 **提取** context，创建 CONSUMER span 作为子节点
- 支持 W3C Trace Context 规范，可对接 Jaeger / Zipkin / SkyWalking 等 OTel 兼容后端
- `aio_publish` 场景自动处理跨线程 context 丢失问题

### 前置条件

**必须在消费启动前初始化 OpenTelemetry**（Mixin 本身不包含 exporter 配置）：

```python
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

def init_opentelemetry(service_name: str = "my-funboost-app"):
    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)
    otlp_exporter = OTLPSpanExporter(endpoint="localhost:4317", insecure=True)
    provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
    trace.set_tracer_provider(provider)
```

启动 Jaeger（可选，本地调试）：

```sh
docker run -d --name jaeger \
  -e COLLECTOR_OTLP_ENABLED=true \
  -p 16686:16686 \
  -p 4317:4317 \
  -p 4318:4318 \
  jaegertracing/all-in-one:latest
```

访问 `http://localhost:16686` 查看链路。

### user_options

OTel Mixin **无专属 user_options**，配置通过全局 `TracerProvider` + exporter 完成。

### 代码示例

```python
from funboost import boost, BrokerEnum, fct
from funboost.contrib.override_publisher_consumer_cls.funboost_otel_mixin import OtelBoosterParams

init_opentelemetry("order-service")

@boost(OtelBoosterParams(
    queue_name='otel_task_entry',
    broker_kind=BrokerEnum.REDIS,
))
def task_entry(order_id: int):
    fct.logger.info(f"处理订单 {order_id}")
    task_process.push(order_id=order_id)  # 链路上下文自动传播
    return order_id

@boost(OtelBoosterParams(
    queue_name='otel_task_process',
    broker_kind=BrokerEnum.REDIS,
))
def task_process(order_id: int):
    return f"processed {order_id}"

if __name__ == '__main__':
    task_process.consume()
    task_entry.consume()
    task_entry.push(order_id=1001)
```

### 手动指定 Mixin

```python
from funboost import boost, BoosterParams, BrokerEnum
from funboost.contrib.override_publisher_consumer_cls.funboost_otel_mixin import (
    AutoOtelConsumerMixin,
    AutoOtelPublisherMixin,
)

@boost(BoosterParams(
    queue_name='my_otel_task',
    broker_kind=BrokerEnum.REDIS,
    consumer_override_cls=AutoOtelConsumerMixin,
    publisher_override_cls=AutoOtelPublisherMixin,
))
def my_otel_task(x):
    return x + 1
```

### 与 logger + task_id 的关系

| 维度 | Logger + task_id | OpenTelemetry |
|------|------------------|---------------|
| 视角 | 一维文本日志 | 树状/甘特图 |
| 跨服务 | 需手动关联 | 自动串联 |
| 性能分析 | 需人工计算 | 直观看瓶颈 |

两者互补，建议生产环境同时使用。

---

## 3. 异常告警通知（AlertNotifierConsumerMixin）

### 工作原理

- 仅做**告警通知**，不熔断、不阻塞消费
- 支持两种触发策略：`consecutive`（连续失败）和 `rate`（滑动窗口错误率）
- 进入告警状态发送通知，恢复后自动发送恢复通知
- requeue、死信队列、远程 kill 不计入失败计数（避免误告警）

### user_options['alert_options'] 配置

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `strategy` | str | `'consecutive'` | `'consecutive'` 或 `'rate'` |
| `failure_threshold` | int | `5` | 连续失败次数阈值（consecutive 策略） |
| `errors_rate` | float | `0.5` | 错误率阈值 0.0~1.0（rate 策略） |
| `period` | float | `60.0` | 统计窗口秒数（rate 策略） |
| `min_calls` | int | `5` | 窗口内最少调用数（rate 策略） |
| `alert_app` | str | `'wechat'` | 告警通道：`dingtalk` / `wechat` / `feishu` / `webhook` / `custom` |
| `webhook_url` | str | `None` | 对应通道的 Webhook 地址（**必填**） |
| `alert_interval` | int | `300` | 告警去重间隔秒数 |
| `exceptions` | tuple/None | `None` | 跟踪的异常类型（None 跟踪所有） |

### 代码示例

```python
from funboost import boost, BoosterParams, BrokerEnum
from funboost.contrib.override_publisher_consumer_cls.alert_notifier_mixin import (
    AlertNotifierConsumerMixin,
    AlertNotifierBoosterParams,
)

# 方式1：连续失败 5 次 → 企业微信告警（最简）
@boost(AlertNotifierBoosterParams(
    queue_name='my_task',
    broker_kind=BrokerEnum.REDIS,
    user_options={
        'alert_options': {
            'failure_threshold': 5,
            'alert_app': 'wechat',
            'webhook_url': 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=YOUR_KEY',
        },
    },
))
def my_task(x):
    return call_external_api(x)


# 方式2：错误率策略 + 钉钉告警
@boost(BoosterParams(
    queue_name='my_task_rate',
    broker_kind=BrokerEnum.REDIS,
    consumer_override_cls=AlertNotifierConsumerMixin,
    user_options={
        'alert_options': {
            'strategy': 'rate',
            'errors_rate': 0.5,
            'period': 60,
            'min_calls': 10,
            'alert_app': 'dingtalk',
            'webhook_url': 'https://oapi.dingtalk.com/robot/send?access_token=YOUR_TOKEN',
            'alert_interval': 600,
        },
    },
))
def my_task_rate(x):
    return call_external_api(x)


# 方式3：自定义告警渠道
class EmailAlertConsumer(AlertNotifierConsumerMixin):
    def custom_send_notification(self, message: str):
        send_email(to='ops@example.com', subject='任务告警', body=message)

@boost(BoosterParams(
    queue_name='my_task_custom',
    broker_kind=BrokerEnum.REDIS,
    consumer_override_cls=EmailAlertConsumer,
    user_options={
        'alert_options': {
            'alert_app': 'custom',
            'failure_threshold': 3,
        },
    },
))
def my_task_custom(x):
    return risky_operation(x)
```

---

## 4. 周期额度限制（PeriodicQuotaConsumerMixin）

### 工作原理

- 在指定周期内限制**总执行次数**，周期结束后配额自动重置
- **周期额度 ≠ 匀速执行**：例如"每天 24 次"允许一口气用完，不要求每小时 1 次
- 可与 `qps` 参数组合：`qps` 控制执行间隔，周期额度控制总次数
- 配额用完后阻塞等待下一周期（不丢消息）

### 两种窗口模式

| 模式 | user_options | 说明 |
|------|-------------|------|
| 滑动窗口（默认） | `sliding_window=True` | 从程序启动时刻起算周期 |
| 固定窗口 | `sliding_window=False` | 从整点边界起算（如每分钟从 XX:00 开始） |

### user_options 配置

| 键名 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `quota_limit` | int | `10` | 每周期最大执行次数 |
| `quota_period` | str | `'m'` | 周期类型：`'s'`秒 / `'m'`分 / `'h'`时 / `'d'`天 |
| `sliding_window` | bool | `True` | 滑动窗口 vs 固定窗口 |

### 代码示例

```python
from funboost import boost, BoosterParams, BrokerEnum
from funboost.contrib.override_publisher_consumer_cls.periodic_quota_mixin import (
    PeriodicQuotaConsumerMixin,
    PeriodicQuotaBoosterParams,
)

# 滑动窗口：每秒 1 次，每分钟最多 6 次
@boost(BoosterParams(
    queue_name='minute_quota_queue',
    broker_kind=BrokerEnum.REDIS,
    consumer_override_cls=PeriodicQuotaConsumerMixin,
    user_options={
        'quota_limit': 6,
        'quota_period': 'm',
        'sliding_window': True,
    },
    qps=1,
))
def my_task(x):
    print(f'Processing {x}')


# 每天最多 30 次，每 10 分钟执行 1 次，固定窗口从 0 点起算
@boost(PeriodicQuotaBoosterParams(
    queue_name='daily_quota_queue',
    user_options={
        'quota_limit': 30,
        'quota_period': 'd',
        'sliding_window': False,
    },
    qps=1 / 600,  # 每 10 分钟 1 次
))
def daily_task(x):
    return process(x)
```

---

## 5. 函数结果持久化到 MongoDB

### 配置字段（BoosterParams 内置，非 Mixin）

通过 `function_result_status_persistance_conf` 配置，类型为 `FunctionResultStatusPersistanceConfig`（已从 `funboost` 顶层导出）。

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `is_save_status` | bool | `False` | 是否保存函数运行状态（成功/失败/耗时等） |
| `is_save_result` | bool | `False` | 是否保存函数返回值（需 `is_save_status=True`） |
| `expire_seconds` | int | `604800`（7天） | MongoDB 文档自动过期时间 |
| `is_use_bulk_insert` | bool | `False` | 批量插入（每 0.5 秒一批，性能更好但略有延迟） |
| `table_name` | str/None | `None` | MongoDB 集合名，默认使用 `queue_name` |

### 前置条件

1. 安装 MongoDB 驱动：`pip install pymongo`
2. 在 `funboost_config.py` 中配置连接：

```python
class BrokerConnConfig(DataClassBase):
    MONGO_CONNECT_URL = 'mongodb://127.0.0.1:27017'
    # 有密码示例：'mongodb://user:pass@host:27017/?authSource=admin'
```

### 代码示例

```python
from funboost import boost, BoosterParams, BrokerEnum, FunctionResultStatusPersistanceConfig

# 单队列独立集合
@boost(BoosterParams(
    queue_name='my_task',
    broker_kind=BrokerEnum.REDIS,
    function_result_status_persistance_conf=FunctionResultStatusPersistanceConfig(
        is_save_status=True,
        is_save_result=True,
        expire_seconds=7 * 24 * 3600,
    ),
))
def my_task(x):
    return x + 1


# 多队列共享同一 MongoDB 集合（便于统一查询）
class PersistBoosterParams(BoosterParams):
    function_result_status_persistance_conf = FunctionResultStatusPersistanceConfig(
        is_save_status=True,
        is_save_result=True,
        expire_seconds=17 * 24 * 3600,
        table_name='my_project_all_tasks',  # 自定义集合名
        is_use_bulk_insert=True,
    )

@boost(PersistBoosterParams(queue_name='queue_a', broker_kind=BrokerEnum.REDIS))
def task_a(x):
    return x

@boost(PersistBoosterParams(queue_name='queue_b', broker_kind=BrokerEnum.REDIS))
def task_b(x):
    return x
```

持久化数据可在 **funweb 管理界面**（`python -m funboost.funweb.app`）查看，也可配合 `MongoAlertMonitor` 做分布式聚合告警。

### MongoAlertMonitor（基于持久化的聚合告警）

无需 Mixin，独立进程轮询 MongoDB 统计失败率/次数：

```python
from funboost.core.mongo_alert_monitor import MongoAlertMonitor

MongoAlertMonitor(
    boosters=[my_task, task_a],       # 被 @boost 装饰的函数
    alert_app='wechat',
    webhook_url='https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=YOUR_KEY',
    window_seconds=60,
    failure_count=10,                  # 窗口内失败 >= 10 次告警
    poll_interval=10,
    alert_interval=300,
).start()
```

---

## 6. 组合多种 Mixin

多个 Mixin 可通过多重继承组合（注意 MRO 顺序）：

```python
from funboost import boost, BoosterParams, BrokerEnum
from funboost.contrib.override_publisher_consumer_cls.funboost_promethus_mixin import (
    PrometheusConsumerMixin, PrometheusPublisherMixin, start_prometheus_http_server,
)
from funboost.contrib.override_publisher_consumer_cls.alert_notifier_mixin import AlertNotifierConsumerMixin

class ObservabilityMixin(PrometheusConsumerMixin, AlertNotifierConsumerMixin):
    """Prometheus 指标 + 失败告警"""
    pass

start_prometheus_http_server(port=8000)

@boost(BoosterParams(
    queue_name='observable_task',
    broker_kind=BrokerEnum.REDIS,
    consumer_override_cls=ObservabilityMixin,
    publisher_override_cls=PrometheusPublisherMixin,
    user_options={
        'alert_options': {
            'failure_threshold': 5,
            'alert_app': 'wechat',
            'webhook_url': 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=YOUR_KEY',
        },
    },
))
def observable_task(x):
    return process(x)
```

> **注意**：`CircuitBreakerConsumerMixin` 的 `circuit_breaker_options` 使用嵌套字典，避免与 `PeriodicQuotaConsumerMixin` 的一级 `period` 键冲突。

---

## 7. 完整综合示例

```python
"""
可观测性综合示例：OTel 链路追踪 + Prometheus 指标 + 失败告警 + MongoDB 持久化
"""
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

from funboost import boost, BoosterParams, BrokerEnum, FunctionResultStatusPersistanceConfig
from funboost.contrib.override_publisher_consumer_cls.funboost_promethus_mixin import (
    PrometheusConsumerMixin, PrometheusPublisherMixin, start_prometheus_http_server,
)
from funboost.contrib.override_publisher_consumer_cls.funboost_otel_mixin import (
    AutoOtelConsumerMixin,
    AutoOtelPublisherMixin,
)
from funboost.contrib.override_publisher_consumer_cls.alert_notifier_mixin import (
    AlertNotifierConsumerMixin,
)


def init_opentelemetry():
    provider = TracerProvider(resource=Resource.create({"service.name": "demo-app"}))
    provider.add_span_processor(BatchSpanProcessor(
        OTLPSpanExporter(endpoint="localhost:4317", insecure=True)
    ))
    trace.set_tracer_provider(provider)


class FullObservabilityConsumer(PrometheusConsumerMixin, AutoOtelConsumerMixin, AlertNotifierConsumerMixin):
    pass


class FullObservabilityPublisher(PrometheusPublisherMixin, AutoOtelPublisherMixin):
    pass


init_opentelemetry()
start_prometheus_http_server(port=8000)

@boost(BoosterParams(
    queue_name='full_observable_task',
    broker_kind=BrokerEnum.REDIS,
    consumer_override_cls=FullObservabilityConsumer,
    publisher_override_cls=FullObservabilityPublisher,
    function_result_status_persistance_conf=FunctionResultStatusPersistanceConfig(
        is_save_status=True,
        is_save_result=True,
    ),
    user_options={
        'alert_options': {
            'failure_threshold': 5,
            'alert_app': 'wechat',
            'webhook_url': 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=YOUR_KEY',
        },
    },
))
def full_observable_task(order_id: int):
    return {"order_id": order_id, "status": "ok"}


if __name__ == '__main__':
    full_observable_task.consume()
    full_observable_task.push(order_id=1001)
```

---

## 8. 注意事项

### 依赖安装

```sh
# Prometheus
pip install prometheus_client

# OpenTelemetry
pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp

# MongoDB 持久化
pip install pymongo

# 告警 webhook 通道（webhook 模式）
pip install requests
```

### 配置文件

| 功能 | 配置位置 | 说明 |
|------|----------|------|
| MongoDB 连接 | `funboost_config.py` → `BrokerConnConfig.MONGO_CONNECT_URL` | 持久化和 MongoAlertMonitor 必需 |
| Redis | `funboost_config.py` → `BrokerConnConfig.REDIS_*` | RPC 模式、分布式控频等 |
| OTel Exporter | 应用启动代码中 `init_opentelemetry()` | Mixin 不包含 exporter，需用户自行配置 |
| Prometheus 拉取 | `start_prometheus_http_server(port)` 或 Pushgateway | 单进程用 HTTP Server，多进程用 Push Gateway |

### 常见陷阱

1. **OTel 必须先 init 再 consume**：未设置 `TracerProvider` 时 span 不会上报到后端
2. **Prometheus 多进程必须用 Push Gateway**：HTTP Server 模式下每个进程独立端口，Prometheus 难以统一采集
3. **持久化约束**：`is_save_result=True` 时 `is_save_status` 必须为 `True`，否则抛 `ValueError`
4. **AlertNotifier 与 CircuitBreaker 区别**：AlertNotifier 只告警不阻塞；CircuitBreaker 会暂停消费或降级
5. **Mixin 不在顶层导出**：必须从 `funboost.contrib.override_publisher_consumer_cls.*` 导入
6. **周期额度 vs Celery rate_limit**：funboost 周期额度允许周期内任意时间分布执行，Celery `rate_limit='6/m'` 强制匀速间隔
7. **告警 IO 在 `_frame_custom_record_process_info_func` 中执行**：AlertNotifier 的 webhook 发送在此钩子，对消费性能影响极小；Prometheus 指标采集在 `_both_sync_and_aio_frame_custom_record_process_info_func`，同步/异步任务均覆盖

### 参考资源

| 资源 | 路径 |
|------|------|
| Prometheus Mixin 源码 | `funboost/contrib/override_publisher_consumer_cls/funboost_promethus_mixin.py` |
| OTel Mixin 源码 | `funboost/contrib/override_publisher_consumer_cls/funboost_otel_mixin.py` |
| 告警 Mixin 源码 | `funboost/contrib/override_publisher_consumer_cls/alert_notifier_mixin.py` |
| 周期额度 Mixin 源码 | `funboost/contrib/override_publisher_consumer_cls/periodic_quota_mixin.py` |
| OTel 演示 | `test_frame/test_otel/test_otel_override.py` |
| 持久化演示 | `test_frame/test_function_status_result_persist/test_persist.py` |
| MongoDB 聚合告警 | `funboost/core/mongo_alert_monitor.py` |
| 文档章节 | `4b.7` OTel / `4b.9` Prometheus / `4b.12` 周期额度 / `6.30` 告警 |

## 相关 Skill

- `developing-funboost-mixin` — Consumer/Publisher Mixin 扩展
- `funboost-funweb-ops` — Web 管理界面运维
