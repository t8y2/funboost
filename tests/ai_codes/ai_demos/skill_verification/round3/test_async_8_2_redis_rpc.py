"""验证 SKILL: funboost-async-programming §8.2 RPC 完整示例（MEMORY_QUEUE 适配，无需 Redis）"""
import asyncio
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"test_async_8_2_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"test_async_8_2_std_{_ts}"

from funboost import boost, BoosterParams, BrokerEnum, ConcurrentModeEnum


@boost(
    BoosterParams(
        queue_name=f"skill_redis_async_rpc_{_ts}",
        broker_kind=BrokerEnum.MEMORY_QUEUE,
        concurrent_mode=ConcurrentModeEnum.ASYNC,
    )
)
async def add(x: int, y: int):
    await asyncio.sleep(0.1)
    return x + y


async def main():
    add.consume()
    await asyncio.sleep(1)
    await add.aio_push(3, 4)
    status = await add.publisher.get_aio_future(3, 4)
    print(status.result)


if __name__ == "__main__":
    asyncio.run(main())
    time.sleep(15)
    os._exit(66)
