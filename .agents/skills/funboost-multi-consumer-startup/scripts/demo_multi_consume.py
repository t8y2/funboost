"""验证 funboost 连续启动多个函数消费（2 个函数版本）"""
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import time

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = "multi_consumer_skill_run"
os.environ["SYS_STD_FILE_NAME"] = "multi_consumer_skill_std"

from funboost import boost, BoosterParams, BrokerEnum


@boost(BoosterParams(
    queue_name="multi_consumer_skill_a",
    broker_kind=BrokerEnum.SQLITE_QUEUE,
    concurrent_num=3,
    qps=5,
))
def task_a(x: int):
    print(f"[A] 消费 task_a({x}), 结果={x * 1}")
    return x * 1


@boost(BoosterParams(
    queue_name="multi_consumer_skill_b",
    broker_kind=BrokerEnum.SQLITE_QUEUE,
    concurrent_num=3,
    qps=3,
))
def task_b(x: int):
    print(f"[B] 消费 task_b({x}), 结果={x * 10}")
    return x * 10


if __name__ == "__main__":
    # 向两个队列各发布 5 条消息
    for i in range(5):
        task_a.push(i)
        task_b.push(i)
    print("=== 已发布 10 条消息（2个队列各5条）===")

    # 连续启动两个消费者（非阻塞，直接顺序调用，禁止 threading.Thread 包装）
    task_a.consume()
    print("task_a 消费者已启动")
    task_b.consume()
    print("task_b 消费者已启动")
    print("=== 两个消费者均已启动，等待消费完成 ===")