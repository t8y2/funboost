"""
测试6: qps=10, concurrent_num=2, 耗时0.5秒
预期：实际吞吐量=min(10, 2/0.5)=4个/秒，8个任务约2秒
"""
import os
import time
from datetime import datetime
from funboost import boost, BrokerEnum, BoosterParams

os.environ["LOG_PATH"] = 'd:/pythonlogs/ai_console_outs'
os.environ['PRINT_WRTIE_FILE_NAME'] = 'test6_qps10_concurrent2.print'
os.environ['SYS_STD_FILE_NAME'] = 'test6_qps10_concurrent2.std'


@boost(BoosterParams(
    queue_name="test6_queue",
    broker_kind=BrokerEnum.SQLITE_QUEUE,
    qps=10,
    concurrent_num=2,
))
def task6(task_id: int):
    print(f'[{datetime.now().strftime("%H:%M:%S")}] 任务 {task_id} 开始')
    time.sleep(0.5)
    print(f'[{datetime.now().strftime("%H:%M:%S")}] 任务 {task_id} 完成')


if __name__ == '__main__':
    for i in range(8):
        task6.push(i)
    
    print(f'[{datetime.now().strftime("%H:%M:%S")}] 配置: qps=10, concurrent_num=2, 耗时0.5秒')
    print(f'[{datetime.now().strftime("%H:%M:%S")}] 预期: 吞吐量=min(10, 2/0.5)=4个/秒，8个任务约2秒')
    
    task6.consume()
    time.sleep(10)
    
    print(f'[{datetime.now().strftime("%H:%M:%S")}] 测试完成')
    os._exit(66)
