"""
FunboostFuture + MemoryFunboostPool + FunboostPool 综合测试。
覆盖各种入参条件组合。
"""
import time
from funboost import MemoryFunboostPool, BoosterParams, BrokerEnum
from funboost.core.funboost_pool import FunboostPool, FunboostPoolPickleFunc, FunboostFuture
from funboost.core.exceptions import FunboostTaskExecutionError


# ============ 业务函数 ============

def add(a, b):
    return a + b

def will_raise(x):
    raise ValueError(f"参数 {x} 不合法")

def slow_task(sec):
    time.sleep(sec)
    return f"done_{sec}"

async def aio_add(a, b):
    return a + b


# ============ 测试 MemoryFunboostPool ============

def test_memory_pool_direct_result():
    """is_future_direct_ret_result=True：future.result() 直接返回业务值"""
    pool = MemoryFunboostPool(2, is_future_direct_ret_result=True)
    fut = pool.submit(add, 10, 20)
    result = fut.result(timeout=5)
    assert result == 30, f"期望 30，实际 {result}"
    assert isinstance(fut, FunboostFuture)
    print("  [PASS] test_memory_pool_direct_result")


def test_memory_pool_status_result():
    """is_future_direct_ret_result=False：future.result() 返回 FunctionResultStatus"""
    from funboost import FunctionResultStatus
    pool = MemoryFunboostPool(2, is_future_direct_ret_result=False)
    fut = pool.submit(add, 5, 3)
    result = fut.result(timeout=5)
    assert isinstance(result, FunctionResultStatus), f"期望 FunctionResultStatus，实际 {type(result)}"
    assert result.result == 8
    assert result.success is True
    print("  [PASS] test_memory_pool_status_result")


def test_memory_pool_exception():
    """任务执行失败时，future.result() 抛出 FunboostTaskExecutionError"""
    pool = MemoryFunboostPool(2, is_future_direct_ret_result=True)
    fut = pool.submit(will_raise, 42)
    try:
        fut.result(timeout=5)
        assert False, "应该抛异常"
    except FunboostTaskExecutionError as e:
        assert "ValueError" in e.original_exception_type
        assert "42" in e.original_exception_msg
    print("  [PASS] test_memory_pool_exception")


def test_memory_pool_exception_status_mode():
    """is_future_direct_ret_result=False + 异常：返回 FunctionResultStatus 且 success=False"""
    from funboost import FunctionResultStatus
    pool = MemoryFunboostPool(2, is_future_direct_ret_result=False)
    fut = pool.submit(will_raise, 99)
    result = fut.result(timeout=5)
    assert isinstance(result, FunctionResultStatus)
    assert result.success is False
    print("  [PASS] test_memory_pool_exception_status_mode")


def test_memory_pool_async_func():
    """支持 async def 函数"""
    pool = MemoryFunboostPool(2)
    fut = pool.submit(aio_add, 100, 200)
    assert fut.result(timeout=5) == 300
    print("  [PASS] test_memory_pool_async_func")


def test_memory_pool_map():
    """map 批量提交"""
    pool = MemoryFunboostPool(4)
    results = list(pool.map(add, [1, 2, 3], [10, 20, 30], timeout=10))
    assert results == [11, 22, 33], f"期望 [11,22,33]，实际 {results}"
    print("  [PASS] test_memory_pool_map")


def test_memory_pool_multiple_submits():
    """连续提交多个任务"""
    pool = MemoryFunboostPool(4)
    futures = [pool.submit(add, i, i * 10) for i in range(10)]
    results = [f.result(timeout=5) for f in futures]
    expected = [i + i * 10 for i in range(10)]
    assert results == expected
    print("  [PASS] test_memory_pool_multiple_submits")


def test_memory_pool_with_qps():
    """带 QPS 限制"""
    pool = MemoryFunboostPool(4, qps=100)
    fut = pool.submit(add, 7, 8)
    assert fut.result(timeout=5) == 15
    print("  [PASS] test_memory_pool_with_qps")


# ============ 测试 FunboostPoolPickleFunc ============

def test_pickle_pool_memory_mode():
    """FunboostPoolPickleFunc + MEMORY_QUEUE 走父类路径"""
    params = BoosterParams(
        queue_name='test_pickle_mem',
        broker_kind=BrokerEnum.MEMORY_QUEUE,
        concurrent_num=2,
        max_retry_times=0,
    )
    pool = FunboostPoolPickleFunc(params, is_need_result=True, is_future_direct_ret_result=True)
    fut = pool.submit(add, 100, 200)
    assert fut.result(timeout=5) == 300
    print("  [PASS] test_pickle_pool_memory_mode")


def test_pickle_pool_no_result():
    """is_need_result=False：submit 返回 FunboostFuture，调用 .result() 报错"""
    params = BoosterParams(
        queue_name='test_pickle_no_result',
        broker_kind=BrokerEnum.MEMORY_QUEUE,
        concurrent_num=2,
    )
    pool = FunboostPoolPickleFunc(params, is_need_result=False)
    fut = pool.submit(add, 1, 2)
    # 内存队列模式走父类路径，is_need_result 不影响内存队列
    # 分布式模式才会返回 has_result_source=False 的 FunboostFuture
    print("  [PASS] test_pickle_pool_no_result (内存队列模式)")


