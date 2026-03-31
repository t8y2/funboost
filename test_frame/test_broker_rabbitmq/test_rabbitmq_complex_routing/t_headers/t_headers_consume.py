# -*- coding: utf-8 -*-
# @Author  : ydf

import time
from funboost import BoosterParams, BrokerEnum, ctrl_c_recv

# 使用 RABBITMQ_COMPLEX_ROUTING 支持复杂路由的 broker
BROKER_KIND_FOR_TEST = BrokerEnum.RABBITMQ_COMPLEX_ROUTING

# 定义交换机名称
EXCHANGE_NAME = 'headers_notification_exchange'


@BoosterParams(
    queue_name='q_urgent_notifications',  # 队列1：紧急通知
    broker_kind=BROKER_KIND_FOR_TEST,
    broker_exclusive_config={
        'exchange_name': EXCHANGE_NAME,
        'exchange_type': 'headers',
        # headers 模式的绑定条件：priority=high 且 urgent=true
        'headers_for_bind': {
            'priority': 'high',
            'urgent': 'true'
        },
        'x_match_for_bind': 'all',  # 必须匹配所有指定的头属性
    })
def urgent_notifications_consumer(user_id: str, title: str, content: str, timestamp: str):
    """紧急通知消费者 - 只处理高优先级且紧急的通知"""
    print(f'🚨【紧急通知】用户 {user_id} | {timestamp}')
    print(f'   标题: {title}')
    print(f'   内容: {content}')
    time.sleep(0.3)


@BoosterParams(
    queue_name='q_high_priority_notifications',  # 队列2：高优先级通知
    broker_kind=BROKER_KIND_FOR_TEST,
    broker_exclusive_config={
        'exchange_name': EXCHANGE_NAME,
        'exchange_type': 'headers',
        # headers 模式的绑定条件：只要 priority=high 即可
        'headers_for_bind': {
            'priority': 'high'
        },
        'x_match_for_bind': 'all',  # 匹配所有指定的头属性
    })
def high_priority_notifications_consumer(user_id: str, title: str, content: str, timestamp: str):
    """高优先级通知消费者 - 处理所有高优先级通知"""
    print(f'⚡【高优先级】用户 {user_id} | {timestamp}')
    print(f'   标题: {title}')
    print(f'   内容: {content}')
    time.sleep(0.5)


@BoosterParams(
    queue_name='q_mobile_notifications',  # 队列3：移动端通知
    broker_kind=BROKER_KIND_FOR_TEST,
    broker_exclusive_config={
        'exchange_name': EXCHANGE_NAME,
        'exchange_type': 'headers',
        # headers 模式的绑定条件：platform=mobile 或 device_type=phone
        'headers_for_bind': {
            'platform': 'mobile',
            'device_type': 'phone'
        },
        'x_match_for_bind': 'any',  # 匹配任意一个指定的头属性即可
    })
def mobile_notifications_consumer(user_id: str, title: str, content: str, timestamp: str):
    """移动端通知消费者 - 处理移动端相关通知"""
    print(f'📱【移动端通知】用户 {user_id} | {timestamp}')
    print(f'   标题: {title}')
    print(f'   内容: {content}')
    time.sleep(0.4)


@BoosterParams(
    queue_name='q_system_admin_notifications',  # 队列4：系统管理员通知
    broker_kind=BROKER_KIND_FOR_TEST,
    broker_exclusive_config={
        'exchange_name': EXCHANGE_NAME,
        'exchange_type': 'headers',
        # headers 模式的绑定条件：category=system 且 role=admin
        'headers_for_bind': {
            'category': 'system',
            'role': 'admin'
        },
        'x_match_for_bind': 'all',  # 必须匹配所有指定的头属性
    })
def system_admin_notifications_consumer(user_id: str, title: str, content: str, timestamp: str):
    """系统管理员通知消费者 - 只处理系统管理相关通知"""
    print(f'🔧【系统管理】用户 {user_id} | {timestamp}')
    print(f'   标题: {title}')
    print(f'   内容: {content}')
    time.sleep(0.6)


@BoosterParams(
    queue_name='q_marketing_notifications',  # 队列5：营销通知
    broker_kind=BROKER_KIND_FOR_TEST,
    broker_exclusive_config={
        'exchange_name': EXCHANGE_NAME,
        'exchange_type': 'headers',
        # headers 模式的绑定条件：category=marketing 且 priority 不为 high
        'headers_for_bind': {
            'category': 'marketing',
            'priority': 'low'
        },
        'x_match_for_bind': 'any',  # 匹配任意一个即可（演示不同的匹配策略）
    })
def marketing_notifications_consumer(user_id: str, title: str, content: str, timestamp: str):
    """营销通知消费者 - 处理营销相关通知"""
    print(f'📢【营销通知】用户 {user_id} | {timestamp}')
    print(f'   标题: {title}')
    print(f'   内容: {content}')
    time.sleep(0.7)


@BoosterParams(
    queue_name='q_audit_all_notifications',  # 队列6：审计所有通知
    broker_kind=BROKER_KIND_FOR_TEST,
    broker_exclusive_config={
        'exchange_name': EXCHANGE_NAME,
        'exchange_type': 'headers',
        # headers 模式的绑定条件：只要有 user_id 头属性即可（用于审计）
        'headers_for_bind': {
            'has_user_id': 'true'  # 自定义的审计标记
        },
        'x_match_for_bind': 'all',
    })
def audit_all_notifications_consumer(user_id: str, title: str, content: str, timestamp: str):
    """审计通知消费者 - 记录所有通知用于审计"""
    print(f'📋【审计记录】用户 {user_id} | {timestamp}')
    print(f'   标题: {title}')
    print(f'   类型: 通知审计记录')
    time.sleep(0.2)


if __name__ == '__main__':
    # 清理之前的消息（可选）
    # urgent_notifications_consumer.clear()
    # high_priority_notifications_consumer.clear()
    # mobile_notifications_consumer.clear()
    # system_admin_notifications_consumer.clear()
    # marketing_notifications_consumer.clear()
    # audit_all_notifications_consumer.clear()

    # 启动所有消费者
    print("启动所有通知服务消费者...")
    urgent_notifications_consumer.consume()
    high_priority_notifications_consumer.consume()
    mobile_notifications_consumer.consume()
    system_admin_notifications_consumer.consume()
    marketing_notifications_consumer.consume()
    audit_all_notifications_consumer.consume()

    print("所有通知服务消费者已启动，等待消息...")
    print("Headers 路由模式特点:")
    print("  - 🏷️  基于消息头属性路由：根据消息的头部属性进行匹配")
    print("  - 🎯 灵活的匹配规则：支持 'all'（全匹配）和 'any'（任意匹配）")
    print("  - 🚫 忽略路由键：完全基于头属性，不使用路由键")
    print("  - 🔧 复杂条件路由：可以实现复杂的业务逻辑路由")
    print()
    print("消费者绑定规则:")
    print("  - 🚨 紧急通知: priority=high AND urgent=true")
    print("  - ⚡ 高优先级: priority=high")
    print("  - 📱 移动端: platform=mobile OR device_type=phone")
    print("  - 🔧 系统管理: category=system AND role=admin")
    print("  - 📢 营销通知: category=marketing OR priority=low")
    print("  - 📋 审计记录: has_user_id=true")
    print("按 Ctrl+C 停止消费...")

    # 阻塞主线程，使消费者可以持续运行
    ctrl_c_recv()
