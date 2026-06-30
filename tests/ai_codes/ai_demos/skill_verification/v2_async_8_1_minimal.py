"""验证 SKILL: funboost-async-programming §8.1 无 Redis 最小完整示例"""
import asyncio
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"v2_async_8_1_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"v2_async_8_1_std_{_ts}"

from funboost import boost, BoosterParams, BrokerEnum, ConcurrentModeEnum


@boost(
    BoosterParams(
        queue_name=f"skill_async_demo_q_v2_{_ts}",
        broker_kind=BrokerEnum.MEMORY_QUEUE,
        concurrent_mode=ConcurrentModeEnum.ASYNC,
        concurrent_num=20,
    )
)
async def async_task(n: int):
    await asyncio.sleep(0.3)
    return n * n


@boost(
    BoosterParams(
        queue_name=f"skill_sync_demo_q_v2_{_ts}",
        broker_kind=BrokerEnum.MEMORY_QUEUE,
    )
)
def sync_task(n: int):
    time.sleep(0.3)
    return n + 1


async def async_main():
    for i in range(3):
        await async_task.aio_push(i)

    sync_task.push(100)

    status = await async_task.publisher.get_aio_future(7)
    print(f"async_task(7) = {status.result}")

    status2 = await sync_task.publisher.get_aio_future(10)
    print(f"sync_task(10) = {status2.result}")


if __name__ == "__main__":
    async_task.consume()
    sync_task.consume()
    time.sleep(1)
    asyncio.run(async_main())
    time.sleep(15)
    os._exit(66)
