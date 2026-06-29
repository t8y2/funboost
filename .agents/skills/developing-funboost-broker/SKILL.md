---
name: developing-funboost-broker
description: 当需要为 funboost 框架添加新的消息中间件时使用。触发场景：实现自定义 Publisher/Consumer 类、使用 register_custom_broker 注册新 broker、使用 override_cls 定制现有 broker 行为。关键词：new broker, AbstractPublisher, AbstractConsumer, register_custom_broker, consumer_override_cls, publisher_override_cls, 扩展中间件, 新增 broker。
compatibility: Python 3.7+, funboost source code access
---

# 开发 Funboost Broker 中间件

## 概述

Funboost 支持 3 种方式添加新 broker：静态扩展（框架作者）、`register_custom_broker`（新中间件）、`override_cls`（mixin 定制）。

**核心原则：** 实现抽象方法，正确注册。非抽象方法一般应调用 `super()`（完全替换父类逻辑时除外）。

## 适用场景

- 为 funboost 添加全新的消息队列后端
- 使用 override_cls 定制现有 broker 行为
- 用 `register_custom_broker` 在用户空间注册 broker
- 修改特定场景的发布/消费流程

## 三种扩展方式

| 方式 | 适用场景 | 是否修改源码 |
|------|----------|-------------|
| 静态扩展 | 框架作者添加核心 broker | 是 |
| `register_custom_broker` | 用户添加全新 broker | 否 |
| `consumer_override_cls` / `publisher_override_cls` | 用户定制现有 broker 行为 | 否 |

## 方式一：静态扩展（框架作者）

需要修改的文件清单：

1. **`funboost/constant.py`** — 在 `BrokerEnum` 中增加枚举
2. **`funboost/funboost_config_deafult.py`** — 在 `BrokerConnConfig` 中添加连接配置（如需）
3. **`funboost/core/broker_kind__exclusive_config_default_define.py`** — 注册专属配置默认值
4. **`funboost/publishers/`** — 创建新的 publisher 文件
5. **`funboost/consumers/`** — 创建新的 consumer 文件
6. **`funboost/factories/broker_kind__publsiher_consumer_type_map.py`** — 注册映射

## 方式二：register_custom_broker（用户空间）

```python
from funboost import register_custom_broker, boost, BoosterParams
from funboost.publishers.base_publisher import AbstractPublisher
from funboost.consumers.base_consumer import AbstractConsumer

class MyPublisher(AbstractPublisher):
    def custom_init(self):
        super().custom_init()
        self._client = connect_to_my_mq()

    def _publish_impl(self, msg: str):
        self._client.send(self.queue_name, msg)

    def clear(self):
        self._client.purge(self.queue_name)

    def get_message_count(self):
        return self._client.queue_length(self.queue_name)

    def close(self):
        self._client.close()

class MyConsumer(AbstractConsumer):
    def custom_init(self):
        super().custom_init()
        self._client = connect_to_my_mq()

    def _dispatch_task(self):
        while True:
            msg = self._client.receive(self.queue_name, timeout=5)
            if msg:
                kw = {"body": msg.body, "raw_msg": msg}
                self._submit_task(kw)

    def _confirm_consume(self, kw):
        kw["raw_msg"].ack()

    def _requeue(self, kw):
        self._client.send(self.queue_name, kw["body"])

# 注册
register_custom_broker("MY_BROKER", MyPublisher, MyConsumer)

# 使用
@boost(BoosterParams(queue_name="test", broker_kind="MY_BROKER"))
def my_task(x):
    return x * 2
```

## 方式三：override_cls（Mixin 混入）

```python
from funboost import boost, BoosterParams, BrokerEnum

class MyConsumerMixin:
    """Mixin 混入到任意 broker 的 consumer 中"""

    def _submit_task(self, kw):
        self._pre_check(kw)
        super()._submit_task(kw)

    def _pre_check(self, kw):
        pass

@boost(BoosterParams(
    queue_name="custom_task",
    broker_kind=BrokerEnum.REDIS_ACK_ABLE,
    consumer_override_cls=MyConsumerMixin,
))
def my_task(x):
    return x
```

## Publisher 必须实现的方法

| 方法 | 是否抽象 | 说明 |
|------|----------|------|
| `_publish_impl(msg: str)` | 是 | 核心发布逻辑——**必须实现**。`msg` 是 JSON 字符串（由框架序列化后传入） |
| `clear()` | 是 | 清空队列所有消息 |
| `get_message_count()` | 是 | 返回队列深度 |
| `close()` | 是 | 关闭连接（可以写 `pass`） |
| `custom_init()` | 否 | 可选的初始化钩子 |

