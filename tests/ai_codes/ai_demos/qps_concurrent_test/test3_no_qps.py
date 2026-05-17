"""
测试3: 不设置qps，只设置concurrent_num，验证默认行为
预期：不设置qps时，按并发数量全速执行
"""
import os
import time
from datetime import datetime
from funboost import boost, BrokerEnum, BoosterParams

os.environ["LOG_PATH"] = 'd:/pythonlogs/ai_console_outs'
os.environ['PRINT_WRTIE_FILE_NAME'] = 'test3_no_qps.print'
os.environ['SYS_STD_FILE_NAME'] = 'test3_no_qps.std'


@boost(BoosterParams(
    queue_name="test3_queue",
    broker_kind=BrokerEnum.SQLITE_QUEUE,
    concurrent_num=3,  # 只设置并发数，不设置qps
))
def task_no_qps(task_id: int):
    """每个任务耗时1秒"""
    print(f'[{datetime.now().strftime("%H:%M:%S")}] 任务 {task_id} 开始')
    time.sleep(1)
    print(f'[{datetime.now().strftime("%H:%M:%S")}] 任务 {task_id} 完成')


if __name__ == '__main__':
    for i in range(6):
        task_no_qps.push(i)
    
    print(f'[{datetime.now().strftime("%H:%M:%S")}] 配置: 不设置qps, concurrent_num=3, 每个任务耗时1秒')
    print(f'[{datetime.now().strftime("%H:%M:%S")}] 预期: 并发3个全速执行，6个任务分2批，约2秒完成')
    
    task_no_qps.consume()
    time.sleep(10)
    
    print(f'[{datetime.now().strftime("%H:%M:%S")}] 测试完成')
    os._exit(66)
