"""验证 SKILL: funboost-async-programming §3 异步 RPC（MEMORY_QUEUE + get_aio_future 替代 Redis）"""
import asyncio
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"test_async_3_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"test_async_3_std_{_ts}"

from funboost import boost, BoosterParams, BrokerEnum, ConcurrentModeEnum


@boost(
    BoosterParams(
        queue_name=f"async_rpc_add_{_ts}",
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

    # 方式1：aio_push + get_aio_future
    await async_add.aio_push(10, 20)
    status = await async_add.publisher.get_aio_future(10, 20)
    print(f"aio_push result={status.result}")

    # 方式2：同步 push + get_aio_future
    async_add.push(1, 2)
    status2 = await async_add.publisher.get_aio_future(1, 2)
    print(f"sync push result={status2.result}")


if __name__ == "__main__":
    asyncio.run(main())
    time.sleep(15)
    os._exit(66)
