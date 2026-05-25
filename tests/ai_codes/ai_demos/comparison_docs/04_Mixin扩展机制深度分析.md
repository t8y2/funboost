# Funboost Mixin 扩展机制深度分析

> Funboost vs Celery 扩展机制对比

---

## 一、扩展机制总览

### 1.1 对比表

| 维度 | Funboost | Celery |
|------|----------|--------|
| **扩展方式** | Mixin 类继承 | Signal 信号 |
| **类型安全** | ✅ | ❌ |
| **配置集成** | ✅ Pydantic | ❌ |
| **可组合性** | ✅ 多 Mixin | ❌ |
| **覆盖粒度** | 方法级 | 钩子级 |
| **内置扩展** | 6+ 种 | 需第三方 |

### 1.2 Funboost Mixin 列表

| Mixin | 说明 |
|-------|------|
| `CircuitBreakerConsumerMixin` | 熔断器 |
| `MicroBatchConsumerMixin` | 微批处理 |
| `PrometheusConsumerMixin` | Prometheus 监控 |
| `AutoOtelConsumerMixin` | OpenTelemetry 链路追踪 |
| `PeriodicQuotaConsumerMixin` | 周期额度限制 |
| `AlertNotifierConsumerMixin` | 异常告警通知 |

---

## 二、CircuitBreakerConsumerMixin - 熔断器

### 2.1 核心概念

```
┌─────────────────────────────────────────────────────────────┐
│                  Circuit Breaker 三态                         │
│                                                             │
│   ┌─────────┐    失败 >= N      ┌─────────┐   恢复超时    ┌──────────┐
│   │ CLOSED  │ ────────────────→ │  OPEN   │ ─────────────→│ HALF_OPEN│
│   │ (正常)  │                   │ (熔断)  │               │  (试探)  │
│   └─────────┘                   └─────────┘               └──────────┘
│        ↑                              │                        │
│        │     连续成功 >= M             │      任意失败           │
│        └───────────────────────────────┘                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 两种触发策略

#### 策略1: consecutive（连续失败）

```python
# 连续失败 5 次触发熔断
# 任意一次成功重置计数
@boost(CircuitBreakerBoosterParams(
    queue_name='demo',
    user_options={
        'circuit_breaker_options': {
            'strategy': 'consecutive',
            'failure_threshold': 5,
            'recovery_timeout': 60,  # 60 秒后尝试恢复
        }
    }
))
def demo_task(x):
    call_api(x)
```

#### 策略2: rate（错误率滑动窗口）

```python
# 60 秒内，调用 >= 10 次 且 错误率 >= 50% 触发熔断
@boost(CircuitBreakerBoosterParams(
    queue_name='rate_demo',
    user_options={
        'circuit_breaker_options': {
            'strategy': 'rate',
            'errors_rate': 0.5,
            'period': 60,
            'min_calls': 10,
        }
    }
))
def rate_task(x):
    call_api(x)
```

### 2.3 两种计数后端

#### 本地内存计数（单进程）

```python
user_options={
    'circuit_breaker_options': {
        'counter_backend': 'local',  # 默认
    }
}
```

#### Redis 分布式计数（多进程/多机器）

```python
user_options={
    'circuit_breaker_options': {
        'counter_backend': 'redis',  # 多进程共享状态
    }
}
```

### 2.4 Fallback 降级模式

```python
def fallback_handler(x):
    """熔断期间执行的降级函数"""
    return {'status': 'degraded', 'data': x}

@boost(CircuitBreakerBoosterParams(
    queue_name='fallback_demo',
    user_options={
        'circuit_breaker_options': {
            'fallback': fallback_handler,
            'failure_threshold': 3,
        }
    }
))
def main_task(x):
    call_api(x)
```

### 2.5 告警钩子

```python
class MyAlertMixin(CircuitBreakerConsumerMixin):
    def _on_circuit_open(self, info_dict):
        """熔断触发时"""
        send_dingtalk(f"队列 {info_dict['queue_name']} 已熔断！失败 {info_dict['failure_count']} 次")

    def _on_circuit_close(self, info_dict):
        """熔断恢复时"""
        send_wechat(f"队列 {info_dict['queue_name']} 已恢复正常")

@boost(BoosterParams(
    queue_name='alert_demo',
    consumer_override_cls=MyAlertMixin,
    user_options={
        'circuit_breaker_options': {
            'failure_threshold': 5,
            'recovery_timeout': 60,
        }
    }
))
def alert_task(x):
    pass
