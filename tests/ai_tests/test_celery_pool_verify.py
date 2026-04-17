"""
验证 funboost/assist/celery_pool.py 的正确性。

测试分为两部分：

  Part A — 单元测试（无需 Redis）
    1. 单例模式：相同 queue_name 返回同一实例
    2. 单例模式：不同 queue_name 返回不同实例
    3. 初始化守卫：单例实例不会被二次初始化
    4. Celery app 命名：app.main 包含 queue_name
    5. start_worker 是公有方法（无下划线前缀）
    6. CeleryFuture 无 backend 时抛 RuntimeError
    7. _FUNC_REGISTRY 注册机制
    8. 线程安全单例：多线程并发创建同一 queue_name 只得到一个实例

  Part B — 集成测试（需要本地 Redis）
    9.  submit + result 基本功能
    10. 多任务提交
    11. map 批量提交
    12. 异常传播
    13. 惰性解析 done() 行为
    14. result 幂等性

运行方式：
    python tests/ai_tests/test_celery_pool_verify.py               # 全部测试
    python tests/ai_tests/test_celery_pool_verify.py --unit-only    # 仅单元测试（跳过 Redis 集成测试）
"""

import sys
import os
import functools
import time
import uuid
import threading
import concurrent.futures

print = functools.partial(print, flush=True)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from funboost.assist.celery_pool import (
    CeleryPool, CeleryFuture, _pool_cache, _pool_cache_lock,
    _get_func_path, _FUNC_REGISTRY,
)


REDIS_URL = 'redis://127.0.0.1:6379/0'


def _clear_pool_cache():
    """清除单例缓存，确保测试隔离。"""
    with _pool_cache_lock:
        for p in list(_pool_cache.values()):
            try:
                p.app.close()
            except Exception:
                pass
        _pool_cache.clear()


def _make_pool_no_worker(queue_name=None):
    """创建 CeleryPool 但不启动 worker（单元测试用）。"""
    qname = queue_name or f'ut_{uuid.uuid4().hex[:8]}'
    return CeleryPool(
        broker_url=REDIS_URL,
        queue_name=qname,
        is_auto_start_worker=False,
    )


# ========================================================================
# Part A: 单元测试（无需 Redis）
# ========================================================================

def test_singleton_same_queue():
    """相同 queue_name 返回同一实例"""
    _clear_pool_cache()
    qname = f'singleton_{uuid.uuid4().hex[:8]}'
    p1 = _make_pool_no_worker(qname)
    p2 = _make_pool_no_worker(qname)
    assert p1 is p2, f"同 queue_name 应返回同一实例: id(p1)={id(p1)}, id(p2)={id(p2)}"
    print("  [PASS] test_singleton_same_queue")


def test_singleton_diff_queue():
    """不同 queue_name 返回不同实例"""
    _clear_pool_cache()
    p1 = _make_pool_no_worker(f'diff_a_{uuid.uuid4().hex[:8]}')
    p2 = _make_pool_no_worker(f'diff_b_{uuid.uuid4().hex[:8]}')
    assert p1 is not p2, "不同 queue_name 应返回不同实例"
    print("  [PASS] test_singleton_diff_queue")


def test_init_guard():
    """单例实例的 __init__ 不会被二次执行"""
    _clear_pool_cache()
    qname = f'guard_{uuid.uuid4().hex[:8]}'
    p1 = CeleryPool(
        broker_url=REDIS_URL,
        queue_name=qname,
        is_auto_start_worker=False,
        concurrent_num=4,
    )
    original_concurrent_num = p1.concurrent_num

    p2 = CeleryPool(
        broker_url=REDIS_URL,
        queue_name=qname,
        is_auto_start_worker=False,
        concurrent_num=99,
    )
    assert p1 is p2
    assert p2.concurrent_num == original_concurrent_num, (
        f"初始化守卫失效：concurrent_num 应保持 {original_concurrent_num}，"
        f"实际为 {p2.concurrent_num}"
    )
    assert getattr(p1, '_initialized', False) is True
    print("  [PASS] test_init_guard")


def test_celery_app_naming():
    """Celery app.main 应包含 queue_name，多实例名称不冲突"""
    _clear_pool_cache()
    q1 = f'naming_a_{uuid.uuid4().hex[:8]}'
    q2 = f'naming_b_{uuid.uuid4().hex[:8]}'
    p1 = _make_pool_no_worker(q1)
    p2 = _make_pool_no_worker(q2)
    assert q1 in p1.app.main, f"app.main 应包含 queue_name: got '{p1.app.main}'"
    assert q2 in p2.app.main, f"app.main 应包含 queue_name: got '{p2.app.main}'"
    assert p1.app.main != p2.app.main, (
        f"不同 queue 的 app.main 应不同: '{p1.app.main}' vs '{p2.app.main}'"
    )
    print("  [PASS] test_celery_app_naming")


