"""验证 skill: funboost-memory-queue-pool §5.1 get_future 同步用法"""
import concurrent.futures
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"mem_funweb_03_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"mem_funweb_03_std_{_ts}"

from funboost import boost, BoosterParams, BrokerEnum


@boost(BoosterParams(queue_name=f"demo_r3_{_ts}", broker_kind=BrokerEnum.MEMORY_QUEUE, concurrent_num=10))
def add(x, y):
    return x + y


if __name__ == "__main__":
    add.consume()
    future: concurrent.futures.Future = add.publisher.get_future(1, 2)
    status = future.result(timeout=10)
    print(status.result, status.success)
    assert status.result == 3 and status.success is True
    print("[PASS] get_future sync")
    time.sleep(15)
    os._exit(66)