```

### 2.6 完整配置参数

```python
user_options={
    'circuit_breaker_options': {
        # 策略
        'strategy': 'consecutive',  # 或 'rate'
        
        # 计数后端
        'counter_backend': 'local',  # 或 'redis'
        
        # consecutive 策略
        'failure_threshold': 5,      # 连续失败次数
        
        # rate 策略
        'errors_rate': 0.5,         # 错误率阈值
        'period': 60,                # 滑动窗口秒数
        'min_calls': 10,             # 最小调用数
        
        # 恢复
        'recovery_timeout': 60,      # 熔断后等待秒数
        'half_open_max_calls': 3,    # 半开连续成功次数
        'half_open_ttl': 30,         # 半开超时秒数
        
        # 异常过滤
        'exceptions': (ValueError,), # 只跟踪特定异常
        
        # 降级
        'fallback': my_fallback,     # 降级函数
    }
}
```

---

## 三、MicroBatchConsumerMixin - 微批处理

### 3.1 核心概念

```
┌─────────────────────────────────────────────────────────────┐
│                    消息缓冲流程                              │
│                                                             │
│  消息队列                                                   │
│     │                                                       │
│     ▼                                                       │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              消息缓冲区                              │   │
│  │                                                      │   │
│  │  [msg1] [msg2] [msg3] ... [msg100]                 │   │
│  │                                                      │   │
│  └─────────────────────────────────────────────────────┘   │
│     │                                                       │
│     │  达到 batch_size=100 或 timeout=5s                  │
│     ▼                                                       │
│  ┌─────────────────────────────────────────────────────┐   │
│  │            批量调用消费函数                           │   │
│  │                                                      │   │
│  │  def consumer(items: list):                         │   │
│  │      db.bulk_insert(items)  # 一次数据库操作         │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 代码示例

```python
@boost(BoosterParams(
    queue_name='batch_insert',
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    consumer_override_cls=MicroBatchConsumerMixin,
    concurrent_mode=ConcurrentModeEnum.THREADING,
    user_options={
        'micro_batch_size': 100,      # 每批 100 条
        'micro_batch_timeout': 5.0,   # 5 秒超时
    }
))
def batch_insert(items: list):
    """消费函数入参变为 list"""
    # 批量插入数据库（一次 IO）
    db.bulk_insert('orders', items)

# 发布消息
for i in range(10000):
    batch_insert.push(order_id=i, amount=100)
```

### 3.3 性能对比

| 模式 | 10000 条插入耗时 | 数据库连接数 |
|------|------------------|--------------|
| 普通模式 | ~50s | 10000 |
| 微批处理 | ~5s | 100 |

### 3.4 配置参数

```python
user_options = {
    'micro_batch_size': 100,     # 批量大小
    'micro_batch_timeout': 5.0,  # 超时秒数
}
```

---

## 四、PrometheusConsumerMixin - 监控指标

### 4.1 暴露的指标

| 指标 | 类型 | 说明 |
|------|------|------|
| `funboost_tasks_total` | Counter | 总任务数 |
| `funboost_tasks_success` | Counter | 成功任务数 |
| `funboost_tasks_failure` | Counter | 失败任务数 |
| `funboost_task_duration_seconds` | Histogram | 任务执行时间 |
| `funboost_queue_length` | Gauge | 队列长度 |

### 4.2 代码示例

```python
from prometheus_client import start_http_server

@boost(BoosterParams(
    queue_name='monitored_task',
    consumer_override_cls=PrometheusConsumerMixin,
    broker_exclusive_config={
        'prometheus_port': 9090,  # 指标暴露端口
    }
))
def monitored_task(x):
    return process(x)

# 启动指标服务器
start_http_server(9090)
```

### 4.3 访问指标

```bash
# 访问 metrics 端点
curl http://localhost:9090/metrics

# 输出示例
funboost_tasks_total{queue_name="monitored_task"} 10000
funboost_tasks_success{queue_name="monitored_task"} 9990
funboost_tasks_failure{queue_name="monitored_task"} 10
```

---

## 五、AutoOtelConsumerMixin - 链路追踪

### 5.1 支持的追踪系统

| 系统 | 状态 |
|------|------|
| Jaeger | ✅ |
| Zipkin | ✅ |
| Tempo | ✅ |
| DataDog | ✅ |
| AWS X-Ray | ✅ |

### 5.2 代码示例

```python
from opentelemetry import trace

@boost(BoosterParams(
    queue_name='traced_task',
    consumer_override_cls=AutoOtelConsumerMixin,
    user_options={
        'otel_service_name': 'my-service',
        'otel_exporter': 'jaeger',
        'otel_endpoint': 'http://localhost:14268/api/traces',
    }
))
def traced_task(x):
    with trace.get_tracer(__name__).start_as_current_span("process"):
        return process(x)
```

---

## 六、PeriodicQuotaConsumerMixin - 周期额度

### 6.1 核心概念