def test_start_worker_is_public():
    """start_worker 是公有方法（无下划线前缀）"""
    _clear_pool_cache()
    p = _make_pool_no_worker()
    assert hasattr(p, 'start_worker'), "CeleryPool 应有 start_worker 方法"
    assert callable(p.start_worker), "start_worker 应是可调用的"
    assert not hasattr(p, '_start_worker'), "不应存在 _start_worker 私有方法"
    print("  [PASS] test_start_worker_is_public")


def test_celery_future_no_backend():
    """未设置 result_backend 时调用 result() 应抛 RuntimeError（无需 Redis）"""
    from unittest.mock import MagicMock
    mock_cr = MagicMock()
    fut = CeleryFuture(mock_cr, has_backend=False)
    try:
        fut.result(timeout=1)
        assert False, "应抛 RuntimeError"
    except RuntimeError as e:
        assert 'result_backend' in str(e), f"异常消息应包含 'result_backend': {e}"
    print("  [PASS] test_celery_future_no_backend")


def test_func_registry():
    """_get_func_path 应注册函数到 _FUNC_REGISTRY"""
    def my_test_func(x):
        return x * 2

    path = _get_func_path(my_test_func)
    assert path.endswith('my_test_func'), f"func_path 应以函数名结尾: got '{path}'"
    assert path in _FUNC_REGISTRY, f"函数应被注册到 _FUNC_REGISTRY"
    assert _FUNC_REGISTRY[path] is my_test_func, "注册的应是原函数引用"
    print("  [PASS] test_func_registry")


def test_thread_safe_singleton():
    """多线程并发创建同一 queue_name 只得到一个实例"""
    _clear_pool_cache()
    qname = f'threadsafe_{uuid.uuid4().hex[:8]}'
    results = []
    barrier = threading.Barrier(8)

    def create_pool():
        barrier.wait()
        p = CeleryPool(
            broker_url=REDIS_URL,
            queue_name=qname,
            is_auto_start_worker=False,
        )
        results.append(id(p))

    threads = [threading.Thread(target=create_pool) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10)

    unique_ids = set(results)
    assert len(unique_ids) == 1, (
        f"8 个线程应得到同一实例，实际得到 {len(unique_ids)} 个不同实例: {unique_ids}"
    )
    print("  [PASS] test_thread_safe_singleton")


def test_pool_cache_populated():
    """创建实例后 _pool_cache 应有记录"""
    _clear_pool_cache()
    qname = f'cache_{uuid.uuid4().hex[:8]}'
    p = _make_pool_no_worker(qname)
    assert qname in _pool_cache, f"_pool_cache 应包含 queue_name '{qname}'"
    assert _pool_cache[qname] is p
    print("  [PASS] test_pool_cache_populated")


def test_celery_future_inherits_future():
    """CeleryFuture 应是 concurrent.futures.Future 的子类"""
    from unittest.mock import MagicMock
    assert issubclass(CeleryFuture, concurrent.futures.Future), (
        "CeleryFuture 应继承 concurrent.futures.Future"
    )
    mock_cr = MagicMock()
    fut = CeleryFuture(mock_cr, has_backend=True)
    assert isinstance(fut, CeleryFuture)
    assert isinstance(fut, concurrent.futures.Future)
    print("  [PASS] test_celery_future_inherits_future")


def test_pool_has_executor_api():
    """CeleryPool 应有 submit/map/shutdown/__enter__/__exit__ 接口"""
    _clear_pool_cache()
    p = _make_pool_no_worker()
    for method in ('submit', 'map', 'shutdown', '__enter__', '__exit__'):
        assert hasattr(p, method), f"CeleryPool 应有 {method} 方法"
        assert callable(getattr(p, method)), f"{method} 应是可调用的"
    print("  [PASS] test_pool_has_executor_api")


def test_context_manager():
    """CeleryPool 应支持 with 语句"""
    _clear_pool_cache()
    p = _make_pool_no_worker()
    with p as pool:
        assert pool is p
    print("  [PASS] test_context_manager")


# ========================================================================
# Part B: 集成测试（需要本地 Redis）
# ========================================================================

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


def _make_integration_pool():
    """创建集成测试用的 CeleryPool（自动启动 worker）。"""
    qname = f'intg_{uuid.uuid4().hex[:8]}'
    print(f"  集成测试队列名: {qname}")
    return CeleryPool(
        broker_url=REDIS_URL,
        result_backend=REDIS_URL,
        concurrent_num=4,
        pool_type='threads',
        queue_name=qname,
        worker_startup_timeout=8.0,
        worker_loglevel='WARNING',
    )


def test_basic_submit_result(pool):
    """submit + result 基本功能"""
    fut = pool.submit(add, 10, 20)
    result = fut.result(timeout=15)
    assert result == 30, f"期望 30，实际 {result}"
    print("  [PASS] test_basic_submit_result")


def test_multiple_functions(pool):
    """提交多个不同函数"""
    f1 = pool.submit(add, 5, 3)
    f2 = pool.submit(multiply, 4, 7)
    f3 = pool.submit(greet, name="CeleryPool")
    assert f1.result(timeout=15) == 8
    assert f2.result(timeout=15) == 28
    assert f3.result(timeout=15) == "Hello, CeleryPool"
    print("  [PASS] test_multiple_functions")


