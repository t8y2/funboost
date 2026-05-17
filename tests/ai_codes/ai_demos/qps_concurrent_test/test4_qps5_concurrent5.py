"""
测试4: qps=5, concurrent_num=5, 耗时1秒
预期：实际吞吐量=min(5, 5/1)=5个/秒，10个任务约2秒
"""
import os
import time
from datetime import datetime
from funboost import boost, BrokerEnum, BoosterParams

os.environ["LOG_PATH"] = 'd:/pythonlogs/ai_console_outs'
os.environ['PRINT_WRTIE_FILE_NAME'] = 'test4_qps5_concurrent5.print'
os.environ['SYS_STD_FILE_NAME'] = 'test4_qps5_concurrent5.std'


@boost(BoosterParams(
    queue_name="test4_queue",
    broker_kind=BrokerEnum.SQLITE_QUEUE,
    qps=5,
    concurrent_num=5,
))
def task4(task_id: int):
    print(f'[{datetime.now().strftime("%H:%M:%S")}] 任务 {task_id} 开始')
    time.sleep(1)
    print(f'[{datetime.now().strftime("%H:%M:%S")}] 任务 {task_id} 完成')


if __name__ == '__main__':
    for i in range(10):
        task4.push(i)
    
    print(f'[{datetime.now().strftime("%H:%M:%S")}] 配置: qps=5, concurrent_num=5, 耗时1秒')
    print(f'[{datetime.now().strftime("%H:%M:%S")}] 预期: 吞吐量=min(5,5/1)=5个/秒，10个任务约2秒')
    
    task4.consume()
    time.sleep(10)
    
    print(f'[{datetime.now().strftime("%H:%M:%S")}] 测试完成')
    os._exit(66)
