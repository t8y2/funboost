# -*- coding: utf-8 -*-
"""
CeleryPool 最简用法 demo
========================

CeleryPool 将 Celery 封装为 concurrent.futures.Executor 兼容接口，
无需 @app.task 装饰器、无需手动启动 worker，3 行代码即可使用分布式任务能力。

运行前提：
  1. pip install celery[redis]
  2. 本机 Redis 可用: redis://localhost:6379/0

运行方式：
  D:\\ProgramData\\miniconda3\\envs\\py39b\\python.exe test_frame/celery_pool_demos/demo_celery_pool.py
"""

import time

from funboost.assist.celery_pool import CeleryPool


def add(a, b):
    return a + b


def multiply(x, y):
    return x * y


if __name__ == '__main__':
    REDIS_URL = 'redis://localhost:6379/0'

    pool = CeleryPool(
        broker_url=REDIS_URL,
        result_backend=REDIS_URL,
        queue_name='demo_celery_pool_queue',
    )

    # 1. 基本 submit + result
    future = pool.submit(add, 1, 2)
    print(f'add(1, 2) = {future.result(timeout=10)}')

    # 2. 多任务提交
    f1 = pool.submit(add, 10, 20)
    f2 = pool.submit(multiply, 3, 7)
    print(f'add(10, 20) = {f1.result(timeout=10)}')
    print(f'multiply(3, 7) = {f2.result(timeout=10)}')

    # 3. map 批量提交
    results = list(pool.map(add, [1, 2, 3], [10, 20, 30], timeout=10))
    print(f'map(add, ...) = {results}')

    print('\ndemo 完成！')
    import os
    time.sleep(10)
    os._exit(0)
