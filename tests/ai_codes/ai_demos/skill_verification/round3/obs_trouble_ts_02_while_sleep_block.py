"""验证 round3 / funboost-troubleshooting SKILL §1.2 等价写法 while sleep 阻塞主线程"""
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"obs_trouble_ts_02_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"obs_trouble_ts_02_std_{_ts}"

from funboost import boost, BoosterParams, BrokerEnum

@boost(BoosterParams(
    queue_name=f"obs_trouble_ts_while_{_ts}",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    concurrent_num=2,
))
def my_task(x):
    print(f"while block demo: {x}")
    return x

if __name__ == "__main__":
    my_task.consume()
    my_task.push(1)
    # SKILL: while 1: time.sleep(100) — 自动化测试仅 sleep 15 秒后退出
    time.sleep(15)
    os._exit(66)
