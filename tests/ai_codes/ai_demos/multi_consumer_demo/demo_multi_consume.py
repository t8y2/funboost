"""
验证 funboost 连续启动多个消费者：
直接顺序调用 func1.consume(); func2.consume(); func3.consume()
不需要 threading.Thread 包装
"""
import os
import time

os.environ["LOG_PATH"] = 'd:/pythonlogs/ai_console_outs'
os.environ['PRINT_WRTIE_FILE_NAME'] = 'multi_consume_demo.print'
os.environ['SYS_STD_FILE_NAME'] = 'multi_consume_demo.std'

from funboost import boost, BoosterParams, BrokerEnum


@boost(BoosterParams(
    queue_name="multi_demo_q1",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    concurrent_num=5,
))
def task_a(name: str):
    print(f"[task_a] 收到: {name}")
    time.sleep(0.1)
    return f"task_a done: {name}"


@boost(BoosterParams(
    queue_name="multi_demo_q2",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    concurrent_num=5,
))
def task_b(value: int):
    print(f"[task_b] 收到: {value}")
    time.sleep(0.1)
    return value * 2


@boost(BoosterParams(
    queue_name="multi_demo_q3",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    concurrent_num=5,
))
def task_c(x: float, y: float):
    print(f"[task_c] 收到: {x} + {y} = {x + y}")
    time.sleep(0.1)
    return x + y


if __name__ == '__main__':
    # 向三个队列分别发布消息
    for i in range(1, 4):
        task_a.push(f"msg_{i}")
    for i in range(10, 13):
        task_b.push(i)
    task_c.push(1.5, 2.5)
    task_c.push(10.0, 20.0)

    print("=" * 60)
    print("连续启动三个消费者...")
    print("=" * 60)

    # 核心验证：连续调用 consume()，不需要 threading
    task_a.consume()
    print("--- task_a.consume() 已启动（非阻塞） ---")
    task_b.consume()
    print("--- task_b.consume() 已启动（非阻塞） ---")
    task_c.consume()
    print("--- task_c.consume() 已启动（非阻塞） ---")

    print("所有消费者均已启动，等待消费完成...")

    time.sleep(12)
    print('12秒到了，自动退出程序')
    os._exit(66)