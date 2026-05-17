"""
测试1: qps大但函数耗时长，并发数量小 - 验证实际达不到qps
预期：并发数=2，每个任务耗时2秒，实际每秒只能执行 2/2=1 个任务，达不到 qps=10
"""
import os
import time
from datetime import datetime
from funboost import boost, BrokerEnum, BoosterParams

os.environ["LOG_PATH"] = 'd:/pythonlogs/ai_console_outs'
os.environ['PRINT_WRTIE_FILE_NAME'] = 'test1_qps_high_slow_task.print'
os.environ['SYS_STD_FILE_NAME'] = 'test1_qps_high_slow_task.std'


@boost(BoosterParams(
    queue_name="test1_queue",
    broker_kind=BrokerEnum.SQLITE_QUEUE,
    qps=10,  # 期望每秒10个
    concurrent_num=2,  # 但并发只有2
))
def slow_task(task_id: int):
    """每个任务耗时2秒"""
    print(f'[{datetime.now().strftime("%H:%M:%S")}] 任务 {task_id} 开始')
    time.sleep(2)
    print(f'[{datetime.now().strftime("%H:%M:%S")}] 任务 {task_id} 完成')


if __name__ == '__main__':
    for i in range(6):
        slow_task.push(i)
    
    print(f'[{datetime.now().strftime("%H:%M:%S")}] 配置: qps=10, concurrent_num=2, 每个任务耗时2秒')
    print(f'[{datetime.now().strftime("%H:%M:%S")}] 预期: 并发只有2，每秒最多执行 2/2=1 个任务，达不到qps=10')
    print(f'[{datetime.now().strftime("%H:%M:%S")}] 预期6个任务需要约 6秒')
    
    slow_task.consume()
    time.sleep(15)
    
    print(f'[{datetime.now().strftime("%H:%M:%S")}] 测试完成')
    os._exit(66)
