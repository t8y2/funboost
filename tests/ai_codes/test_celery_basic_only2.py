"""最小化 CeleryPool 测试：只测 basic_submit，无 sys.argv"""
import time
import uuid
from funboost.assist.celery_pool import CeleryPool, CeleryFuture

REDIS_URL = 'redis://127.0.0.1:6379/0'

def add(a, b):
    return a + b


def test2():
    print(">>> 创建 pool...")
    pool = CeleryPool(
        broker_url=REDIS_URL,
        result_backend=REDIS_URL,
        concurrent_num=4,
        pool_type='threads',
        queue_name=f'test_basic_{uuid.uuid4().hex[:8]}',
        worker_startup_timeout=10.0,
        worker_loglevel='INFO',
    )
    print(">>> pool 创建完毕, worker 应已就绪")
    print(">>> 提交 add(10, 20)...")
    fut = pool.submit(add, 10, 20)
    print(">>> 任务已提交, 调用 result(timeout=15)...")
    result = fut.result(timeout=15)
    print(f">>> 结果: {result}")
    assert result == 30, f"期望 30, 实际 {result}"
    print(">>> [PASS] basic test")



if __name__ == '__main__':
    test2()
    