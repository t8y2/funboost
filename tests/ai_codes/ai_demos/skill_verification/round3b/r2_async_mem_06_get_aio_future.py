"""round3b: 验证 async 任务的 publisher.get_aio_future()"""
import asyncio
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"r2_async_mem_06_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"r2_async_mem_06_std_{_ts}"

from funboost import boost, BoosterParams, BrokerEnum, ConcurrentModeEnum


@boost(BoosterParams(
    queue_name=f"r2_get_aio_future_{_ts}",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    concurrent_mode=ConcurrentModeEnum.ASYNC,
    concurrent_num=10,
))
async def async_mul(x, y):
    await asyncio.sleep(0.3)
    return x * y


async def run_async():
    af = async_mul.publisher.get_aio_future(3, 4)
    status = await af
    assert status.result == 12 and status.success is True
    print(f"[PASS] get_aio_future async result={status.result}")


if __name__ == "__main__":
    async_mul.consume()
    asyncio.run(run_async())
    time.sleep(15)
    os._exit(66)
