"""验证连续启动多个函数消费"""
import os
import time

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = "multi_consumer_run1"
os.environ["SYS_STD_FILE_NAME"] = "multi_consumer_std1"

from funboost import boost, BoosterParams, BrokerEnum, enable_ctrl_c_quit_on_windows


@boost(BoosterParams(
    queue_name="multi_consumer_demo_a",
    broker_kind=BrokerEnum.SQLITE_QUEUE,
    concurrent_num=3,
    qps=5,
))
def task_a(x: int):
    print(f"[A] 消费 task_a({x}), 结果={x * 1}")
    return x * 1


@boost(BoosterParams(
    queue_name="multi_consumer_demo_b",
    broker_kind=BrokerEnum.SQLITE_QUEUE,
    concurrent_num=3,
    qps=5,
))
def task_b(x: int):
    print(f"[B] 消费 task_b({x}), 结果={x * 10}")
    return x * 10


@boost(BoosterParams(
    queue_name="multi_consumer_demo_c",
    broker_kind=BrokerEnum.SQLITE_QUEUE,
    concurrent_num=3,
    qps=5,
))
def task_c(x: int):
    print(f"[C] 消费 task_c({x}), 结果={x * 100}")
    return x * 100


if __name__ == "__main__":
    # 向三个队列各发布 5 条消息
    for i in range(5):
        task_a.push(i)
        task_b.push(i)
        task_c.push(i)
    print("=== 已发布 15 条消息（3个队列各5条）===")

    # 连续启动三个消费者（非阻塞，直接顺序调用）
    task_a.consume()
    print("task_a 消费者已启动")
    task_b.consume()
    print("task_b 消费者已启动")
    task_c.consume()
    print("task_c 消费者已启动")
    print("=== 三个消费者均已启动，等待消费完成 ===")

    # 保持脚本运行，让消费者有时间处理
    time.sleep(20)
    print("=== 测试结束 ===")