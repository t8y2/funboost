"""验证 SKILL: funboost-async-programming §1.1 ASYNC 协程模式"""
import asyncio
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"v2_async_1_1_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"v2_async_1_1_std_{_ts}"

from funboost import boost, BoosterParams, BrokerEnum, ConcurrentModeEnum


@boost(
    BoosterParams(
        queue_name=f"async_fetch_queue_v2_{_ts}",
        broker_kind=BrokerEnum.MEMORY_QUEUE,
        concurrent_mode=ConcurrentModeEnum.ASYNC,
        concurrent_num=100,
        qps=10,
    )
)
async def async_fetch(url: str):
    await asyncio.sleep(0.1)
    print(f"fetch {url}")
    return url


if __name__ == "__main__":
    for i in range(5):
        async_fetch.push(f"https://example.com/{i}")
    async_fetch.consume()
    time.sleep(15)
    os._exit(66)
