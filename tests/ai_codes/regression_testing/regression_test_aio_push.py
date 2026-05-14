# -*- coding: utf-8 -*-
"""
回归测试：异步 push 通路（async def + aio_push）
"""
import sys, os, asyncio
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from funboost import boost, BoosterParams, BrokerEnum, ConcurrentModeEnum

@boost(BoosterParams(
    queue_name="regression_test_async",
    qps=100, broker_kind=BrokerEnum.MEMORY_QUEUE,
    is_using_rpc_mode=True,
    concurrent_mode=ConcurrentModeEnum.ASYNC
))
async def async_add(x, y):
    await asyncio.sleep(0.1)
    return x + y

async def _run():
    async_add.consume()
    aio_result = await async_add.aio_push(100, 200)
    result = await aio_result.result
    assert result == 300, f"期望 300，实际 {result}"
    print("[PASS] aio_push: 100+200=300")

asyncio.run(_run())
