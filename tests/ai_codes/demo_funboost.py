"""
funboost 最简单示例：使用内存队列，无需 Redis/RabbitMQ 等外部中间件。
"""
import time
from funboost import boost, BoosterParams, BrokerEnum


@boost(BoosterParams(
    queue_name="ai_codes_demo_queue",
    broker_kind=BrokerEnum.MEMORY_QUEUE,  # 内存队列，零依赖
    qps=5,
    concurrent_num=3,
))
def add(a: int, b: int):
    result = a + b
    print(f"[consume] {a} + {b} = {result}")
    time.sleep(0.5)
    return result


if __name__ == "__main__":
    print("[publish] 开始发布任务...")
    for i in range(10):
        add.push(i, i * 2)

    print("[consume] 开始消费...")
    add.consume()