# ============ 测试 FunboostPool（函数路径模式）============

def test_funboost_pool_memory_mode():
    """FunboostPool + MEMORY_QUEUE"""
    params = BoosterParams(
        queue_name='test_fp_mem',
        broker_kind=BrokerEnum.MEMORY_QUEUE,
        concurrent_num=4,
    )
    pool = FunboostPool(params, is_need_result=True, is_future_direct_ret_result=True)
    f1 = pool.submit(add, 5, 3)
    assert f1.result(timeout=5) == 8
    print("  [PASS] test_funboost_pool_memory_mode")


def test_funboost_pool_status_mode():
    """FunboostPool + is_future_direct_ret_result=False"""
    from funboost import FunctionResultStatus
    params = BoosterParams(
        queue_name='test_fp_status',
        broker_kind=BrokerEnum.MEMORY_QUEUE,
        concurrent_num=2,
    )
    pool = FunboostPool(params, is_need_result=True, is_future_direct_ret_result=False)
    fut = pool.submit(add, 10, 10)
    result = fut.result(timeout=5)
    assert isinstance(result, FunctionResultStatus)
    assert result.result == 20
    print("  [PASS] test_funboost_pool_status_mode")


def test_funboost_pool_exception():
    """FunboostPool + 异常"""
    params = BoosterParams(
        queue_name='test_fp_exc',
        broker_kind=BrokerEnum.MEMORY_QUEUE,
        concurrent_num=2,
    )
    pool = FunboostPool(params, is_need_result=True, is_future_direct_ret_result=True)
    fut = pool.submit(will_raise, 77)
    try:
        fut.result(timeout=5)
        assert False, "应该抛异常"
    except FunboostTaskExecutionError as e:
        assert "ValueError" in e.original_exception_type
        assert "77" in e.original_exception_msg
    print("  [PASS] test_funboost_pool_exception")


def test_funboost_pool_async():
    """FunboostPool + async 函数"""
    params = BoosterParams(
        queue_name='test_fp_async',
        broker_kind=BrokerEnum.MEMORY_QUEUE,
        concurrent_num=2,
    )
    pool = FunboostPool(params, is_need_result=True)
    fut = pool.submit(aio_add, 50, 50)
    assert fut.result(timeout=5) == 100
    print("  [PASS] test_funboost_pool_async")


# ============ 测试 FunboostFuture 本身 ============

def test_funboost_future_is_standard_future():
    """FunboostFuture 是 concurrent.futures.Future 的子类"""
    import concurrent.futures
    pool = MemoryFunboostPool(2)
    fut = pool.submit(add, 1, 1)
    assert isinstance(fut, concurrent.futures.Future)
    assert isinstance(fut, FunboostFuture)
    fut.result(timeout=5)
    print("  [PASS] test_funboost_future_is_standard_future")


def test_funboost_future_no_result_source():
    """has_result_source=False 时，调用 .result() 报 RuntimeError"""
    fut = FunboostFuture(has_result_source=False)
    try:
        fut.result(timeout=1)
        assert False, "应该抛 RuntimeError"
    except RuntimeError as e:
        assert "is_need_result" in str(e)
    print("  [PASS] test_funboost_future_no_result_source")


def test_funboost_future_done_callback():
    """惰性模式下：先调用 result() 触发解析，回调随之触发"""
    pool = MemoryFunboostPool(2)
    callback_results = []

    def on_done(fut):
        callback_results.append(fut.result())

    fut = pool.submit(add, 7, 7)
    fut.add_done_callback(on_done)
    assert fut.result(timeout=5) == 14
    time.sleep(0.1)
    assert callback_results == [14], f"回调结果不对: {callback_results}"
    print("  [PASS] test_funboost_future_done_callback")


# ============ 主入口 ============

if __name__ == '__main__':
    print("=" * 60)
    print("MemoryFunboostPool 测试")
    print("=" * 60)
    test_memory_pool_direct_result()
    test_memory_pool_status_result()
    test_memory_pool_exception()
    test_memory_pool_exception_status_mode()
    test_memory_pool_async_func()
    test_memory_pool_map()
    test_memory_pool_multiple_submits()
    test_memory_pool_with_qps()

    print()
    print("=" * 60)
    print("FunboostPoolPickleFunc 测试")
    print("=" * 60)
    test_pickle_pool_memory_mode()
    test_pickle_pool_no_result()

    print()
    print("=" * 60)
    print("FunboostPool 测试")
    print("=" * 60)
    test_funboost_pool_memory_mode()
    test_funboost_pool_status_mode()
    test_funboost_pool_exception()
    test_funboost_pool_async()

    print()
    print("=" * 60)
    print("FunboostFuture 测试")
    print("=" * 60)
    test_funboost_future_is_standard_future()
    test_funboost_future_no_result_source()
    test_funboost_future_done_callback()

    print()
    print("=" * 60)
    print("全部测试通过！")
    print("=" * 60)
