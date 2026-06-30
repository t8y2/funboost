"""验证 SKILL: funboost-async-programming §3 异步 RPC（MEMORY_QUEUE + get_aio_future 替代 Redis）"""
import asyncio
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"v2_async_3_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"v2_async_3_std_{_ts}"

from funboost import boost, BoosterParams, BrokerEnum, ConcurrentModeEnum


@boost(
    BoosterParams(
        queue_name=f"async_rpc_add_v2_{_ts}",
        broker_kind=BrokerEnum.MEMORY_QUEUE,
        concurrent_mode=ConcurrentModeEnum.ASYNC,
    )
)
async def async_add(x: int, y: int):
    await asyncio.sleep(0.1)
    return x + y


async def main():
    async_add.consume()
    await asyncio.sleep(1)

    # MEMORY_QUEUE 无 Redis RPC：用 get_aio_future 替代 skill 中 AioAsyncResult
    status1 = await async_add.publisher.get_aio_future(10, 20)
    print(status1.result)

    status2 = await async_add.publisher.get_aio_future(1, 2)
    print(status2.result)


if __name__ == "__main__":
    asyncio.run(main())
    time.sleep(15)
    os._exit(66)