> **注意：** `_publish_impl` 接收的 `msg` 已经是 JSON 字符串，直接写入中间件即可。框架在调用 `_publish_impl` 之前已完成参数序列化和 extra 字段注入。

## Consumer 必须实现的方法

| 方法 | 是否抽象 | 说明 |
|------|----------|------|
| `_dispatch_task()` | 是 | 主循环：取消息，调用 `self._submit_task(kw)` |
| `_confirm_consume(kw)` | 是 | 确认消费（ACK） |
| `_requeue(kw)` | 是 | 消息重入队 |
| `custom_init()` | 否 | 可选的初始化钩子 |

### `_dispatch_task` 两种实现模式

**模式 A：自带循环**（适合长连接 broker，如 RabbitMQ/Kafka）：

```python
def _dispatch_task(self):
    while True:
        msg = self._client.receive(timeout=5)
        if msg:
            self._submit_task({"body": msg.body, "raw_msg": msg})
```

**模式 B：单次取消息**（框架通过 `___keep_circulating` 自动重复调用）：

```python
def _dispatch_task(self):
    msg = self._client.poll(timeout=0.5)
    if msg:
        self._submit_task({"body": msg.body})
```

两种模式均正确。模式 B 更简洁，框架自动处理异常重试和循环。

## kw 字典结构

传给 `_submit_task` 的 kw 字典必须包含：

```python
kw = {
    "body": message_body_string,  # JSON 字符串（与 _publish_impl 收到的 msg 相同）
    # broker 特有字段，用于 ack/requeue：
    # "receipt_handle": ...,  # SQS 用
    # "message": ...,         # AMQP 用
    # "channel": ...,         # RabbitMQ 用
}
```

> **重要：** `kw["body"]` 必须是字符串类型（JSON string），不能是 dict。框架会在 `_submit_task` 内部调用 `_convert_msg_before_run` 做反序列化。

## super() 调用规则

| 场景 | 必须调 super()？ | 调用位置 |
|------|------------------|----------|
| `custom_init()` | 是 | 先调 super()，再执行自己的初始化 |
| `_submit_task()` 重写 | 是 | 先执行前置逻辑，再调 super() |
| `_run()` / `_async_run()` | 是 | 在自己的上下文中包裹 super() |
| `_publish_impl()` | 否 | 抽象方法——直接实现 |
| `_dispatch_task()` | 否 | 抽象方法——直接实现 |
| `_confirm_consume()` | 否 | 抽象方法——直接实现 |

## broker_exclusive_config 访问规范

```python
# 在 consumer 中
value = self.consumer_params.broker_exclusive_config["my_key"]

# 在 publisher 中
value = self.publisher_params.broker_exclusive_config["my_key"]
```

**推荐用 `[]` 方括号访问（缺失 key 抛 KeyError）——新 broker 中已注册的 key 推荐用 `[]`。**

在 `broker_kind__exclusive_config_default_define.py` 中注册默认值：

```python
register_broker_exclusive_config_default("MY_BROKER", {
    "my_key": "default_value",
})
```

## 参考代码位置

- 基础 publisher：`funboost/publishers/base_publisher.py`
- 基础 consumer：`funboost/consumers/base_consumer.py`
- 动态扩展示例：`funboost/contrib/register_custom_broker_contrib/`
- Mixin 示例：`funboost/contrib/override_publisher_consumer_cls/`
- 工厂注册：`funboost/factories/broker_kind__publsiher_consumer_type_map.py`

## 常见错误

| 错误 | 修正 |
|------|------|
| 非抽象方法忘记调 `super()` | 除抽象方法外始终调用 super() |
| exclusive_config 用 `.get()` | 推荐用 `[]` 方括号访问已注册的 key |
| `_dispatch_task` 中没调 `self._submit_task(kw)` | 每条消息必须调用此方法 |
| kw 字典缺少 `body` 键 | `_submit_task` 必须有 `kw["body"]` |
| 过度防御性编程（到处 try） | funboost 偏好简洁代码，让异常正常抛出 |
| 静态扩展后没注册到工厂映射 | 必须在 `broker_kind__publsiher_consumer_type_map.py` 中注册 |

## 测试新 Broker

实现后编写测试验证功能：
- AI 写测试放在 `tests/ai_codes/regression_testing/` 或 `tests/ai_codes/ai_demos/{子文件夹}/`
- 发布消息 -> 启动消费 -> 验证消费结果
- 运行约 30 秒后 kill（funboost 不会自动停止）
- AI 测试时使用 `timeout` 或 `os._exit` 自动终止
