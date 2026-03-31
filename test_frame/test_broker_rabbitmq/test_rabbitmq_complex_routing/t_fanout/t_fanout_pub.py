# -*- coding: utf-8 -*-
# @Author  : ydf

from funboost import BoostersManager, PublisherParams, BrokerEnum, TaskOptions
import time

BROKER_KIND_FOR_TEST = BrokerEnum.RABBITMQ_COMPLEX_ROUTING
EXCHANGE_NAME = 'fanout_broadcast_exchange'


if __name__ == '__main__':
    # 创建一个 fanout 发布者，用于广播消息给所有绑定的队列
    fanout_publisher = BoostersManager.get_cross_project_publisher(PublisherParams(
        queue_name='fanout_publisher_instance', 
        broker_kind=BROKER_KIND_FOR_TEST,
        broker_exclusive_config={
            'exchange_name': EXCHANGE_NAME,
            'exchange_type': 'fanout',
            # fanout 模式不需要设置 routing_key，会被忽略
        }
    ))

    print("开始发布用户操作事件消息...")
    print("=" * 60)

    # 模拟不同的用户操作事件
    user_events = [
        {
            'user_id': 'user_001',
            'action': '用户注册',
            'message': '新用户注册成功，需要发送欢迎通知'
        },
        {
            'user_id': 'user_002', 
            'action': '订单支付',
            'message': '用户完成订单支付，金额 ¥299.00'
        },
        {
            'user_id': 'user_003',
            'action': '密码修改',
            'message': '用户修改登录密码，需要安全提醒'
        },
        {
            'user_id': 'user_001',
            'action': '会员升级',
            'message': '用户升级为VIP会员，享受专属服务'
        },
        {
            'user_id': 'user_004',
            'action': '订单退款',
            'message': '用户申请订单退款，金额 ¥158.00'
        },
        {
            'user_id': 'user_002',
            'action': '评价商品',
            'message': '用户对商品进行了5星好评'
        },
        {
            'user_id': 'user_005',
            'action': '账户异常',
            'message': '检测到账户异常登录，需要安全验证'
        },
        {
            'user_id': 'user_003',
            'action': '积分兑换',
            'message': '用户使用积分兑换优惠券'
        }
    ]

    for i, event in enumerate(user_events, 1):
        print(f"[{i}] 发布事件: 用户 {event['user_id']} - {event['action']}")
        print(f"    消息内容: {event['message']}")
        
        # 发布消息 - fanout 模式会广播给所有绑定的队列
        # 注意：即使我们可以指定路由键，fanout 模式也会忽略它
        fanout_publisher.publish(
            {
                'user_id': event['user_id'],
                'action': event['action'], 
                'message': event['message']
            },
            task_options=TaskOptions(
                # 即使设置了路由键，fanout 模式也会忽略，所有队列都会收到消息
                other_extra_params={'routing_key_for_publish': 'ignored_routing_key'}
            )
        )
        
        print(f"    ✅ 消息已广播给所有服务（邮件、短信、推送、审计、数据分析）")
        print()
        
        # 稍微延迟，便于观察消费者处理过程
        time.sleep(1)

    print("=" * 60)
    print("所有事件消息发布完成！")
    print("\nFanout 路由模式说明:")
    print("  📢 每条消息都会被广播给所有 5 个服务:")
    print("     - 📧 邮件服务：发送邮件通知")
    print("     - 📱 短信服务：发送短信通知") 
    print("     - 🔔 推送服务：发送推送通知")
    print("     - 📝 审计服务：记录操作日志")
    print("     - 📊 数据分析：收集行为数据")
    print("  🚫 路由键被完全忽略，无论设置什么值都会广播给所有队列")
    print("  ⚡ 适合需要多个服务同时处理同一事件的场景")
