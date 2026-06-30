"""验证 using-funboost-basics: 异步 aio_push / aio_publish"""
import asyncio
import os
import time

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
_ts = int(time.time())
os.environ["PRINT_WRTIE_FILE_NAME"] = f"basics_05_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"basics_05_std_{_ts}"

from funboost import boost, BoosterParams, BrokerEnum, TaskOptions


@boost(BoosterParams(queue_name="basics_05_async", broker_kind=BrokerEnum.MEMORY_QUEUE))
def my_task(url: str, depth: int = 1):
    print(f"[OK] async consumed url={url}, depth={depth}")
    return depth


async def publish_tasks():
    await my_task.aio_push("https://example.com", depth=3)
    await my_task.aio_publish({"url": "https://example.com/async"}, task_options=TaskOptions(countdown=0))


if __name__ == "__main__":
    asyncio.run(publish_tasks())
    my_task.consume()
    time.sleep(15)
    os._exit(66)
