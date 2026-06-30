"""round3b: using-funboost-basics — aio_push / aio_publish 运行时验证"""
import asyncio
import os
import time

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
_ts = int(time.time())
os.environ["PRINT_WRTIE_FILE_NAME"] = f"r3b_basics_05_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"r3b_basics_05_std_{_ts}"

from funboost import boost, BoosterParams, BrokerEnum, TaskOptions, ConcurrentModeEnum

HITS = []


@boost(BoosterParams(
    queue_name="aio_r3b",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    concurrent_mode=ConcurrentModeEnum.ASYNC,
))
async def my_task(url: str, depth: int = 1):
    print(f"[OK] aio consumed url={url}, depth={depth}")
    HITS.append((url, depth))
    return depth


async def publish_tasks():
    await my_task.aio_push("https://example.com", depth=3)
    await my_task.aio_publish(
        {"url": "https://example.com/publish", "depth": 5},
        task_options=TaskOptions(countdown=0),
    )


if __name__ == "__main__":
    asyncio.run(publish_tasks())
    my_task.consume()
    time.sleep(12)
    ok = len(HITS) >= 2
    print(f"[{'PASS' if ok else 'FAIL'}] aio_push+aio_publish hits={HITS}")
    import os
    os._exit(66 if ok else 1)
