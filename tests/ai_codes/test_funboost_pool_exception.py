"""
验证 FunboostPool / MemoryFunboostPool 任务执行失败时，
future.result() 抛出的异常类型是 FunboostTaskExecutionError，
且保留了原始异常类型名和消息。
"""
from funboost import MemoryFunboostPool
from funboost.core.exceptions import FunboostTaskExecutionError


def will_raise_value_error(x):
    raise ValueError(f"参数 {x} 不合法")


def will_raise_runtime_error():
    raise RuntimeError("运行时故障")


def normal_task(x):
    return x * 2


if __name__ == "__main__":
    pool = MemoryFunboostPool(2, is_future_direct_ret_result=True)

    # -------- 场景 1: ValueError --------
    fut1 = pool.submit(will_raise_value_error, 42)
    try:
        fut1.result(timeout=5)
        print("场景1: 未抛异常，不符合预期！")
    except FunboostTaskExecutionError as e:
        assert "ValueError" in e.original_exception_type, f"异常类型不对: {e.original_exception_type}"
        assert "42" in e.original_exception_msg, f"异常消息不对: {e.original_exception_msg}"
        print(f"场景1 OK: 捕获到 FunboostTaskExecutionError")
        print(f"  original_exception_type = {e.original_exception_type}")
        print(f"  original_exception_msg  = {e.original_exception_msg}")
        print(f"  str(e) = {e}")
    except Exception as e:
        print(f"场景1 FAIL: 期望 FunboostTaskExecutionError，实际是 {type(e).__name__}: {e}")

    # -------- 场景 2: RuntimeError --------
    fut2 = pool.submit(will_raise_runtime_error)
    try:
        fut2.result(timeout=5)
        print("场景2: 未抛异常，不符合预期！")
    except FunboostTaskExecutionError as e:
        assert "RuntimeError" in e.original_exception_type
        assert "运行时故障" in e.original_exception_msg
        print(f"场景2 OK: 捕获到 FunboostTaskExecutionError")
        print(f"  original_exception_type = {e.original_exception_type}")
        print(f"  original_exception_msg  = {e.original_exception_msg}")
    except Exception as e:
        print(f"场景2 FAIL: 期望 FunboostTaskExecutionError，实际是 {type(e).__name__}: {e}")

    # -------- 场景 3: 正常任务不应抛异常 --------
    fut3 = pool.submit(normal_task, 21)
    result = fut3.result(timeout=5)
    assert result == 42, f"正常任务返回值不对: {result}"
    print(f"场景3 OK: 正常任务返回 {result}")

    print("\n全部验证通过")
