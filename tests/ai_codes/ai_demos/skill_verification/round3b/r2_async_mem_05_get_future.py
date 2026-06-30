"""round3b: 验证 @boost + MEMORY_QUEUE 的 publisher.get_future()"""
import concurrent.futures
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"r2_async_mem_05_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"r2_async_mem_05_std_{_ts}"

from funboost import boost, BoosterParams, BrokerEnum


@boost(BoosterParams(
    queue_name=f"r2_get_future_{_ts}",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    concurrent_num=10,
))
def add(x, y):
    return x + y


if __name__ == "__main__":
    add.consume()
    future: concurrent.futures.Future = add.publisher.get_future(3, 4)
    status = future.result(timeout=10)
    assert status.result == 7 and status.success is True
    print(f"[PASS] get_future sync result={status.result}")
    time.sleep(15)
    os._exit(66)
