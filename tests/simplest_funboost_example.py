"""
funboost 最最简单示例：使用内存队列，无需任何外部中间件。
运行方式：python tests/simplest_funboost_example.py
"""
import os
import sys

# 让脚本无论从哪里运行，都能导入项目根目录的 funboost 包
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
from funboost import boost, BrokerEnum, BoosterParams


@boost(BoosterParams(
    queue_name="simplest_example_queue",
    broker_kind=BrokerEnum.MEMORY_QUEUE,  # 内存队列，零外部依赖
    qps=10,
    concurrent_num=2,
))
def add(x, y):
    result = x + y
    print(f"✅ 消费任务: {x} + {y} = {result}")
    return result


if __name__ == "__main__":
    print("发布 3 个任务到内存队列...")
    for i in range(3):
        add.push(i, i + 10)

    print("启动消费...")
    add.consume()

    # 等待消费完成
    time.sleep(3)
    print("✅ 最简示例运行完成！")
