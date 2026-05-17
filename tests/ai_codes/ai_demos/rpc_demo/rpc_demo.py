"""
RPC 模式 demo: push 任务并获取返回值
"""
import os
import time

os.environ["LOG_PATH"] = 'd:/pythonlogs/ai_console_outs'
os.environ['PRINT_WRTIE_FILE_NAME'] = 'rpc_demo_print_20260516.print'
os.environ['SYS_STD_FILE_NAME'] = 'rpc_demo_std_20260516.std'

from funboost import boost, BrokerEnum, BoosterParams


@boost(BoosterParams(
    queue_name="test_rpc_queue_v1",
    broker_kind=BrokerEnum.REDIS_ACK_ABLE,
    concurrent_num=10,
    is_using_rpc_mode=True,
))
def multiply_task(a, b):
    result = a * b
    print(f"计算: {a} * {b} = {result}")
    return result


if __name__ == '__main__':
    multiply_task.consume()

    async_results = []
    for i in range(1, 6):
        ar = multiply_task.push(i, i * 10)
        async_results.append(ar)
        print(f"已推送任务: {i} * {i*10}")

    for i, ar in enumerate(async_results):
        result = ar.result
        print(f"RPC 结果 {i+1}: {result}")

    print("所有 RPC 结果已获取完成!")
    time.sleep(5)
    print("5秒到了，退出程序")
    os._exit(66)
