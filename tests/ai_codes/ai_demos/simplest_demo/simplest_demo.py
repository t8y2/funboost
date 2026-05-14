"""
最简单 funboost demo
使用 MEMORY_QUEUE（内存队列），无需安装任何外部中间件
"""

import os

# ---------- 设置环境变量（for AI 检查输出）----------
os.environ["LOG_PATH"] = 'd:/pythonlogs/ai_console_outs'
os.environ['PRINT_WRTIE_FILE_NAME'] = 'simplest_demo_print.print'
os.environ['SYS_STD_FILE_NAME'] = 'simplest_demo_std.std'
# -------------------------------------------------

import time
from funboost import boost, BoosterParams, BrokerEnum


# 最简单的任务：一个加法函数，用 @boost 装饰后变成分布式调度任务
@boost(BoosterParams(
    queue_name="simplest_demo_queue",
    broker_kind=BrokerEnum.MEMORY_QUEUE,  # 内存队列，无需安装任何中间件
    qps=2,  # 每秒执行 2 次
    concurrent_num=5,  # 5 个线程并发
))
def add(x: int, y: int) -> int:
    """一个简单的加法任务"""
    result = x + y
    print(f"收到任务: {x} + {y} = {result}")
    time.sleep(0.2)
    return result


if __name__ == '__main__':
    # 1. 发布 6 个任务到队列
    print("=== 开始发布任务 ===")
    for i in range(6):
        add.push(i, i * 10)
    print("=== 已发布 6 个任务 ===")

    # 2. 启动消费（非阻塞，在当前进程中用多线程消费）
    add.consume()

    # 3. 等待消费完成，然后强制退出
    time.sleep(5)
    print("=== 5 秒到了，现在自动强制退出程序 ===")
    os._exit(66)
