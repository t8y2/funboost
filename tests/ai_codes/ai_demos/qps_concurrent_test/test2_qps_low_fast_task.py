"""
测试2: qps小，并发大，函数耗时短 - 验证qps是瓶颈
预期：qps=2，concurrent_num=10，每个任务耗时0.1秒
实际应该每秒只执行2个任务，6个任务需要约3秒
"""
import os
import time
from datetime import datetime
from funboost import boost, BrokerEnum, BoosterParams

os.environ["LOG_PATH"] = 'd:/pythonlogs/ai_console_outs'
os.environ['PRINT_WRTIE_FILE_NAME'] = 'test2_qps_low_fast_task.print'
os.environ['SYS_STD_FILE_NAME'] = 'test2_qps_low_fast_task.std'


@boost(BoosterParams(
    queue_name="test2_queue",
    broker_kind=BrokerEnum.SQLITE_QUEUE,
    qps=2,  # 限制每秒2个
    concurrent_num=10,  # 并发大
))
def fast_task(task_id: int):
    """每个任务耗时0.1秒"""
    print(f'[{datetime.now().strftime("%H:%M:%S")}] 任务 {task_id} 开始')
    time.sleep(0.1)
    print(f'[{datetime.now().strftime("%H:%M:%S")}] 任务 {task_id} 完成')


if __name__ == '__main__':
    for i in range(6):
        fast_task.push(i)
    
    print(f'[{datetime.now().strftime("%H:%M:%S")}] 配置: qps=2, concurrent_num=10, 每个任务耗时0.1秒')
    print(f'[{datetime.now().strftime("%H:%M:%S")}] 预期: qps=2限制，每秒只执行2个任务，6个任务需要约3秒')
    
    fast_task.consume()
    time.sleep(10)
    
    print(f'[{datetime.now().strftime("%H:%M:%S")}] 测试完成')
    os._exit(66)
