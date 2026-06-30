"""验证 round3 / funboost-troubleshooting SKILL §3 步骤1 consume() 直接调用"""
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"obs_trouble_ts_05_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"obs_trouble_ts_05_std_{_ts}"

from funboost import boost, BoosterParams, BrokerEnum

@boost(BoosterParams(
    queue_name=f"obs_trouble_ts_consume_{_ts}",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    concurrent_num=2,
))
def my_task(x):
    print(f"consumed: {x}")
    return x

if __name__ == "__main__":
    my_task.consume()  # 非阻塞；不要再用 threading.Thread 包装
    my_task.push(42)
    time.sleep(15)
    os._exit(66)
