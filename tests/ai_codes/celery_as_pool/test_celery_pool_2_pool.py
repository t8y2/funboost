"""
一个脚本中实例化 2 个不同的 CeleryPool，各自独立队列、独立 worker。

运行前提：
  1. pip install celery[redis]
  2. 本机 Redis 可用: redis://localhost:6379/0

运行：
  python tests/ai_codes/celery_as_pool/test_celery_pool_2_pool.py
"""

import time


def add(a, b):
    return a + b


def multiply(x, y):
    return x * y


def slow_add(a, b):
    time.sleep(1)
    return a + b


def format_result(name, value):
    return f"{name}={value}"


if __name__ == '__main__':
    from celery_pool import CeleryPool

    # ---- Pool A：加法池，2 并发 ----
    pool_a = CeleryPool(
        broker_url='redis://localhost:6379/0',
        result_backend='redis://localhost:6379/0',
        concurrent_num=2,
        pool_type='threads',
        queue_name='pool_a_add',
        worker_loglevel='WARNING',
        worker_startup_timeout=5,
    )

    # ---- Pool B：乘法池，3 并发 ----
    pool_b = CeleryPool(
        broker_url='redis://localhost:6379/0',
        result_backend='redis://localhost:6379/0',
        concurrent_num=3,
        pool_type='threads',
        queue_name='pool_b_multiply',
        worker_loglevel='WARNING',
        worker_startup_timeout=5,
    )

    print("=" * 60)
    print("两个 CeleryPool 各自独立运行")
    print("=" * 60)

    # 向 Pool A 提交加法任务
    fa1 = pool_a.submit(add, 10, 20)
    fa2 = pool_a.submit(add, 100, 200)
    fa3 = pool_a.submit(slow_add, 1, 2)

    # 向 Pool B 提交乘法任务
    fb1 = pool_b.submit(multiply, 3, 7)
    fb2 = pool_b.submit(multiply, 5, 5)
    fb3 = pool_b.submit(format_result, "answer", 42)

    print(f"  Pool A - add(10,20)           = {fa1.result(timeout=10)}")
    print(f"  Pool A - add(100,200)         = {fa2.result(timeout=10)}")
    print(f"  Pool A - slow_add(1,2)        = {fa3.result(timeout=10)}")
    print(f"  Pool B - multiply(3,7)        = {fb1.result(timeout=10)}")
    print(f"  Pool B - multiply(5,5)        = {fb2.result(timeout=10)}")
    print(f"  Pool B - format_result(...)   = {fb3.result(timeout=10)}")

    # 交叉提交：Pool A 执行乘法，Pool B 执行加法（函数不绑定池）
    print("\n交叉提交：同一函数可以提交到不同的 Pool")
    fc1 = pool_a.submit(multiply, 6, 6)
    fc2 = pool_b.submit(add, 999, 1)
    print(f"  Pool A - multiply(6,6)  = {fc1.result(timeout=10)}")
    print(f"  Pool B - add(999,1)     = {fc2.result(timeout=10)}")

    print("\n全部通过！两个 Pool 独立运行，互不干扰。")
