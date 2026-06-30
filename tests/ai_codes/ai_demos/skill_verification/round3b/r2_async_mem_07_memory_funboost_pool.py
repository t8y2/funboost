"""round3b: 验证 MemoryFunboostPool import / submit / result"""
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"r2_async_mem_07_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"r2_async_mem_07_std_{_ts}"

from funboost import MemoryFunboostPool
from funboost.core.funboost_pool import MemoryFunboostPool as MF_from_core


def double(x):
    return x * 2


assert MemoryFunboostPool is MF_from_core

if __name__ == "__main__":
    with MemoryFunboostPool(concurrent_num=5, qps=20) as pool:
        futures = [pool.submit(double, i) for i in range(5)]
        results = [f.result(timeout=10) for f in futures]
    assert results == [0, 2, 4, 6, 8], f"unexpected: {results}"
    print(f"[PASS] MemoryFunboostPool submit/result={results}")
    time.sleep(15)
    os._exit(66)
