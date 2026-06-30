"""round3b: 验证 ConcurrentModeEnum.ASYNC + async def 消费"""
import asyncio
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"r2_async_mem_03_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"r2_async_mem_03_std_{_ts}"

from funboost import boost, BoosterParams, BrokerEnum, ConcurrentModeEnum

results = []


@boost(BoosterParams(
    queue_name=f"r2_async_consume_{_ts}",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    concurrent_mode=ConcurrentModeEnum.ASYNC,
    concurrent_num=10,
))
async def async_fetch(n: int):
    await asyncio.sleep(0.2)
    results.append(n * n)
    return n * n


if __name__ == "__main__":
    for i in range(3):
        async_fetch.push(i)
    async_fetch.consume()
    time.sleep(5)
    assert len(results) == 3, f"expected 3 consumed, got {len(results)}"
    assert results == [0, 1, 4], f"unexpected results: {results}"
    print(f"[PASS] ASYNC consume results={results}")
    time.sleep(15)
    os._exit(66)
