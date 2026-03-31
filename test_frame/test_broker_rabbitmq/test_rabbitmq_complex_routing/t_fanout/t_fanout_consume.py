# -*- coding: utf-8 -*-
# @Author  : ydf

import time
from funboost import BoosterParams, BrokerEnum, ctrl_c_recv

# 使用 RABBITMQ_COMPLEX_ROUTING 支持复杂路由的 broker
BROKER_KIND_FOR_TEST = BrokerEnum.RABBITMQ_COMPLEX_ROUTING

# 定义交换机名称
EXCHANGE_NAME = 'fanout_broadcast_exchange'


@BoosterParams(
    queue_name='q_email_service',  # 队列1：邮件服务
    broker_kind=BROKER_KIND_FOR_TEST,
    broker_exclusive_config={
        'exchange_name': EXCHANGE_NAME,
        'exchange_type': 'fanout',
        # fanout 模式不需要指定 routing_key_for_bind，会自动使用空字符串
    })
def email_service_consumer(user_id: str, action: str, message: str):
    """邮件服务消费者 - 处理所有需要发送邮件通知的事件"""
    print(f'📧【邮件服务】用户 {user_id} 执行了 {action} 操作，发送邮件通知: {message}')
    time.sleep(0.5)


@BoosterParams(
    queue_name='q_sms_service',  # 队列2：短信服务
    broker_kind=BROKER_KIND_FOR_TEST,
    broker_exclusive_config={
        'exchange_name': EXCHANGE_NAME,
        'exchange_type': 'fanout',
        # fanout 模式会忽略路由键，所有消息都会被广播
    })
def sms_service_consumer(user_id: str, action: str, message: str):
    """短信服务消费者 - 处理所有需要发送短信通知的事件"""
    print(f'📱【短信服务】用户 {user_id} 执行了 {action} 操作，发送短信通知: {message}')
    time.sleep(0.8)


@BoosterParams(
    queue_name='q_push_service',  # 队列3：推送服务
    broker_kind=BROKER_KIND_FOR_TEST,
    broker_exclusive_config={
        'exchange_name': EXCHANGE_NAME,
        'exchange_type': 'fanout',
    })
def push_service_consumer(user_id: str, action: str, message: str):
    """推送服务消费者 - 处理所有需要推送通知的事件"""
    print(f'🔔【推送服务】用户 {user_id} 执行了 {action} 操作，发送推送通知: {message}')
    time.sleep(0.3)


@BoosterParams(
    queue_name='q_audit_service',  # 队列4：审计服务
    broker_kind=BROKER_KIND_FOR_TEST,
    broker_exclusive_config={
        'exchange_name': EXCHANGE_NAME,
        'exchange_type': 'fanout',
    })
def audit_service_consumer(user_id: str, action: str, message: str):
    """审计服务消费者 - 记录所有用户操作日志"""
    print(f'📝【审计服务】记录用户 {user_id} 的 {action} 操作: {message}')
    time.sleep(0.2)


@BoosterParams(
    queue_name='q_analytics_service',  # 队列5：数据分析服务
    broker_kind=BROKER_KIND_FOR_TEST,
    broker_exclusive_config={
        'exchange_name': EXCHANGE_NAME,
        'exchange_type': 'fanout',
    })
def analytics_service_consumer(user_id: str, action: str, message: str):
    """数据分析服务消费者 - 收集用户行为数据"""
    print(f'📊【数据分析】收集用户 {user_id} 的行为数据: {action} - {message}')
    time.sleep(0.4)


if __name__ == '__main__':
    # 清理之前的消息（可选）
    # email_service_consumer.clear()
    # sms_service_consumer.clear()
    # push_service_consumer.clear()
    # audit_service_consumer.clear()
    # analytics_service_consumer.clear()

    # 查看消息数量（可选）
    # print(f"邮件服务队列消息数: {email_service_consumer.get_message_count()}")
    # print(f"短信服务队列消息数: {sms_service_consumer.get_message_count()}")
    # print(f"推送服务队列消息数: {push_service_consumer.get_message_count()}")
    # print(f"审计服务队列消息数: {audit_service_consumer.get_message_count()}")
    # print(f"数据分析队列消息数: {analytics_service_consumer.get_message_count()}")

    # 启动所有消费者
    print("启动所有服务消费者...")
    email_service_consumer.consume()
    sms_service_consumer.consume()
    push_service_consumer.consume()
    audit_service_consumer.consume()
    analytics_service_consumer.consume()

    print("所有服务消费者已启动，等待消息...")
    print("Fanout 路由模式特点:")
    print("  - 📢 广播模式：所有绑定到交换机的队列都会收到相同的消息")
    print("  - 🚫 忽略路由键：无论发布时使用什么路由键，都会广播给所有队列")
    print("  - ⚡ 适用场景：通知系统、日志收集、数据同步等需要多个服务同时处理的场景")
    print("按 Ctrl+C 停止消费...")

    # 阻塞主线程，使消费者可以持续运行
    ctrl_c_recv()
