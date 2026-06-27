"""
【funboost 简单演示】- 使用 MEMORY_QUEUE (Python内存队列，无需外部中间件)
按照 AGENTS.md 第十二条指引编写，使用环境变量方式输出到文件。
"""
import os

# === 环境变量设置（必须写在最开头） ===
os.environ["LOG_PATH"] = 'd:/pythonlogs/ai_console_outs'
os.environ['PRINT_WRTIE_FILE_NAME'] = 'simple_demo_print.print'
os.environ['SYS_STD_FILE_NAME'] = 'simple_demo_std.std'

# === 业务代码 ===
import time
from funboost import boost, BrokerEnum, BoosterParams


@boost(BoosterParams(
    queue_name='simple_demo_queue',
    broker_kind=BrokerEnum.MEMORY_QUEUE,    # 内存队列，无需任何外部中间件
    qps=3,                                   # 每秒最多消费3条
    concurrent_num=5,                        # 最大并发数5
    log_level=50,                            # 只显示关键输出
    create_logger_file=False,                # 不创建日志文件
))
def my_add(a, b):
    """一个简单的加法函数"""
    result = a + b
    print(f'✓ 消费: {a} + {b} = {result}')
    time.sleep(0.5)  # 模拟耗时
    return result


if __name__ == '__main__':
    print('=' * 50)
    print('【1】直接调用函数 (不走消息队列)')
    ret = my_add(100, 200)
    print(f'    返回值: {ret}')
    print()

    print('【2】清空队列')
    my_add.clear()
    print('    队列已清空')
    print()

    print('【3】发布 5 条消息到队列')
    for i in range(5):
        my_add.push(i, i * 10)
        print(f'    发布: push({i}, {i * 10})')
    print(f'    队列消息数: {my_add.get_message_count()}')
    print()

    print('【4】启动消费 (将消费5条消息，每条耗时0.5秒，qps=3)')
    print('=' * 50)
    my_add.consume()

    # 预估：框架启动 ~5s + 5条/3qps≈1.7s + 缓冲 = 约10秒
    sleep_time = 10
    print(f'    等待 {sleep_time} 秒后自动退出...')
    time.sleep(sleep_time)

    print(f'    队列剩余消息数: {my_add.get_message_count()}')
    print('=' * 50)
    print('演示完成 ✓')
    os._exit(66)  # 强制退出，防止进程卡住
