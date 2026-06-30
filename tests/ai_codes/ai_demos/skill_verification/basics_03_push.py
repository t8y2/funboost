"""验证 using-funboost-basics: push 只传业务参数"""
import os
import time

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
_ts = int(time.time())
os.environ["PRINT_WRTIE_FILE_NAME"] = f"basics_03_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"basics_03_std_{_ts}"

from funboost import boost, BoosterParams, BrokerEnum


@boost(BoosterParams(queue_name="basics_03_push", broker_kind=BrokerEnum.MEMORY_QUEUE))
def my_task(url: str, depth: int = 1):
    print(f"[OK] push consumed url={url}, depth={depth}")
    return depth


if __name__ == "__main__":
    my_task.push("https://example.com", depth=3)
    my_task.consume()
    time.sleep(15)
    os._exit(66)
