# -*- coding: utf-8 -*-
"""
测试 NATS_CORE 中间件 (无持久化，高性能)

使用方式：
    1. 确保 NATS 服务器已启动 (默认 nats://192.168.6.134:4222)
    2. pip install nats-py
    3. 运行此脚本

NATS Core 特点：
    - 轻量高性能，适用于对延迟敏感但不需要持久化的场景
    - 不支持持久化和消费确认，消息丢失风险由业务层自行处理
    - 支持 Queue Group（消费者组），多个消费者实例可负载均衡分摊消息
    - queue_group 非空 = 负载均衡模式（默认）
    - queue_group 为空字符串 = 广播模式
"""
import time
from funboost import boost, BoosterParams, BrokerEnum


@boost(BoosterParams(
    queue_name='nats_core_test_queue',
    broker_kind=BrokerEnum.NATS_CORE,
    broker_exclusive_config={'nats_url': 'nats://127.0.0.1:4222'},
    qps=10,
    concurrent_num=5,
))
def nats_core_task(x: int, y: int):
    result = x + y
    print(f'[NATS_CORE] 计算: {x} + {y} = {result}')
    time.sleep(0.5)
    return result


@boost(BoosterParams(
    queue_name='nats_core_broadcast_queue',
    broker_kind=BrokerEnum.NATS_CORE,
    broker_exclusive_config={'nats_url': 'nats://127.0.0.1:4222', 'queue_group': ''},
    qps=10,
    concurrent_num=5,
))
def nats_core_broadcast_task(msg: str):
    print(f'[NATS_CORE 广播模式] 收到消息: {msg}')
    time.sleep(0.3)
    return True


if __name__ == '__main__':
    print('=== 先启动消费 (NATS Core 无持久化, 必须先启动消费者再发布消息) ===')
    nats_core_task.consume()
    nats_core_broadcast_task.consume()

    import time
    time.sleep(2)

    print('=== 发布消息到 NATS_CORE 队列 ===')
    for i in range(10):
        nats_core_task.push(x=i, y=i * 10)

    print('=== 发布消息到 NATS_CORE 广播队列 ===')
    for i in range(5):
        nats_core_broadcast_task.push(msg=f'broadcast_msg_{i}')

    from funboost import ctrl_c_recv
    ctrl_c_recv()
