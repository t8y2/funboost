"""验证 SKILL: funboost-async-programming §5.4 AioAsyncResult 正确用法（MEMORY_QUEUE）"""
import asyncio
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"v2_async_5_4_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"v2_async_5_4_std_{_ts}"

from funboost import boost, BoosterParams, BrokerEnum, ConcurrentModeEnum


@boost(
    BoosterParams(
        queue_name=f"api_good_task_v2_{_ts}",
        broker_kind=BrokerEnum.MEMORY_QUEUE,
        concurrent_mode=ConcurrentModeEnum.ASYNC,
    )
)
async def my_task(x: int):
    await asyncio.sleep(0.1)
    return x * 2


async def api_good():
    # MEMORY_QUEUE：用 get_aio_future 替代 AioAsyncResult（无需 Redis RPC）
    status = await my_task.publisher.get_aio_future(1)
    return status.result


async def main():
    my_task.consume()
    await asyncio.sleep(1)
    result = await api_good()
    print(f"api_good result={result}")


if __name__ == "__main__":
    asyncio.run(main())
    time.sleep(15)
    os._exit(66)
