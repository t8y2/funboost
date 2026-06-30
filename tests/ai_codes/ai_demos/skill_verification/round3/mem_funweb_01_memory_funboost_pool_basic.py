"""验证 skill: funboost-memory-queue-pool §4.1 MemoryFunboostPool 基础用法"""
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"mem_funweb_01_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"mem_funweb_01_std_{_ts}"


def my_func(arg1, arg2):
    return arg1 + arg2


if __name__ == "__main__":
    from funboost import MemoryFunboostPool

    pool = MemoryFunboostPool(concurrent_num=10, qps=5)
    future = pool.submit(my_func, 1, 2)
    result = future.result(timeout=10)
    print(f"result={result}")
    assert result == 3, f"expected 3, got {result}"
    print("[PASS] MemoryFunboostPool basic")
    time.sleep(15)
    os._exit(66)
