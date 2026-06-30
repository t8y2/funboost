"""验证 funboost-troubleshooting SKILL §3 步骤2 queue_name 必须一致"""
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"v2_ts_06_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"v2_ts_06_std_{_ts}"

from funboost import boost, BoosterParams, BrokerEnum

QUEUE = f"order_process_{_ts}"

@boost(BoosterParams(queue_name=QUEUE, broker_kind=BrokerEnum.MEMORY_QUEUE, concurrent_num=2))
def task_a(x):
    print(f"task_a publish side push: {x}")
    return x

@boost(BoosterParams(queue_name=QUEUE, broker_kind=BrokerEnum.MEMORY_QUEUE, concurrent_num=2))
def task_b(x):
    print(f"task_b consume side got: {x}")
    return x * 2

if __name__ == "__main__":
    task_b.consume()
    task_a.push(10)
    time.sleep(15)
    os._exit(66)
