"""round3b: 验证 specify_async_loop 参数可传递且 ASYNC 消费正常"""
import asyncio
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"r2_async_mem_09_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"r2_async_mem_09_std_{_ts}"

from funboost import boost, BoosterParams, BrokerEnum, ConcurrentModeEnum

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
done = []


@boost(BoosterParams(
    queue_name=f"r2_specify_loop_{_ts}",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    concurrent_mode=ConcurrentModeEnum.ASYNC,
    specify_async_loop=loop,
    is_auto_start_specify_async_loop_in_child_thread=True,
    concurrent_num=5,
))
async def async_task(x):
    await asyncio.sleep(0.2)
    done.append(x)
    return x


if __name__ == "__main__":
    async_task.consume()
    async_task.push(42)
    time.sleep(5)
    assert 42 in done, f"task not consumed, done={done}"
    print(f"[PASS] specify_async_loop + is_auto_start_specify_async_loop_in_child_thread=True")
    time.sleep(15)
    os._exit(66)
