"""验证 using-funboost-basics: publish + TaskOptions"""
import os
import time

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
_ts = int(time.time())
os.environ["PRINT_WRTIE_FILE_NAME"] = f"basics_04_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"basics_04_std_{_ts}"

from funboost import boost, BoosterParams, BrokerEnum, TaskOptions


@boost(BoosterParams(queue_name="basics_04_publish", broker_kind=BrokerEnum.MEMORY_QUEUE))
def my_task(url: str, depth: int = 1):
    print(f"[OK] publish consumed url={url}, depth={depth}")
    return depth


if __name__ == "__main__":
    my_task.publish(
        {"url": "https://example.com", "depth": 3},
        task_options=TaskOptions(
            countdown=0,
            task_id="custom-id-1",
        )
    )
    my_task.consume()
    time.sleep(15)
    os._exit(66)
