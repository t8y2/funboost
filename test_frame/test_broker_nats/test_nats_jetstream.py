# -*- coding: utf-8 -*-
"""
测试 NATS_JETSTREAM 中间件 (持久化模式，支持ACK/消费者组)

使用方式：
    1. 确保 NATS 服务器已启动且启用了 JetStream (默认 nats://127.0.0.1:4222)
    2. pip install nats-py
    3. 运行此脚本

NATS JetStream 特点：
    - 持久化消费（durable consumer），重启不丢失消费位置
    - 支持消费确认（ACK），未确认的消息会重投
    - 支持消费者组（多个消费者分摊消息）
    - Pull 模式拉取消息
    - 适用于需要可靠消息传递但不想部署 RabbitMQ/Kafka 重型中间件的场景
"""
import time
from funboost import boost, BoosterParams, BrokerEnum


@boost(BoosterParams(
    queue_name='jetstream_test_queue',
    broker_kind=BrokerEnum.NATS_JETSTREAM,
    broker_exclusive_config={
        'nats_url': 'nats://127.0.0.1:4222', # 可以独立优先配置，也可以使用funboost_config.py 的 NATS_URL  全局配置
        'consumer_group': 'test_group',
        'ack_wait': 60,
        'max_deliver': 3,
    },
    qps=10,
    concurrent_num=5,
    max_retry_times=2,
))
def jetstream_task(x: int, y: int):
    result = x * y
    print(f'[NATS_JETSTREAM] 计算: {x} * {y} = {result}')
    time.sleep(0.5)
    return result


@boost(BoosterParams(
    queue_name='jetstream_order_queue',
    broker_kind=BrokerEnum.NATS_JETSTREAM,
    broker_exclusive_config={
        'consumer_group': 'order_group',
        'ack_wait': 30,
        'max_deliver': 5,
    },
    qps=5,
    concurrent_num=3,
    max_retry_times=3,
))
def jetstream_order_task(order_id: str, amount: float):
    print(f'[NATS_JETSTREAM] 处理订单: order_id={order_id}, amount={amount}')
    time.sleep(1)
    return {'order_id': order_id, 'status': 'processed'}


if __name__ == '__main__':
    print('=== 发布消息到 JetStream 队列 ===')
    for i in range(10):
        jetstream_task.push(x=i, y=i + 1)

    print('=== 发布订单消息到 JetStream 队列 ===')
    for i in range(5):
        jetstream_order_task.push(order_id=f'ORD_{i:04d}', amount=99.5 + i)

    print('=== 启动消费 ===')
    jetstream_task.consume()
    jetstream_order_task.consume()

