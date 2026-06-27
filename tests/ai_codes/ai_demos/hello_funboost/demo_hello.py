"""
funboost 入门 Demo —— 展示基本 push + consume 流程
"""

import os
import time

# ============ 必须放在最开头的环境变量配置 ============
os.environ["LOG_PATH"] = 'd:/pythonlogs/ai_console_outs'
os.environ['PRINT_WRTIE_FILE_NAME'] = 'hello_funboost_20250101.print'
os.environ['SYS_STD_FILE_NAME'] = 'hello_funboost_20250101.std'
# =====================================================

from funboost import boost, BrokerEnum, BoosterParams


@boost(BoosterParams(
    queue_name="hello_funboost_queue",
    broker_kind=BrokerEnum.REDIS,
    qps=3,              # 每秒处理 3 条
    concurrent_num=5,   # 5 个并发线程
    is_using_rpc_mode=False,
))
def greet(name: str, msg: str):
    """打招呼任务"""
    result = f"👋 [{name}] 说: {msg}"
    print(result)
    time.sleep(0.3)  # 模拟业务处理
    return result


if __name__ == '__main__':
    print("=" * 50)
    print("🚀 funboost Demo 启动")
    print("=" * 50)

    # 发布 8 条消息
    users = ["Alice", "Bob", "Cindy", "David", "Eva", "Frank", "Grace", "Henry"]
    for i, user in enumerate(users):
        greet.push(user, f"这是第 {i+1} 条消息！")
        print(f"📤 已发布: {user} 的第 {i+1} 条消息")

    print(f"\n📊 共发布 {len(users)} 条消息，开始消费...\n")

    # 启动消费
    greet.consume()

    # 消息数=8, qps=3, 并发=5, 每条耗时~0.3s
    # 预估: 启动5-10s + 8/3≈3s + 缓冲2s ≈ 15s
    time.sleep(18)
    print('\n⏰ 时间到，自动退出程序')
    os._exit(66)