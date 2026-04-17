# -*- coding: utf-8 -*-
"""
CELERY_POOL 作为 funboost 自定义 broker 的最简 demo
====================================================

将 CeleryPool 注册为 funboost 的 broker_kind，
通过 @boost 装饰器即可使用 Celery 作为消息队列后端。

运行前提：
  1. pip install celery[redis]
  2. 本机 Redis 可用: redis://localhost:6379/0

运行方式：
  D:\\ProgramData\\miniconda3\\envs\\py39b\\python.exe test_frame/celery_pool_demos/demo_celery_pool_as_broker.py
"""

import time

from funboost import boost, BoosterParams
from funboost.contrib.register_custom_broker_contrib.celery_pool_as_funboost_broker import (
    BROKER_KIND_CELERY_POOL,
)


@boost(BoosterParams(
    queue_name='demo_celery_broker_queue3',
    broker_kind=BROKER_KIND_CELERY_POOL,
    concurrent_num=2,
    broker_exclusive_config={
        'broker_url': 'redis://localhost:6379/0',
        'result_backend': 'redis://localhost:6379/0',
        'concurrent_num': 4,
        'pool_type': 'threads',
        'worker_loglevel': 'INFO',
        'worker_startup_timeout': 5.0,
    }
))
def add(x, y):
    print(f'  [add] {x} + {y} = {x + y}')
    return x + y


if __name__ == '__main__':
    print(add.publisher.get_message_count())
    add.publisher.clear()
    add.consume()

    time.sleep(2)
    for i in range(5):
        add.push(x=i, y=i * 10)
    print(add.publisher.get_message_count())
    rs = add.push(x=1, y=2)
    print(f'add(1, 2) 结果: {rs.get(timeout=10)}')

    time.sleep(5)
    print('\ndemo 完成！')
    import os
    os._exit(0)
