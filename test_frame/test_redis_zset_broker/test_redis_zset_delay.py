# -*- coding: utf-8 -*-
"""
测试 REDIS_ZSET_DELAY — 基于 Redis ZSet 的延迟队列 Broker

验证要点：
1. delay_seconds 指定的消息在延迟后才被消费
2. eta_timestamp 指定的消息在到达指定时间后才被消费
3. 不指定延迟参数的消息立即可消费
4. 确认消费（ACK）正常工作
"""

import time

from funboost import boost, BoosterParams, TaskOptions, ctrl_c_recv
from funboost.constant import BrokerEnum


@boost(BoosterParams(
    queue_name='test_zset_delay_queue3',
    broker_kind=BrokerEnum.REDIS_ZSET_DELAY,
    qps=5,
    concurrent_num=2,
    broker_exclusive_config={
        'pull_msg_batch_size': 8,
        'pull_base_interval': 0.5,
    },
))
def delay_task(x, desc):
    print(f'[消费 @ {time.strftime("%H:%M:%S")}] x={x}, {desc}')


def test_delay():
    delay_task.clear()
    time.sleep(0.5)

    now = time.time()
    print(f'当前时间: {time.strftime("%H:%M:%S")}')

    delay_task.publish({'x': 1, 'desc': '无延迟，立即可消费'})

    delay_task.publish(
        {'x': 2, 'desc': '延迟 10 秒'},
        task_options=TaskOptions(other_extra_params={
            'for_broker_redis_zset_delay': {'delay_seconds': 10}
        }),
    )

    delay_task.publish(
        {'x': 3, 'desc': '延迟 20 秒'},
        task_options=TaskOptions(other_extra_params={
            'for_broker_redis_zset_delay': {'delay_seconds': 20}
        }),
    )

    delay_task.publish(
        {'x': 4, 'desc': f'eta_timestamp={now + 30:.0f}，约 30 秒后消费'},
        task_options=TaskOptions(other_extra_params={
            'for_broker_redis_zset_delay': {'eta_timestamp': now + 30}
        }),
    )

    delay_task.publish(
        {'x': 5, 'desc': '延迟 5 秒'},
        task_options=TaskOptions(other_extra_params={
            'for_broker_redis_zset_delay': {'delay_seconds': 5}
        }),
    )

    print(f'队列消息数量: {delay_task.get_message_count()}')
    print('--- 开始消费（观察消息应按 到期时间 依次出现）---')
    print(f'  预期顺序: x=1(立即) → x=5(5s后) → x=2(10s后) → x=3(20s后) → x=4(30s后)')


if __name__ == '__main__':
    test_delay()
    delay_task.consume()
    ctrl_c_recv()
