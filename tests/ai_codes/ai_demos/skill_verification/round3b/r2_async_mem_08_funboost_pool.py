"""round3b: 验证 FunboostPool import / submit / result (MEMORY_QUEUE 零 Redis)"""
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"r2_async_mem_08_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"r2_async_mem_08_std_{_ts}"

from funboost import FunboostPool, BoosterParams, BrokerEnum
from funboost.core.funboost_pool import FunboostPool as FP_from_core


def triple(x):
    return x * 3


assert FunboostPool is FP_from_core

if __name__ == "__main__":
    pool = FunboostPool(
        BoosterParams(
            queue_name=f"r2_funboost_pool_{_ts}",
            broker_kind=BrokerEnum.MEMORY_QUEUE,
            concurrent_num=5,
            qps=20,
            max_retry_times=0,
        ),
        is_need_result=True,
    )
    futures = [pool.submit(triple, i) for i in range(4)]
    results = [f.result(timeout=10) for f in futures]
    assert results == [0, 3, 6, 9], f"unexpected: {results}"
    print(f"[PASS] FunboostPool submit/result={results}")
    time.sleep(15)
    os._exit(66)
