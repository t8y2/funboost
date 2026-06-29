# -*- coding: utf-8 -*-
"""
测试 REDIS_ZSET_PRIORITY — 基于 Redis ZSet 的优先级队列 Broker

验证要点：
1. priority 越大的消息越先被消费
2. 确认消费（ACK）正常工作
3. 不指定 priority 时默认 priority=0
"""

import random
import time

from funboost import boost, BoosterParams, TaskOptions, enable_ctrl_c_quit_on_windows
from funboost.constant import BrokerEnum

consumed_order = []


@boost(BoosterParams(
    queue_name='test_zset_priority_queue3',
    broker_kind=BrokerEnum.REDIS_ZSET_PRIORITY,
    qps=3,
    concurrent_num=1,
    broker_exclusive_config={
        'pull_msg_batch_size': 8,
    },
))
def priority_task(x, priority_val):
    consumed_order.append((x, priority_val))
    print(f'[消费] x={x}, priority={priority_val}, 已消费 {len(consumed_order)} 条')


def test_priority():
    priority_task.clear()
    time.sleep(0.5)

    print('--- 发布 20 条不同优先级的消息 ---')
    for i in range(20):
        p = random.randint(0, 100)
        priority_task.publish(
            {'x': i, 'priority_val': p},
            task_options=TaskOptions(other_extra_params={
                'for_broker_redis_zset_priority': {'priority': p}
            }),
        )
        print(f'  发布 x={i}, priority={p}')

    print(f'队列消息数量: {priority_task.get_message_count()}')
    print('--- 开始消费（观察消费顺序应为 priority 从大到小）---')


if __name__ == '__main__':
    test_priority()
    priority_task.consume()
    enable_ctrl_c_quit_on_windows()
