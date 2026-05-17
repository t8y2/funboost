"""
组合验证: concurrent_mode=ASYNC + is_using_rpc_mode=True + aio_push + AioAsyncResult
"""
import os
import time
import asyncio

os.environ["LOG_PATH"] = 'd:/pythonlogs/ai_console_outs'
os.environ['PRINT_WRTIE_FILE_NAME'] = 'async_rpc_demo_print_20260516.print'
os.environ['SYS_STD_FILE_NAME'] = 'async_rpc_demo_std_20260516.std'

from funboost import boost, BrokerEnum, BoosterParams, ConcurrentModeEnum, AioAsyncResult


@boost(BoosterParams(
    queue_name="test_async_rpc_queue_v2",
    broker_kind=BrokerEnum.REDIS_ACK_ABLE,
    concurrent_mode=ConcurrentModeEnum.ASYNC,
    concurrent_num=10,
    is_using_rpc_mode=True,
))
async def multiply_async(a, b):
    await asyncio.sleep(0.05)
    result = a * b
    print(f"异步计算: {a} * {b} = {result}")
    return result


async def sequential_pushes():
    print("--- 顺序推送 ---")
    for i in range(1, 4):
        aio_ar = await multiply_async.aio_push(i, i * 10)
        val = await aio_ar.result
        print(f"  顺序 RPC {i}: {val}")


async def parallel_pushes():
    print("--- 并发推送 ---")
    cors = [multiply_async.aio_push(i, i * 100) for i in range(1, 5)]
    results = await asyncio.gather(*cors)
    vals = await asyncio.gather(*[ar.result for ar in results])
    for i, v in enumerate(vals, 1):
        print(f"  并发 RPC {i}: {v}")


async def explicit_AioAsyncResult():
    print("--- 显式 AioAsyncResult ---")
    aio_ar = await multiply_async.aio_push(99, 99)
    sr = await AioAsyncResult(aio_ar.task_id).status_and_result
    print(f"  status_and_result dict: result={sr['result']}, success={sr['success']}")
    val = await AioAsyncResult(aio_ar.task_id).result
    print(f"  AioAsyncResult(task_id).result: {val}")


async def main():
    await sequential_pushes()
    await parallel_pushes()
    await explicit_AioAsyncResult()
    print("所有异步 RPC 组合测试完成!")


if __name__ == '__main__':
    multiply_async.consume()
    time.sleep(2)
    asyncio.run(main())
    print("main done, sleeping...")
    time.sleep(5)
    print("退出程序")
    os._exit(66)
