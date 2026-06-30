"""round3b: funboost-broker-selection — broker_kind=MEMORY_QUEUE 运行时验证"""
import os
import time

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
_ts = int(time.time())
os.environ["PRINT_WRTIE_FILE_NAME"] = f"r3b_broker_02_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"r3b_broker_02_std_{_ts}"

from funboost import boost, BoosterParams, BrokerEnum

DONE = False


@boost(BoosterParams(
    queue_name="production_task_r3b",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
))
def my_task(data: dict):
    global DONE
    print(f"[OK] my_task data={data}")
    DONE = True
    return data


if __name__ == "__main__":
    my_task.push({"key": "value"})
    my_task.consume()
    time.sleep(12)
    print(f"[{'PASS' if DONE else 'FAIL'}] broker_kind=MEMORY_QUEUE consumed={DONE}")
    import os
    os._exit(66 if DONE else 1)
