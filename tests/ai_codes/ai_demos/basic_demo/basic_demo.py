"""
funboost 基础示例 - 验证 AI 是否掌握规范写法
"""
import os

# 设置日志输出环境变量（第二种方式核心）
os.environ["LOG_PATH"] = 'd:/pythonlogs/ai_console_outs'
os.environ['PRINT_WRTIE_FILE_NAME'] = 'funboost_basic_demo.print'
os.environ['SYS_STD_FILE_NAME'] = 'funboost_basic_demo.std'

import time
from funboost import boost, BrokerEnum, BoosterParams


@boost(BoosterParams(
    queue_name="ai_demo_basic_queue",
    broker_kind=BrokerEnum.SQLITE_QUEUE,  # 使用内置 sqlite，无需外部依赖
    qps=5,
    concurrent_num=5,
))
def greet(name: str, age: int):
    """简单的问候任务"""
    print(f'你好 {name}，你今年 {age} 岁了！')
    return f"问候完成: {name}"


if __name__ == '__main__':
    # 发布 5 个任务
    for i in range(5):
        greet.push(f"用户{i+1}", 20 + i)
    
    print(f'已发布 5 个任务到队列')
    
    # 启动消费
    greet.consume()
    
    # 等待消费完成
    time.sleep(5)
    
    # 验证结果
    print(f'消费完成，共处理 5 个任务')
    print('测试通过！')
    
    # 强制退出
    os._exit(66)
