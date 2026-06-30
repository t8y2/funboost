"""验证 SKILL: funboost-async-programming §2 异步发布 aio_push / aio_publish"""
import asyncio
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"test_async_2_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"test_async_2_std_{_ts}"

from funboost import boost, BoosterParams, BrokerEnum, ConcurrentModeEnum, TaskOptions


@boost(
    BoosterParams(
        queue_name=f"aio_publish_demo_{_ts}",
        broker_kind=BrokerEnum.MEMORY_QUEUE,
        concurrent_mode=ConcurrentModeEnum.ASYNC,
    )
)
async def process(x: int):
    await asyncio.sleep(0.2)
    print(f"process {x}")


async def main():
    for i in range(3):
        await process.aio_push(i)

    await process.aio_publish(
        {"x": 99},
        task_options=TaskOptions(countdown=1),
    )


if __name__ == "__main__":
    process.consume()
    asyncio.run(main())
    time.sleep(15)
    os._exit(66)
