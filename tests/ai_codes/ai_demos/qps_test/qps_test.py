"""
测试 QPS 和并发数量的实际关系
"""
import os
import time
from funboost import boost, BrokerEnum, BoosterParams

os.environ["LOG_PATH"] = 'd:/pythonlogs/ai_console_outs'
os.environ['PRINT_WRTIE_FILE_NAME'] = 'qps_test.print'
os.environ['SYS_STD_FILE_NAME'] = 'qps_test.std'


@boost(BoosterParams(
    queue_name="qps_test_queue",
    broker_kind=BrokerEnum.SQLITE_QUEUE,
    qps=2,  # 每秒执行2个任务
    concurrent_num=10,  # 并发数10
))
def slow_task(task_id: int):
    """每个任务耗时1秒"""
    start = time.time()
    print(f'任务 {task_id} 开始执行')
    time.sleep(1)  # 模拟耗时
    print(f'任务 {task_id} 执行完成，耗时 {time.time()-start:.2f}秒')


if __name__ == '__main__':
    # 发布 6 个任务
    for i in range(1, 7):
        slow_task.push(i)
    
    print(f'已发布 6 个任务，qps=2, concurrent_num=10')
    print(f'预期：每秒执行2个任务，6个任务应该需要约3秒')
    
    start_time = time.time()
    
    # 启动消费
    slow_task.consume()
    
    # 等待消费完成
    time.sleep(10)
    
    elapsed = time.time() - start_time
    print(f'总耗时: {elapsed:.2f}秒')
    print(f'测试完成')
    
    os._exit(66)
