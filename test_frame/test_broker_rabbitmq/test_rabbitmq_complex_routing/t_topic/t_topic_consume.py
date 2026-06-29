# -*- coding: utf-8 -*-
# @Author  : ydf

import time
from funboost import BoosterParams, BrokerEnum, enable_ctrl_c_quit_on_windows

# 使用 RABBITMQ_COMPLEX_ROUTING 支持复杂路由的 broker
BROKER_KIND_FOR_TEST = BrokerEnum.RABBITMQ_COMPLEX_ROUTING

# 定义交换机名称
EXCHANGE_NAME = 'topic_log_exchange'


@BoosterParams(
    queue_name='q_all_logs',  # 队列1：接收所有日志
    broker_kind=BROKER_KIND_FOR_TEST,
    broker_exclusive_config={
        'exchange_name': EXCHANGE_NAME,
        'exchange_type': 'topic',
        'routing_key_for_bind': '#',  # 关键：# 匹配所有路由键，接收所有消息
    })
def all_logs_consumer(timestamp: str, content: str):
    """这个消费者接收所有级别的日志"""
    print(f'【全部日志消费者】 {timestamp} 收到消息: {content}')
    time.sleep(0.5)


@BoosterParams(
    queue_name='q_error_logs',  # 队列2：只接收错误日志
    broker_kind=BROKER_KIND_FOR_TEST,
    broker_exclusive_config={
        'exchange_name': EXCHANGE_NAME,
        'exchange_type': 'topic',
        'routing_key_for_bind': '*.error',  # 关键：*.error 匹配所有以 .error 结尾的路由键
    })
def error_logs_consumer(timestamp: str, content: str):
    """这个消费者只处理错误级别的日志"""
    print(f'!!!!!!!!!!【错误日志消费者】 {timestamp} 收到消息: {content} !!!!!!!!!!')
    time.sleep(1)


@BoosterParams(
    queue_name='q_system_logs',  # 队列3：只接收系统相关日志
    broker_kind=BROKER_KIND_FOR_TEST,
    broker_exclusive_config={
        'exchange_name': EXCHANGE_NAME,
        'exchange_type': 'topic',
        'routing_key_for_bind': 'system.*',  # 关键：system.* 匹配所有以 system. 开头的路由键
    })
def system_logs_consumer(timestamp: str, content: str):
    """这个消费者只处理系统相关的日志"""
    print(f'【系统日志消费者】 {timestamp} 收到消息: {content}')
    time.sleep(0.8)


@BoosterParams(
    queue_name='q_app_critical_logs',  # 队列4：只接收应用的关键日志
    broker_kind=BROKER_KIND_FOR_TEST,
    broker_exclusive_config={
        'exchange_name': EXCHANGE_NAME,
        'exchange_type': 'topic',
        'routing_key_for_bind': 'app.*.critical',  # 关键：app.*.critical 匹配 app.任意单词.critical 格式
    })
def app_critical_logs_consumer(timestamp: str, content: str):
    """这个消费者只处理应用的关键日志"""
    print(f'🔥🔥🔥【应用关键日志消费者】 {timestamp} 收到消息: {content} 🔥🔥🔥')
    time.sleep(1.2)


if __name__ == '__main__':
    # 清理之前的消息（可选）
    # all_logs_consumer.clear()
    # error_logs_consumer.clear()
    # system_logs_consumer.clear()
    # app_critical_logs_consumer.clear()

    # 查看消息数量（可选）
    # print(f"全部日志队列消息数: {all_logs_consumer.get_message_count()}")
    # print(f"错误日志队列消息数: {error_logs_consumer.get_message_count()}")
    # print(f"系统日志队列消息数: {system_logs_consumer.get_message_count()}")
    # print(f"应用关键日志队列消息数: {app_critical_logs_consumer.get_message_count()}")

    # 启动消费者
    print("启动所有消费者...")
    all_logs_consumer.consume()
    error_logs_consumer.consume()
    system_logs_consumer.consume()
    app_critical_logs_consumer.consume()

    print("消费者已启动，等待消息...")
    print("路由键匹配规则:")
    print("  - 全部日志消费者: '#' (匹配所有)")
    print("  - 错误日志消费者: '*.error' (匹配任意.error)")
    print("  - 系统日志消费者: 'system.*' (匹配system.任意)")
    print("  - 应用关键日志消费者: 'app.*.critical' (匹配app.任意.critical)")
    print("按 Ctrl+C 停止消费...")

    # 阻塞主线程，使消费者可以持续运行
    enable_ctrl_c_quit_on_windows()
