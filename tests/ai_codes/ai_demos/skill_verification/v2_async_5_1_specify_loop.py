"""验证 SKILL: funboost-async-programming §5.1 specify_async_loop（无网络，验证 loop 绑定）"""
import asyncio
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"v2_async_5_1_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"v2_async_5_1_std_{_ts}"

from funboost import boost, BoosterParams, BrokerEnum, ConcurrentModeEnum

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)


@boost(
    BoosterParams(
        queue_name=f"aiohttp_task_v2_{_ts}",
        broker_kind=BrokerEnum.MEMORY_QUEUE,
        concurrent_mode=ConcurrentModeEnum.ASYNC,
        specify_async_loop=loop,
    )
)
async def fetch(url: str):
    # 用 asyncio.sleep 模拟 IO，避免外网依赖；保留 specify_async_loop 验证点
    await asyncio.sleep(0.2)
    return f"mock response for {url}"[:50]


if __name__ == "__main__":
    fetch.push("https://example.com")
    fetch.consume()
    time.sleep(15)
    os._exit(66)
