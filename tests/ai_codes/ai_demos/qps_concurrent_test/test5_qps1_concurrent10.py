"""
测试5: qps=1, concurrent_num=10, 耗时0.5秒
预期：实际吞吐量=min(1, 10/0.5)=1个/秒，5个任务约5秒
"""
import os
import time
from datetime import datetime
from funboost import boost, BrokerEnum, BoosterParams

os.environ["LOG_PATH"] = 'd:/pythonlogs/ai_console_outs'
os.environ['PRINT_WRTIE_FILE_NAME'] = 'test5_qps1_concurrent10.print'
os.environ['SYS_STD_FILE_NAME'] = 'test5_qps1_concurrent10.std'


@boost(BoosterParams(
    queue_name="test5_queue",
    broker_kind=BrokerEnum.SQLITE_QUEUE,
    qps=1,
    concurrent_num=10,
))
def task5(task_id: int):
    print(f'[{datetime.now().strftime("%H:%M:%S")}] 任务 {task_id} 开始')
    time.sleep(0.5)
    print(f'[{datetime.now().strftime("%H:%M:%S")}] 任务 {task_id} 完成')


if __name__ == '__main__':
    for i in range(5):
        task5.push(i)
    
    print(f'[{datetime.now().strftime("%H:%M:%S")}] 配置: qps=1, concurrent_num=10, 耗时0.5秒')
    print(f'[{datetime.now().strftime("%H:%M:%S")}] 预期: 吞吐量=min(1,20)=1个/秒，5个任务约5秒')
    
    task5.consume()
    time.sleep(12)
    
    print(f'[{datetime.now().strftime("%H:%M:%S")}] 测试完成')
    os._exit(66)
