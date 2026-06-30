"""验证 funboost-troubleshooting SKILL §4.2 specify_async_loop 传递 loop"""
import os
import time
import asyncio

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"v2_ts_10_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"v2_ts_10_std_{_ts}"

from funboost import boost, BoosterParams, BrokerEnum, ConcurrentModeEnum

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

try:
    import aiohttp
    ss = aiohttp.ClientSession(loop=loop)
    has_aiohttp = True
except ImportError:
    ss = None
    has_aiohttp = False

@boost(BoosterParams(
    queue_name=f"v2_ts_async_loop_{_ts}",
    concurrent_mode=ConcurrentModeEnum.ASYNC,
    specify_async_loop=loop,
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    concurrent_num=2,
))
async def async_task(x):
    if has_aiohttp:
        url = 'https://httpbin.org/get'
        async with ss.request('get', url=url) as resp:
            print(f"aiohttp status={resp.status} x={x}")
    else:
        print(f"async_task without aiohttp: {x}")
    return x

if __name__ == "__main__":
    async_task.consume()
    async_task.push(1)
    time.sleep(15)
    if has_aiohttp:
        loop.run_until_complete(ss.close())
    os._exit(66)
