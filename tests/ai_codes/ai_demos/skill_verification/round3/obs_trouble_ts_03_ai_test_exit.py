"""验证 round3 / funboost-troubleshooting SKILL §1.2 AI 测试脚本自动退出模式"""
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"obs_trouble_ts_03_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"obs_trouble_ts_03_std_{_ts}"

from funboost import boost, BoosterParams, BrokerEnum

@boost(BoosterParams(
    queue_name=f"obs_trouble_ts_ai_exit_{_ts}",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    concurrent_num=2,
))
def my_task(x):
    print(f"ai exit demo: {x}")
    return x

if __name__ == "__main__":
    my_task.push(1)
    my_task.consume()
    time.sleep(15)
    os._exit(66)
