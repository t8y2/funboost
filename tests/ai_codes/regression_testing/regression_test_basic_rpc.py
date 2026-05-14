# -*- coding: utf-8 -*-
"""
回归测试：push -> consume -> async_result.result 通路
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from funboost import boost, BoosterParams, BrokerEnum

@boost(BoosterParams(
    queue_name="regression_test_rpc",
    qps=100, broker_kind=BrokerEnum.MEMORY_QUEUE,
    is_using_rpc_mode=True
))
def add(x, y):
    return x + y

add.consume()
result = add.push(10, 20).result
assert result == 30, f"期望 30，实际 {result}"
print("[PASS] basic_rpc: 10+20=30")