```
┌─────────────────────────────────────────────────────────────┐
│                    周期额度控制                               │
│                                                             │
│   限制：每分钟最多执行 1000 次                               │
│                                                             │
│   第 1 分钟: ████████████████████████ 1000/1000  (满)       │
│   第 2 分钟: ████████████░░░░░░░░░░░░░░░ 500/1000  (进行中)│
│   第 3 分钟: ░░░░░░░░░░░░░░░░░░░░░░░░░░ 0/1000  (重置)     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 6.2 代码示例

```python
@boost(BoosterParams(
    queue_name='quota_limited',
    consumer_override_cls=PeriodicQuotaConsumerMixin,
    user_options={
        'quota_limit': 1000,         # 周期内限制
        'quota_period': 60,          # 周期秒数
        'quota_backend': 'redis',     # 或 'local'
    }
))
def limited_task(x):
    """每分钟最多执行 1000 次"""
    pass
```

---

## 七、自定义 Mixin

### 7.1 创建自定义 Mixin

```python
from funboost.consumers.base_consumer import AbstractConsumer

class MyCustomMixin(AbstractConsumer):
    """自定义扩展 Mixin"""
    
    def custom_init(self):
        """初始化扩展"""
        super().custom_init()
        # 初始化自定义逻辑
        self._custom_state = {}
    
    def _submit_task(self, kw):
        """拦截任务提交"""
        # 在任务提交前执行自定义逻辑
        self._pre_submit(kw)
        
        # 调用父类方法
        super()._submit_task(kw)
        
        # 在任务提交后执行自定义逻辑
        self._post_submit(kw)
    
    def _pre_submit(self, kw):
        """提交前钩子"""
        pass
    
    def _post_submit(self, kw):
        """提交后钩子"""
        pass
```

### 7.2 使用自定义 Mixin

```python
@boost(BoosterParams(
    queue_name='custom_demo',
    consumer_override_cls=MyCustomMixin,
    # 自定义配置
    user_options={
        'my_option1': 'value1',
        'my_option2': 'value2',
    }
))
def custom_task(x):
    pass
```

### 7.3 组合多个 Mixin

```python
class MyComboMixin(
    CircuitBreakerConsumerMixin,
    MicroBatchConsumerMixin,
    PrometheusConsumerMixin,
    AbstractConsumer
):
    """组合多个 Mixin"""
    pass

@boost(BoosterParams(
    queue_name='combo_demo',
    consumer_override_cls=MyComboMixin,
    user_options={
        'circuit_breaker_options': {...},
        'micro_batch_size': 100,
    }
))
def combo_task(x):
    pass
```

---

## 八、Mixin 实现原理

### 8.1 Mixin 类结构

```python
class AbstractConsumer:
    """消费者基类"""
    
    def custom_init(self):
        """初始化钩子"""
        pass
    
    def _submit_task(self, kw):
        """提交任务"""
        pass
    
    def _run_consuming_function_with_confirm_and_retry(self, kw, retry_times, status):
        """执行消费函数"""
        pass

class CircuitBreakerConsumerMixin(AbstractConsumer):
    """熔断器 Mixin - 覆盖 _submit_task"""
    
    def custom_init(self):
        """初始化熔断器"""
        super().custom_init()
        self._circuit_breaker = CircuitBreaker()
    
    def _submit_task(self, kw):
        """检查熔断状态"""
        while self._circuit_breaker.is_open:
            time.sleep(1)
        super()._submit_task(kw)
    
    def _frame_custom_record_process_info_func(self, result_status, kw):
        """记录执行结果到熔断器"""
        super()._frame_custom_record_process_info_func(result_status, kw)
        if result_status.success:
            self._circuit_breaker.record_success()
        else:
            self._circuit_breaker.record_failure()
```

### 8.2 MRO（方法解析顺序）

```python
class MyConsumer(
    CircuitBreakerConsumerMixin,
    MicroBatchConsumerMixin,
    AbstractConsumer
):
    pass

# MRO 顺序：
# MyConsumer
# → CircuitBreakerConsumerMixin
# → MicroBatchConsumerMixin
# → AbstractConsumer
```

### 8.3 调用流程

```
_submit_task()
    │
    ├─ CircuitBreakerConsumerMixin._submit_task()
    │       │
    │       └─ 检查熔断状态
    │               │
    │               ▼
    │       MicroBatchConsumerMixin._submit_task()
    │               │
    │               ├─ 累积到缓冲区
    │               │
    │               └─ 达到阈值时调用
    │                       │
    │                       ▼
    │               AbstractConsumer._run_consuming_function()
    │                       │
    │                       ▼
    │               consumer_function()
```

---

## 九、Celery Signal 机制对比

### 9.1 Celery Signal 示例

```python
from celery.signals import (
    task_pre_RUN,
    task_success,
    task_failure,
    task_retry,
    worker_ready,
    worker_shutdown,
)

@task_success.connect
def handle_success(sender=None, result=None, **kwargs):
    """任务成功时"""
    print(f"Task {sender.name} succeeded: {result}")

