"""验证 skill: funboost-memory-queue-pool §4.2 FunboostPool + REDIS_ACK_ABLE"""
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"mem_funweb_02_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"mem_funweb_02_std_{_ts}"


def my_func(arg1, arg2):
    return arg1 + arg2


if __name__ == "__main__":
    from funboost import FunboostPool, BoosterParams, BrokerEnum

    pool = FunboostPool(
        BoosterParams(
            queue_name=f"persistent_pool_r3_{_ts}",
            broker_kind=BrokerEnum.REDIS_ACK_ABLE,
            concurrent_num=10,
            qps=10,
            max_retry_times=5,
        ),
        is_need_result=True,
    )
    future = pool.submit(my_func, arg1=10, arg2=20)
    result = future.result(timeout=30)
    print(f"result={result}")
    assert result == 30, f"expected 30, got {result}"
    print("[PASS] FunboostPool REDIS_ACK_ABLE")
    time.sleep(15)
    os._exit(66)
