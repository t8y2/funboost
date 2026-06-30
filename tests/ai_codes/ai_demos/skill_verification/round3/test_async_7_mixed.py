"""验证 SKILL: funboost-async-programming §7 异步消费 + 同步消费混合"""
import asyncio
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"test_async_7_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"test_async_7_std_{_ts}"

from funboost import boost, BoosterParams, BrokerEnum, ConcurrentModeEnum


@boost(
    BoosterParams(
        queue_name=f"mixed_async_queue_{_ts}",
        broker_kind=BrokerEnum.MEMORY_QUEUE,
        concurrent_mode=ConcurrentModeEnum.ASYNC,
    )
)
async def async_worker(x):
    await asyncio.sleep(0.3)
    return f"async {x}"


@boost(
    BoosterParams(
        queue_name=f"mixed_sync_queue_{_ts}",
        broker_kind=BrokerEnum.MEMORY_QUEUE,
    )
)
def sync_worker(x):
    time.sleep(0.3)
    return f"sync {x}"


if __name__ == "__main__":

    async def publish_all():
        for i in range(3):
            await async_worker.aio_push(i)
        for j in range(3):
            sync_worker.push(j)

    asyncio.run(publish_all())

    async_worker.consume()
    sync_worker.consume()
    time.sleep(15)
    os._exit(66)
