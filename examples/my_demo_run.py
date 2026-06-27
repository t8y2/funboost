"""
funboost 简单演示示例 - 使用 MEMORY_QUEUE (Python内存队列，无需任何外部中间件)
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import time
from funboost import boost, BrokerEnum, BoosterParams


@boost(BoosterParams(
    queue_name='my_test_queue',
    broker_kind=BrokerEnum.MEMORY_QUEUE,  # 内存队列，无需安装任何中间件
    qps=3,                                 # 每秒最多消费3条
    concurrent_num=5,                       # 最大并发数5
))
def my_add(a, b):
    """一个简单的加法函数"""
    print(f'▶ 开始执行: {a} + {b} ...', end=' ')
    time.sleep(0.5)  # 模拟耗时
    result = a + b
    print(f'结果 = {result}')
    return result


if __name__ == '__main__':
    # 1. 直接调用 - 测试函数本身（不走消息队列）
    print('=' * 50)
    print('【1】直接调用函数: my_add(100, 200)')
    ret = my_add(100, 200)
    print(f'    返回值: {ret}')
    print()

    # 2. 清空队列（确保队列干净）
    print('【2】清空队列')
    my_add.clear()
    print()

    # 3. 发布消息到队列
    print('【3】发布10条消息到队列')
    for i in range(10):
        my_add.push(i, i * 10)
    print(f'    已发布10条消息, 当前队列消息数: {my_add.get_message_count()}')
    print()

    # 4. 启动消费
    print('【4】启动消费 (将在后台线程运行, 消费完自动退出)')
    print('=' * 50)
    my_add.consume()

    # 等待消费完成
    time.sleep(5)

    print()
    print('=' * 50)
    print('【5】查看结果')
    print(f'    队列剩余消息数: {my_add.get_message_count()}')
    print('演示结束 ✓')
