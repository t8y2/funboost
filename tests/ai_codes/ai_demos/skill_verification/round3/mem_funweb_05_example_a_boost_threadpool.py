"""验证 skill: funboost-memory-queue-pool §7 示例 A @boost 替代 ThreadPoolExecutor"""
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"mem_funweb_05_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"mem_funweb_05_std_{_ts}"

from funboost import boost, BoosterParams, BrokerEnum


@boost(BoosterParams(queue_name=f"test1_r3_{_ts}", broker_kind=BrokerEnum.MEMORY_QUEUE, concurrent_num=5, qps=10))
def f(x, y):
    print(f"{x} + {y} = {x + y}")
    time.sleep(0.1)


if __name__ == "__main__":
    f.consume()
    for i in range(10):
        f.push(i, i * 2)
    print("[PASS] example A push/consume started")
    time.sleep(15)
    os._exit(66)
