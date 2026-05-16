# -*- coding: utf-8 -*-
"""
回归测试：多个 RPC 调用不串
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from funboost import boost, BoosterParams, BrokerEnum

@boost(BoosterParams(
    queue_name="regression_test_rpc_multi",
    qps=100, broker_kind=BrokerEnum.MEMORY_QUEUE,
    is_using_rpc_mode=True
))
def mul(x, y):
    return x * y

mul.consume()
for a, b, expected in [(2, 3, 6), (5, 5, 25), (0, 999, 0), (-1, 8, -8)]:
    r = mul.push(a, b).result
    assert r == expected, f"{a}*{b} 期望 {expected}，实际 {r}"
print("[PASS] multi_rpc: 4 个乘法断言通过")
