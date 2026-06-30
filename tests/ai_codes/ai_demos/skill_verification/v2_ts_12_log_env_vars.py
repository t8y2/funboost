"""验证 funboost-troubleshooting SKILL §5.4 AI agent 捕获输出环境变量"""
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:/pythonlogs/ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"v2_ts_log_env_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"v2_ts_std_{_ts}"

from funboost import boost, BoosterParams, BrokerEnum

@boost(BoosterParams(
    queue_name=f"v2_ts_log_env_{_ts}",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    concurrent_num=2,
))
def my_task(x):
    print(f"log env demo print: {x}")
    return x

if __name__ == "__main__":
    for key in ("LOG_PATH", "PRINT_WRTIE_FILE_NAME", "SYS_STD_FILE_NAME"):
        print(f"{key}={os.environ.get(key)!r}")
    my_task.push(1)
    my_task.consume()
    time.sleep(15)
    os._exit(66)
