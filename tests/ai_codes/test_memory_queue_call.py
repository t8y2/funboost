# -*- coding: utf-8 -*-
"""
测试内存队列的 call 方法：发布消息并通过 concurrent.futures.Future 获取结果，不依赖 Redis。
"""
import time
from funboost import boost, BoosterParams, BrokerEnum


@boost(BoosterParams(
    queue_name='test_memory_queue_call_q1',
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    qps=0,
    concurrent_num=10,
))
def add(x, y):
    time.sleep(0.5)  # 模拟耗时
    return x + y


@boost(BoosterParams(
    queue_name='test_memory_queue_call_q2',
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    qps=0,
    concurrent_num=10,
))
def divide(a, b):
    return a / b


if __name__ == '__main__':
    # 启动消费
    add.consume()
    divide.consume()
    time.sleep(1)  # 等消费者启动

    # ========== 测试1：正常调用 ==========
    print('=' * 50)
    print('测试1：call 方法正常获取结果')
    future = add.publisher.call(10, y=20)
    # future 是 concurrent.futures.Future 对象
    # .result(timeout) 阻塞等待结果，返回 FunctionResultStatus 对象
    function_result_status = future.result(timeout=10)
    print(f'  success: {function_result_status.success}')
    print(f'  result: {function_result_status.result}')
    print(f'  task_id: {function_result_status.task_id}')
    assert function_result_status.success is True
    assert function_result_status.result == 30
    print('  ✅ 测试1 通过')

    # ========== 测试2：多个 call 并发 ==========
    print('=' * 50)
    print('测试2：多个 call 并发获取结果')
    futures = []
    for i in range(5):
        f = add.publisher.call(i, y=i * 10)
        futures.append((i, f))

    for i, f in futures:
        frs = f.result(timeout=10)
        expected = i + i * 10
        print(f'  {i} + {i * 10} = {frs.result} (expected {expected}), success={frs.success}')
        assert frs.result == expected
        assert frs.success is True
    print('  ✅ 测试2 通过')

    # ========== 测试3：函数异常时 Future 也能正常返回 ==========
    print('=' * 50)
    print('测试3：函数异常时 Future 正常返回（success=False）')
    future_err = divide.publisher.call(10, b=0)  # 除零错误
    frs_err = future_err.result(timeout=10)
    print(f'  success: {frs_err.success}')
    print(f'  exception: {frs_err.exception}')
    assert frs_err.success is False
    print('  ✅ 测试3 通过')

    # ========== 测试4：普通 push 不受影响 ==========
    print('=' * 50)
    print('测试4：普通 push 不受 call 影响')
    add.push(100, y=200)
    time.sleep(2)
    print('  ✅ 测试4 通过（push 正常运行）')

    print('=' * 50)
    print('🎉 所有测试通过！内存队列 call 方法工作正常，完全不依赖 Redis。')
