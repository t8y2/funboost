# -*- coding: utf-8 -*-
"""
回归测试：第一次抛异常、重试后成功 -> 最终应拿到正确结果
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from funboost import boost, BoosterParams, BrokerEnum

call_count = [0]

@boost(BoosterParams(
    queue_name="regression_test_retry",
    qps=100, broker_kind=BrokerEnum.MEMORY_QUEUE,
    max_retry_times=3, is_using_rpc_mode=True
))
def flaky(x):
    call_count[0] += 1
    if call_count[0] == 1:
        raise ValueError("第一次必然失败")
    return x * 10

flaky.consume()
r = flaky.push(7).result
assert r == 70, f"期望 70，实际 {r}"
print("[PASS] retry_then_success: 失败重试后恢复")
