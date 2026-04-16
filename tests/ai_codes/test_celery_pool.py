"""
CeleryPool 综合测试 —— threads 并发模式。
需要本地运行 Redis（默认 127.0.0.1:6379）。
"""
import time
import uuid
import concurrent.futures
from funboost.assist.celery_pool import CeleryPool, CeleryFuture


REDIS_URL = 'redis://127.0.0.1:6379/0'


def add(a, b):
    return a + b


def multiply(x, y):
    return x * y


def greet(name):
    return f"Hello, {name}"


def slow_task(sec):
    time.sleep(sec)
    return f"done_{sec}"


def will_raise(x):
    raise ValueError(f"参数 {x} 不合法")


def _make_pool():
    qname = f'test_celery_{uuid.uuid4().hex[:8]}'
    print(f"  使用随机队列名: {qname}")
    return CeleryPool(
        broker_url=REDIS_URL,
        result_backend=REDIS_URL,
        concurrent_num=4,
        pool_type='threads',
        queue_name=qname,
        worker_startup_timeout=8.0,
        worker_loglevel='INFO',
    )


# ============ 测试用例 ============

def test_basic_submit(pool):
    """基本提交 + 获取结果"""
    fut = pool.submit(add, 10, 20)
    result = fut.result(timeout=15)
    assert result == 30, f"期望 30，实际 {result}"
    assert isinstance(fut, CeleryFuture)
    assert isinstance(fut, concurrent.futures.Future)
    print("  [PASS] test_basic_submit")


def test_multiple_submits(pool):
    """连续提交多个不同函数"""
    f1 = pool.submit(add, 5, 3)
    f2 = pool.submit(multiply, 4, 7)
    f3 = pool.submit(greet, name="CeleryPool")

    assert f1.result(timeout=15) == 8
    assert f2.result(timeout=15) == 28
    assert f3.result(timeout=15) == "Hello, CeleryPool"
    print("  [PASS] test_multiple_submits")


def test_map(pool):
    """map 批量提交"""
    results = list(pool.map(add, [1, 2, 3], [10, 20, 30], timeout=20))
    assert results == [11, 22, 33], f"期望 [11,22,33]，实际 {results}"
    print("  [PASS] test_map")


def test_concurrent_submit(pool):
    """并发提交：同时提交多个任务，验证 threads pool 并行执行"""
    futures = []
    for i in range(4):
        futures.append(pool.submit(add, i, i * 10))

    results = [f.result(timeout=20) for f in futures]
    expected = [i + i * 10 for i in range(4)]
    assert results == expected, f"期望 {expected}，实际 {results}"
    print("  [PASS] test_concurrent_submit")


def test_concurrent_slow_tasks(pool):
    """并发慢任务：2 个 2 秒任务，threads pool 应该并行，总时间 < 5 秒"""
    start = time.time()
    futures = [pool.submit(slow_task, 2) for _ in range(2)]
    results = [f.result(timeout=15) for f in futures]
    elapsed = time.time() - start
    assert all(r == "done_2" for r in results), f"结果不对: {results}"
    assert elapsed < 5, f"并发不足：2 个 2s 任务耗时 {elapsed:.1f}s，应 < 5s"
    print(f"  [PASS] test_concurrent_slow_tasks ({elapsed:.1f}s)")


def test_exception(pool):
    """任务异常"""
    fut = pool.submit(will_raise, 42)
    try:
        fut.result(timeout=15)
        assert False, "应该抛异常"
    except Exception as e:
        assert "42" in str(e) or "42" in repr(e), f"异常信息中应包含 '42': {e}"
    print("  [PASS] test_exception")


def test_no_backend():
    """未设置 result_backend 时，调用 result() 报 RuntimeError"""
    pool = CeleryPool(
        broker_url=REDIS_URL,
        result_backend=None,
        queue_name=f'test_nobackend_{uuid.uuid4().hex[:8]}',
        is_auto_start_worker=False,
    )
    fut = pool.submit(add, 1, 2)
    try:
        fut.result(timeout=1)
        assert False, "应该抛 RuntimeError"
    except RuntimeError as e:
        assert "result_backend" in str(e)
    print("  [PASS] test_no_backend")


def test_done_after_result(pool):
    """惰性模式：调用 result() 后 done() 应返回 True"""
    fut = pool.submit(add, 100, 200)
    assert not fut.done(), "惰性模式下 result() 前 done() 应为 False"
    result = fut.result(timeout=15)
    assert result == 300
    assert fut.done(), "result() 后 done() 应为 True"
    print("  [PASS] test_done_after_result")


def test_result_idempotent(pool):
    """多次调用 result() 应返回相同结果"""
    fut = pool.submit(add, 7, 8)
    r1 = fut.result(timeout=15)
    r2 = fut.result(timeout=15)
    r3 = fut.result()
    assert r1 == r2 == r3 == 15
    print("  [PASS] test_result_idempotent")


def test_callback(pool):
    """惰性模式下回调在 result() 触发后执行"""
    callback_results = []

    def on_done(fut):
        callback_results.append(fut.result())

    fut = pool.submit(add, 3, 4)
    fut.add_done_callback(on_done)
    assert fut.result(timeout=15) == 7
    time.sleep(0.2)
    assert callback_results == [7], f"回调结果不对: {callback_results}"
    print("  [PASS] test_callback")


# ============ 主入口 ============

if __name__ == '__main__':
    print("=" * 60)
    print("CeleryPool 测试 — threads 并发模式 (需要本地 Redis)")
    print("=" * 60)

    pool = _make_pool()

    import sys, os
    tests = [
        ("test_basic_submit",       lambda: test_basic_submit(pool)),
        ("test_multiple_submits",   lambda: test_multiple_submits(pool)),
        ("test_map",                lambda: test_map(pool)),
        ("test_concurrent_submit",  lambda: test_concurrent_submit(pool)),
        ("test_concurrent_slow_tasks", lambda: test_concurrent_slow_tasks(pool)),
        ("test_exception",          lambda: test_exception(pool)),
        ("test_no_backend",         lambda: test_no_backend()),
        ("test_done_after_result",  lambda: test_done_after_result(pool)),
        ("test_result_idempotent",  lambda: test_result_idempotent(pool)),
        ("test_callback",          lambda: test_callback(pool)),
    ]
    passed = 0
    for name, fn in tests:
        sys.stdout.write(f"\n>>> 开始 {name} ...\n"); sys.stdout.flush()
        try:
            fn()
            passed += 1
        except Exception as e:
            sys.stdout.write(f"  [FAIL] {name}: {e}\n"); sys.stdout.flush()
        time.sleep(2)

    print()
    print("=" * 60)
    print(f"{passed}/{len(tests)} 个测试通过")
    print("=" * 60)
    os._exit(0)
