"""验证 SKILL: funboost-async-programming §1.2 THREADING 模式运行 async def"""
import asyncio
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"v2_async_1_2_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"v2_async_1_2_std_{_ts}"

from funboost import boost, BoosterParams, BrokerEnum


@boost(BoosterParams(queue_name=f"thread_async_queue_v2_{_ts}", broker_kind=BrokerEnum.MEMORY_QUEUE))
async def my_async_task(x):
    await asyncio.sleep(0.3)
    print(x)


if __name__ == "__main__":
    my_async_task.push(1)
    my_async_task.consume()
    time.sleep(15)
    os._exit(66)
