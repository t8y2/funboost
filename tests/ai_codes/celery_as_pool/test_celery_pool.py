"""
CeleryPool 使用示例 —— 与 FunboostPool / ThreadPoolExecutor 的 API 对比。

运行前提：
  1. 已安装 celery:  pip install celery[redis]
  2. 本机 Redis 可用: redis://localhost:6379/0

运行方式：
  cd 到项目根目录后：
  python tests/ai_codes/celery_as_pool/test_celery_pool.py
"""

import time
# import nb_log

# ---------- 业务函数（必须是顶层可导入的，与 FunboostPool 约束一致） ----------

def add(a, b):
    return a + b


def multiply(x, y):
    return x * y


def greet(name):
    return f"Hello, {name}!"


def slow_task(seconds):
    time.sleep(seconds)
    return f"slept {seconds}s"


# ---------- CeleryPool 演示 ----------

def demo_celery_pool():
    from celery_pool import CeleryPool

    pool = CeleryPool(
        broker_url='redis://localhost:6379/0',
        result_backend='redis://localhost:6379/0',
        concurrent_num=4,
        pool_type='threads',
        queue_name='celery_pool_demo',
        worker_loglevel='WARNING',
        worker_startup_timeout=5,
    )

    # ---- 基本 submit ----
    f1 = pool.submit(add, 5, 3)
    f2 = pool.submit(multiply, 4, 7)
    f3 = pool.submit(greet, name="Celery")

    print(f"  add(5,3)          = {f1.result(timeout=10)}")
    print(f"  multiply(4,7)     = {f2.result(timeout=10)}")
    print(f"  greet('Celery')   = {f3.result(timeout=10)}")

    # ---- map 批量提交 ----
    results = list(pool.map(add, [1, 2, 3], [10, 20, 30], timeout=10))
    print(f"  map(add, ...)     = {results}")

    print("\n基础测试通过！")
    print("CeleryPool worker 进程保持运行中，主进程不会自动退出（daemon=False 线程保活）")
    print("可以继续在其他地方使用 pool.submit() 提交任务")


if __name__ == '__main__':
    print("=" * 60)
    print("CeleryPool 演示 —— 与 ThreadPoolExecutor / FunboostPool 同 API")
    print("=" * 60)
    demo_celery_pool()
