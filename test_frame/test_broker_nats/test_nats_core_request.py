# -*- coding: utf-8 -*-
"""
测试 NATS_CORE Request-Reply 模式

验证：
    1. 普通的 publish/push 消费仍然正常
    2. request() 发送消息后能同步等待消费者响应结果
    3. 消费者端无需任何修改，框架自动检测 request 消息并响应
"""
import time
import json
from funboost import boost, BoosterParams, BrokerEnum


@boost(BoosterParams(
    queue_name='nats_core_rpc_queue',
    broker_kind=BrokerEnum.NATS_CORE,
    broker_exclusive_config={'nats_url': 'nats://127.0.0.1:4222'},
    qps=10,
    concurrent_num=5,
))
def rpc_add(x: int, y: int):
    result = x + y
    print(f'[NATS_CORE RPC] 计算: {x} + {y} = {result}')
    time.sleep(0.3)
    return result


@boost(BoosterParams(
    queue_name='nats_core_rpc_echo_queue',
    broker_kind=BrokerEnum.NATS_CORE,
    broker_exclusive_config={'nats_url': 'nats://127.0.0.1:4222'},
    qps=10,
    concurrent_num=5,
))
def rpc_echo(name: str, greeting: str):
    msg = f'{greeting}, {name}!'
    print(f'[NATS_CORE RPC] 回显: {msg}')
    time.sleep(0.2)
    return msg


if __name__ == '__main__':
    print('=== 先启动消费 ===')
    rpc_add.consume()
    rpc_echo.consume()

    time.sleep(2)

    print('\n=== 测试1: publisher.request() 同步等待响应 ===')
    for i in range(5):
        response_bytes = rpc_add.publisher.request({"x": i, "y": i * 10}, timeout=5)
        result = json.loads(response_bytes)
        print(f'  request({i}, {i * 10}) -> 响应: {result}')

    print('\n=== 测试2: publisher.request() 字符串返回值 ===')
    response_bytes = rpc_echo.publisher.request({"name": "funboost", "greeting": "Hello"}, timeout=5)
    result = json.loads(response_bytes)
    print(f'  request(echo) -> 响应: {result}')

    print('\n=== 测试3: 普通 push 仍然正常 ===')
    for i in range(3):
        rpc_add.push(x=i + 100, y=i + 200)

    time.sleep(3)
    print('\n=== 测试完成 ===')
