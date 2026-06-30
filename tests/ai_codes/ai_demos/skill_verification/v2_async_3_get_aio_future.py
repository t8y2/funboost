"""验证 SKILL: funboost-async-programming §3 MEMORY_QUEUE get_aio_future 片段"""
import asyncio
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"v2_async_3_future_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"v2_async_3_future_std_{_ts}"

from funboost import boost, BoosterParams, BrokerEnum, ConcurrentModeEnum


@boost(
    BoosterParams(
        queue_name=f"async_task_future_v2_{_ts}",
        broker_kind=BrokerEnum.MEMORY_QUEUE,
        concurrent_mode=ConcurrentModeEnum.ASYNC,
    )
)
async def async_task(x: int, y: int):
    await asyncio.sleep(0.1)
    return x + y


async def main():
    async_task.consume()
    await asyncio.sleep(1)
    future = async_task.publisher.get_aio_future(1, 2)
    result_status = await future
    print(result_status.result)


if __name__ == "__main__":
    asyncio.run(main())
    time.sleep(15)
    os._exit(66)
