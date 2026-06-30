"""验证 funboost-troubleshooting SKILL §4.1 event loop already running 解决方案"""
import os
import time
import asyncio

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"v2_ts_09_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"v2_ts_09_std_{_ts}"

from funboost import boost, BoosterParams, BrokerEnum, ConcurrentModeEnum

loop = asyncio.new_event_loop()

@boost(BoosterParams(
    queue_name=f"v2_ts_eloop_{_ts}",
    concurrent_mode=ConcurrentModeEnum.ASYNC,
    specify_async_loop=loop,
    is_auto_start_specify_async_loop_in_child_thread=False,
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    concurrent_num=2,
))
async def my_task(x):
    print(f"async task: {x}")
    return x + 1

if __name__ == "__main__":
    my_task.consume()
    my_task.push(1)

    def run_loop_briefly():
        asyncio.set_event_loop(loop)
        loop.run_until_complete(asyncio.sleep(2))

    import threading
    t = threading.Thread(target=run_loop_briefly)
    t.start()
    t.join(timeout=5)
    print("[OK] is_auto_start_specify_async_loop_in_child_thread=False 配置生效")
    time.sleep(13)
    os._exit(66)