@task_failure.connect
def handle_failure(sender=None, exception=None, **kwargs):
    """任务失败时"""
    print(f"Task {sender.name} failed: {exception}")
```

### 9.2 Funboost Mixin vs Celery Signal

| 维度 | Funboost Mixin | Celery Signal |
|------|----------------|---------------|
| **类型安全** | ✅ 类型提示完整 | ❌ 运行时才发现错误 |
| **配置方式** | Pydantic 统一配置 | 分散在各模块 |
| **覆盖粒度** | 方法级重写 | 只能注册回调 |
| **组合能力** | 多 Mixin 叠加 | 多 Signal 叠加 |
| **上下文访问** | 直接访问 `self` | 通过 `sender` 传递 |
| **调试难度** | 低 | 中 |

### 9.3 Celery Signal 的局限性

```python
# ❌ Celery 无法拦截任务执行
@task_success.connect
def on_success(sender, result):
    # sender 是 Task 对象，不是 Consumer
    # 无法访问消费者的内部状态
    pass

# ✅ Funboost 可以
class MyMixin(AbstractConsumer):
    def _run_consuming_function(self, kw):
        # 直接访问消费者内部状态
        self._my_state
        super()._run_consuming_function(kw)
```

---

## 十、最佳实践

### 10.1 熔断器最佳实践

```python
class AlertCircuitBreakerMixin(CircuitBreakerConsumerMixin):
    def _on_circuit_open(self, info):
        send_alert(f"熔断: {info['queue_name']}")
    
    def _on_circuit_close(self, info):
        send_recovery(f"恢复: {info['queue_name']}")

@boost(BoosterParams(
    queue_name='api_tasks',
    broker_kind=BrokerEnum.REDIS_ACK_ABLE,
    consumer_override_cls=AlertCircuitBreakerMixin,
    user_options={
        'circuit_breaker_options': {
            'strategy': 'rate',
            'counter_backend': 'redis',
            'errors_rate': 0.3,
            'period': 30,
            'min_calls': 20,
            'recovery_timeout': 120,
        }
    }
))
def api_task(endpoint):
    return call_api(endpoint)
```

### 10.2 微批 + 熔断组合

```python
class ComboMixin(
    MicroBatchConsumerMixin,
    CircuitBreakerConsumerMixin,
    AbstractConsumer
):
    pass

@boost(BoosterParams(
    queue_name='batch_api',
    broker_kind=BrokerEnum.REDIS,
    consumer_override_cls=ComboMixin,
    user_options={
        'micro_batch_size': 50,
        'micro_batch_timeout': 2.0,
        'circuit_breaker_options': {
            'failure_threshold': 3,
        }
    }
))
def batch_api_task(items: list):
    """批量调用 API"""
    return batch_call_api(items)
```

### 10.3 监控 + 告警组合

```python
class MonitoredMixin(
    PrometheusConsumerMixin,
    AlertNotifierConsumerMixin,
    AbstractConsumer
):
    pass

@boost(BoosterParams(
    queue_name='monitored_task',
    broker_kind=BrokerEnum.REDIS,
    consumer_override_cls=MonitoredMixin,
    broker_exclusive_config={
        'prometheus_port': 9090,
    }
))
def monitored_task(x):
    return process(x)
```

---

## 十一、源码位置

| 文件 | 说明 |
|------|------|
| `contrib/override_publisher_consumer_cls/circuit_breaker_mixin.py` | 熔断器实现 |
| `contrib/override_publisher_consumer_cls/funboost_micro_batch_mixin.py` | 微批处理实现 |
| `contrib/override_publisher_consumer_cls/funboost_promethus_mixin.py` | Prometheus 监控 |
| `contrib/override_publisher_consumer_cls/funboost_otel_mixin.py` | OpenTelemetry 追踪 |
| `contrib/override_publisher_consumer_cls/periodic_quota_mixin.py` | 周期额度 |
| `contrib/override_publisher_consumer_cls/alert_notifier_mixin.py` | 告警通知 |
| `consumers/base_consumer.py` | 消费者基类 |

---

## 附录：Mixin 覆盖方法清单

| 方法 | 说明 | 常用场景 |
|------|------|----------|
| `custom_init` | 初始化 | 初始化扩展状态 |
| `_submit_task` | 任务提交 | 拦截/过滤/熔断 |
| `_confirm_consume` | 确认消费 | 自定义确认逻辑 |
| `_requeue` | 重新入队 | 自定义重试逻辑 |
| `_frame_custom_record_process_info_func` | 结果记录 | 更新扩展状态 |
| `_on_circuit_open` | 熔断触发 | 发送告警 |
| `_on_circuit_close` | 熔断恢复 | 发送通知 |

---

*文档版本：v1.0*
*最后更新：2026-05-18*
