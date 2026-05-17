"""
funboost 基础示例 - subprocess 方式运行（第一种方式）
"""
import time
from funboost import boost, BrokerEnum, BoosterParams


@boost(BoosterParams(
    queue_name="ai_demo_subprocess_queue",
    broker_kind=BrokerEnum.SQLITE_QUEUE,
    qps=5,
    concurrent_num=5,
))
def multiply_task(x: int, y: int):
    """乘法任务"""
    print(f'计算: {x} * {y} = {x * y}')
    return x * y


if __name__ == '__main__':
    # 发布 3 个任务
    for i in range(1, 4):
        multiply_task.push(i, i * 10)
    
    print(f'已发布 3 个乘法任务')
    
    # 启动消费
    multiply_task.consume()
    
    # 等待消费完成
    time.sleep(5)
    
    print(f'消费完成，测试通过！')