def test_map_batch(pool):
    """map 批量提交"""
    results = list(pool.map(add, [1, 2, 3], [10, 20, 30], timeout=20))
    assert results == [11, 22, 33], f"期望 [11,22,33]，实际 {results}"
    print("  [PASS] test_map_batch")


def test_exception_propagation(pool):
    """任务异常应传播到 future"""
    fut = pool.submit(will_raise, 42)
    try:
        fut.result(timeout=15)
        assert False, "应抛异常"
    except Exception as e:
        assert "42" in str(e) or "42" in repr(e), f"异常信息应包含 '42': {e}"
    print("  [PASS] test_exception_propagation")


def test_lazy_done(pool):
    """惰性模式：result() 前 done() 为 False，之后为 True"""
    fut = pool.submit(add, 100, 200)
    assert not fut.done(), "惰性模式下 result() 前 done() 应为 False"
    result = fut.result(timeout=15)
    assert result == 300
    assert fut.done(), "result() 后 done() 应为 True"
    print("  [PASS] test_lazy_done")


def test_result_idempotent(pool):
    """多次调用 result() 返回相同值"""
    fut = pool.submit(add, 7, 8)
    r1 = fut.result(timeout=15)
    r2 = fut.result(timeout=15)
    r3 = fut.result()
    assert r1 == r2 == r3 == 15, f"三次调用结果应均为 15: {r1}, {r2}, {r3}"
    print("  [PASS] test_result_idempotent")


# ========================================================================
# 运行入口
# ========================================================================

def _check_redis():
    """尝试连接 Redis，返回是否可用。"""
    try:
        import redis
        r = redis.Redis.from_url(REDIS_URL, socket_connect_timeout=2)
        r.ping()
        r.close()
        return True
    except Exception:
        return False


if __name__ == '__main__':
    unit_only = '--unit-only' in sys.argv

    print("=" * 60)
    print("CeleryPool 验证测试")
    print("=" * 60)

    unit_tests = [
        ("test_singleton_same_queue",     test_singleton_same_queue),
        ("test_singleton_diff_queue",     test_singleton_diff_queue),
        ("test_init_guard",               test_init_guard),
        ("test_celery_app_naming",        test_celery_app_naming),
        ("test_start_worker_is_public",   test_start_worker_is_public),
        ("test_celery_future_no_backend", test_celery_future_no_backend),
        ("test_func_registry",            test_func_registry),
        ("test_thread_safe_singleton",    test_thread_safe_singleton),
        ("test_pool_cache_populated",     test_pool_cache_populated),
        ("test_celery_future_inherits_future", test_celery_future_inherits_future),
        ("test_pool_has_executor_api",    test_pool_has_executor_api),
        ("test_context_manager",          test_context_manager),
    ]

    integration_tests = [
        ("test_basic_submit_result",   test_basic_submit_result),
        ("test_multiple_functions",    test_multiple_functions),
        ("test_map_batch",             test_map_batch),
        ("test_exception_propagation", test_exception_propagation),
        ("test_lazy_done",             test_lazy_done),
        ("test_result_idempotent",     test_result_idempotent),
    ]

    passed = 0
    failed = 0
    skipped = 0
    total = len(unit_tests) + (0 if unit_only else len(integration_tests))

    print(f"\n--- Part A: 单元测试 ({len(unit_tests)} 项) ---\n")
    for name, fn in unit_tests:
        sys.stdout.write(f">>> {name} ...\n")
        sys.stdout.flush()
        try:
            fn()
            passed += 1
        except Exception as e:
            sys.stdout.write(f"  [FAIL] {name}: {e}\n")
            sys.stdout.flush()
            failed += 1

    _clear_pool_cache()

    if unit_only:
        skipped = len(integration_tests)
        print(f"\n--- Part B: 集成测试 (已跳过，使用 --unit-only) ---")
    else:
        redis_ok = _check_redis()
        if not redis_ok:
            skipped = len(integration_tests)
            print(f"\n--- Part B: 集成测试 (已跳过，Redis 不可用) ---")
            print(f"  提示: 请确保 Redis 运行在 {REDIS_URL}")
        else:
            print(f"\n--- Part B: 集成测试 ({len(integration_tests)} 项，需 Redis) ---\n")
            _clear_pool_cache()
            pool = _make_integration_pool()
            for name, fn in integration_tests:
                sys.stdout.write(f">>> {name} ...\n")
                sys.stdout.flush()
                try:
                    fn(pool)
                    sys.stdout.flush()
                    passed += 1
                except Exception as e:
                    sys.stdout.write(f"  [FAIL] {name}: {e}\n")
                    sys.stdout.flush()
                    failed += 1
                time.sleep(1)

    print()
    print("=" * 60)
    print(f"结果: {passed} 通过 / {failed} 失败 / {skipped} 跳过 (共 {total + skipped} 项)")
    print("=" * 60)
    sys.stdout.flush()

    _clear_pool_cache()
    time.sleep(2)

    if failed > 0:
        os._exit(1)
    else:
        os._exit(0)
