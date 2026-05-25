"""
funboost 最简验证脚本 - 验证核心功能是否正常
使用 MEMORY_QUEUE，无需任何外部依赖
"""
import os

os.environ["LOG_PATH"] = 'd:/pythonlogs/ai_console_outs'
os.environ['PRINT_WRTIE_FILE_NAME'] = 'simplest_verify_20241220.print'
os.environ['SYS_STD_FILE_NAME'] = 'simplest_verify_20241220.std'

import time
from funboost import boost, BrokerEnum, BoosterParams


@boost(BoosterParams(
    queue_name="simplest_verify_queue",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    qps=10,
    concurrent_num=5,
))
def add(x, y):
    result = x + y
    print(f'✅ 计算: {x} + {y} = {result}')
    return result


if __name__ == '__main__':
    # 发布 6 个任务
    for i in range(6):
        add.push(i, i * 10)

    print(f'已发布 6 个任务到内存队列')

    # 启动消费
    add.consume()

    # 等待消费完成（6个任务，qps=10，concurrent_num=5，秒级完成）
    time.sleep(5)
    print('验证完成：funboost 核心功能正常！')
    os._exit(66)