"""round3b: 验证 aio_push / aio_publish 异步发布"""
import asyncio
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"r2_async_mem_04_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"r2_async_mem_04_std_{_ts}"

from funboost import boost, BoosterParams, BrokerEnum, ConcurrentModeEnum, TaskOptions

processed = []


@boost(BoosterParams(
    queue_name=f"r2_aio_push_{_ts}",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    concurrent_mode=ConcurrentModeEnum.ASYNC,
    concurrent_num=10,
))
async def process(x: int):
    await asyncio.sleep(0.2)
    processed.append(x)
    return x


async def main():
    for i in range(3):
        await process.aio_push(i)
    await process.aio_publish({"x": 99}, task_options=TaskOptions())


if __name__ == "__main__":
    process.consume()
    asyncio.run(main())
    time.sleep(5)
    assert 99 in processed, f"99 not in processed={processed}"
    assert len(processed) >= 4, f"expected >=4, got {processed}"
    print(f"[PASS] aio_push/aio_publish processed={sorted(processed)}")
    time.sleep(15)
    os._exit(66)
