"""
funboost 最简示例：使用内存队列，无需 Redis/RabbitMQ。

- @boost 将普通函数 mul 变成分布式任务
- mul.push(a, b) 向队列发布消息
- mul.consume() 启动消费者（永久运行，Ctrl+C 停止）
"""
from funboost import boost, BoosterParams, BrokerEnum


@boost(BoosterParams(
    queue_name="hello_funboost_ai_codes",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    concurrent_num=3,
    qps=0.05,
    max_retry_times=5,
))
def mul(a, b):
    import time
    result = a * b
    print(f"[消费] {a} * {b} = {result}")
    time.sleep(0.5)
    return result


if __name__ == "__main__":
    print("开始向队列发布 60 条消息...")
    for i in range(1, 60):
        mul.push(i, i * 10)

    print("启动消费者（按 Ctrl+C 停止）...")
    mul.consume()
