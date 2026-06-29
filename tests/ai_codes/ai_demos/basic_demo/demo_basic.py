"""
Funboost 基础 Demo - AI 自动测试脚本
展示 @boost 装饰器的基本用法：发布任务 + 消费执行
"""
import os
import time
from datetime import datetime

# ============ 必须在脚本开头设置环境变量（用于 AI 检查输出）============
# 每次运行必须使用不同的文件名后缀，防止读取到上一次的老日志
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
os.environ['LOG_PATH'] = r'D:\pythonlogs\ai_console_outs'
os.environ['PRINT_WRTIE_FILE_NAME'] = f'ai_print_{timestamp}.txt'
os.environ['SYS_STD_FILE_NAME'] = f'ai_std_{timestamp}.txt'
# ====================================================================

from funboost import boost, BoosterParams
from funboost import enable_ctrl_c_quit_on_windows

# ============ 定义任务函数 ============
@boost(BoosterParams(
    queue_name='ai_demo_queue',           # 队列名
    broker_kind='MEMORY_QUEUE',           # 使用内存队列（零序列化开销，适合测试）
    concurrent_num=3,                     # 并发数
    log_level=20,                         # INFO 级别日志
    max_retry_times=0,                    # 不重试
))
def add_task(x, y):
    """简单的加法任务"""
    result = x + y
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 执行任务：{x} + {y} = {result}")
    return result


@boost(BoosterParams(
    queue_name='ai_demo_queue2',
    broker_kind='MEMORY_QUEUE',
    concurrent_num=2,
    log_level=20,
))
def process_message(msg_id, content):
    """处理消息任务"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 处理消息 {msg_id}: {content}")
    time.sleep(0.1)  # 模拟处理耗时
    return f"Processed: {content}"


# ============ 主程序 ============
if __name__ == '__main__':
    print("=" * 60)
    print("Funboost 基础 Demo 开始运行")
    print(f"开始时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 1. 发布任务
    print("\n【步骤 1】发布任务...")
    
    # 发布加法任务
    print("  - 发布 5 个加法任务...")
    for i in range(5):
        add_task.push(i, i * 10)
        print(f"    已发布任务 {i+1}: add_task({i}, {i*10})")
    
    # 发布消息处理任务
    print("  - 发布 3 个消息处理任务...")
    for i in range(3):
        process_message.push(msg_id=f"MSG_{i}", content=f"Hello World {i}")
        print(f"    已发布任务 {i+1}: process_message(MSG_{i})")
    
    print("\n【步骤 2】启动消费者...")
    # 2. 启动消费者（非阻塞，会持续消费）
    add_task.consume()
    process_message.consume()
    
    print("  - 消费者已启动，等待任务执行完成...")
    print("\n【步骤 3】等待任务执行...")
    
    # 3. 等待足够时间让任务执行完成
    # 估算：5 个加法任务（瞬时）+ 3 个消息任务（每个 0.1 秒，并发 2）
    # 框架启动约 2-3 秒 + 任务执行约 2 秒 + 缓冲 3 秒 = 约 8 秒
    wait_time = 10
    print(f"  - 等待 {wait_time} 秒...")
    time.sleep(wait_time)
    
    print("\n【步骤 4】脚本结束")
    print(f"结束时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print("所有任务应已执行完成，请检查上方输出日志")
    print("=" * 60)
    
    # 4. 自动退出（防止 consume() 无限循环阻塞）
    # 根据 AGENTS.md 要求，使用 os._exit(66) 退出
    os._exit(66)
