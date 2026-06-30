"""验证 SKILL: funboost-async-programming §5.1 specify_async_loop + aiohttp"""
import asyncio
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"test_async_5_1_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"test_async_5_1_std_{_ts}"

import aiohttp

from funboost import boost, BoosterParams, BrokerEnum, ConcurrentModeEnum

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)


@boost(
    BoosterParams(
        queue_name=f"aiohttp_task_{_ts}",
        broker_kind=BrokerEnum.MEMORY_QUEUE,
        concurrent_mode=ConcurrentModeEnum.ASYNC,
        specify_async_loop=loop,
    )
)
async def fetch(url: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            text = (await resp.text())[:50]
            print(f"fetch ok len={len(text)}")
            return text


if __name__ == "__main__":
    fetch.push("https://httpbin.org/get")
    fetch.consume()
    time.sleep(15)
    os._exit(66)
