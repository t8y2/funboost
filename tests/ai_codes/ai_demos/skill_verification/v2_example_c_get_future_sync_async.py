"""验证 skill: funboost-memory-queue-pool §7 示例 C get_future / get_aio_future"""
import asyncio
import concurrent.futures
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"v2_example_c_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"v2_example_c_std_{_ts}"

from funboost import boost, BoosterParams, BrokerEnum, ConcurrentModeEnum


@boost(BoosterParams(queue_name=f"sync_q_v2_{_ts}", broker_kind=BrokerEnum.MEMORY_QUEUE, qps=2, concurrent_num=10))
def sync_task(x, y):
    time.sleep(0.5)
    return x + y


@boost(BoosterParams(
    queue_name=f"async_q_v2_{_ts}",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    concurrent_mode=ConcurrentModeEnum.ASYNC,
    concurrent_num=10,
))
async def async_task(x, y):
    await asyncio.sleep(0.5)
    return x * y


if __name__ == "__main__":
    sync_task.consume()
    async_task.consume()

    f = sync_task.publisher.get_future(3, 4)
    status = f.result(timeout=10)
    print(f"同步: {status.result}")
    assert status.result == 7

    async def run_async():
        af = async_task.publisher.get_aio_future(3, 4)
        status = await af
        print(f"异步: {status.result}")
        assert status.result == 12

    asyncio.run(run_async())
    print("[PASS] example C sync/async get_future")
    time.sleep(15)
    os._exit(66)
