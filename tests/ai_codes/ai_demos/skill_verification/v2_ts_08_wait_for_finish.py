"""验证 funboost-troubleshooting SKILL §3 步骤7 wait_for_possible_has_finish_all_tasks"""
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"v2_ts_08_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"v2_ts_08_std_{_ts}"

from funboost import boost, BoosterParams, BrokerEnum

@boost(BoosterParams(
    queue_name=f"v2_ts_wait_{_ts}",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    concurrent_num=2,
    qps=10,
))
def f(x):
    print(f"wait demo task: {x}")
    return x

if __name__ == "__main__":
    for i in range(5):
        f.push(i)
    f.consume()
    f.wait_for_possible_has_finish_all_tasks(minutes=1)
    print("[OK] wait_for_possible_has_finish_all_tasks 返回")
    time.sleep(5)
    os._exit(66)
