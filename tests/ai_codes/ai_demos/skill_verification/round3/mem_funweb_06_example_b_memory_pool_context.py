"""验证 skill: funboost-memory-queue-pool §7 示例 B MemoryFunboostPool context manager"""
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"mem_funweb_06_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"mem_funweb_06_std_{_ts}"

from funboost import MemoryFunboostPool


def process(item):
    return item * 2


if __name__ == "__main__":
    with MemoryFunboostPool(concurrent_num=5, qps=20) as pool:
        futures = [pool.submit(process, i) for i in range(20)]
        results = [f.result(timeout=30) for f in futures]
        print(results[:5])
        assert results[:5] == [0, 2, 4, 6, 8], results[:5]
    print("[PASS] example B MemoryFunboostPool")
    time.sleep(15)
    os._exit(66)
