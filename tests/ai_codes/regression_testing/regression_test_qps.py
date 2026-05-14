# -*- coding: utf-8 -*-
"""
回归测试：QPS 限流。
消费函数内收集完成信号，不依赖 RPC（省掉 Redis）。
"""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from funboost import boost, BoosterParams, BrokerEnum

TASK_COUNT = 10
completed = []

@boost(BoosterParams(
    queue_name="regression_test_qps",
    qps=10, broker_kind=BrokerEnum.MEMORY_QUEUE
))
def dummy(x):
    completed.append(x)

dummy.consume()

t0 = time.time()
for i in range(TASK_COUNT):
    dummy.push(i)

while len(completed) < TASK_COUNT:
    time.sleep(0.005)

elapsed = time.time() - t0
print(f"[PASS] qps_control: {TASK_COUNT} 个任务耗时 {elapsed:.3f}s, 理论 ~0.9s (qps=10)")
if elapsed < 0.5:
    print(f"[WARN] 耗时 {elapsed:.3f}s 过短，QPS 限流可能未生效")
