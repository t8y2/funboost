# RabbitMQ Headers 路由模式示例

本示例演示了如何使用 funboost 框架实现 RabbitMQ 的 Headers 路由模式。

## Headers 路由模式特点

Headers 路由模式是 RabbitMQ 中最灵活的路由方式，具有以下特点：

- 🏷️ **基于消息头属性**：完全根据消息的头部属性进行路由，忽略路由键
- 🎯 **灵活的匹配规则**：支持 `all`（全匹配）和 `any`（任意匹配）两种策略
- 🔧 **复杂条件路由**：可以实现复杂的业务逻辑路由条件
- 📊 **多维度匹配**：支持多个头属性的组合匹配

## 文件说明

- `t_headers_consume.py`: 消费者示例，展示不同的头属性绑定规则
- `t_headers_pub.py`: 发布者示例，展示如何使用动态消息头发布消息

## 业务场景示例

本示例模拟了一个智能通知系统，根据消息的不同属性将通知路由到相应的处理服务：

### 消费者服务及绑定规则

1. **🚨 紧急通知服务** (`q_urgent_notifications`)
   - 绑定条件: `priority=high` **AND** `urgent=true`
   - 匹配策略: `all` (必须同时满足所有条件)
   - 处理: 最高优先级的紧急通知

2. **⚡ 高优先级通知服务** (`q_high_priority_notifications`)
   - 绑定条件: `priority=high`
   - 匹配策略: `all`
   - 处理: 所有高优先级通知

3. **📱 移动端通知服务** (`q_mobile_notifications`)
   - 绑定条件: `platform=mobile` **OR** `device_type=phone`
   - 匹配策略: `any` (满足任意一个条件即可)
   - 处理: 移动端相关通知

4. **🔧 系统管理通知服务** (`q_system_admin_notifications`)
   - 绑定条件: `category=system` **AND** `role=admin`
   - 匹配策略: `all`
   - 处理: 系统管理员专用通知

5. **📢 营销通知服务** (`q_marketing_notifications`)
   - 绑定条件: `category=marketing` **OR** `priority=low`
   - 匹配策略: `any`
   - 处理: 营销推广相关通知

6. **📋 审计通知服务** (`q_audit_all_notifications`)
   - 绑定条件: `has_user_id=true`
   - 匹配策略: `all`
   - 处理: 所有需要审计的通知记录

## 运行示例

### 1. 启动消费者

```bash
cd test_frame/test_broker_rabbitmq/test_rabbitmq_complex_routing/t_headers
python t_headers_consume.py
```

### 2. 发布消息

在另一个终端中运行：

```bash
cd test_frame/test_broker_rabbitmq/test_rabbitmq_complex_routing/t_headers
python t_headers_pub.py
```

## 消息路由示例

| 消息类型 | 消息头属性 | 匹配的消费者 |
|---------|-----------|-------------|
| 系统严重故障 | `priority=high, urgent=true, category=system, role=admin` | 🚨紧急 + ⚡高优先级 + 🔧系统管理 + 📋审计 |
| 订单支付成功 | `priority=high, platform=mobile` | ⚡高优先级 + 📱移动端 + 📋审计 |
| 新功能上线 | `priority=low, category=marketing` | 📢营销通知 + 📋审计 |
| 账户安全提醒 | `priority=high, urgent=true, device_type=phone` | 🚨紧急 + ⚡高优先级 + 📱移动端 + 📋审计 |
| 系统维护通知 | `category=system, role=admin, priority=medium` | 🔧系统管理 + 📋审计 |

## 核心配置说明

### 消费者配置

```python
@BoosterParams(
    queue_name='队列名称',
    broker_kind=BrokerEnum.RABBITMQ_COMPLEX_ROUTING,
    broker_exclusive_config={
        'exchange_name': 'headers_notification_exchange',
        'exchange_type': 'headers',
        'headers_for_bind': {
            'priority': 'high',      # 头属性匹配条件
            'urgent': 'true'         # 可以设置多个条件
        },
        'x_match_for_bind': 'all',   # 'all' 或 'any'
    })
def consumer_function(user_id: str, title: str, content: str, timestamp: str):
    # 消费者函数的参数名必须与发布的字典 keys 完全一致
    pass
```

### 发布者配置

```python
headers_publisher = BoostersManager.get_cross_project_publisher(PublisherParams(
    queue_name='发布者实例名',
    broker_kind=BrokerEnum.RABBITMQ_COMPLEX_ROUTING,
    broker_exclusive_config={
        'exchange_name': 'headers_notification_exchange',
        'exchange_type': 'headers',
        # headers 模式不使用路由键
    }
))

# 发布消息时指定头属性
headers_publisher.publish(
    {'user_id': 'user001', 'title': '标题', 'content': '内容', 'timestamp': '时间'},
    task_options=TaskOptions(
        other_extra_params={
            'headers_for_publish': {
                'priority': 'high',
                'urgent': 'true',
                'category': 'system'
            }
        }
    )
)
```

## 匹配策略说明

### `x_match_for_bind: 'all'` (全匹配)
- 消息头必须包含**所有**指定的属性，且值完全匹配
- 适用于需要严格条件控制的场景

### `x_match_for_bind: 'any'` (任意匹配)  
- 消息头只需包含**任意一个**指定的属性匹配即可
- 适用于多种条件都可以触发的场景

## 使用场景

Headers 路由模式特别适合以下场景：

1. **智能通知系统**: 根据优先级、平台、用户角色等多维度路由
2. **多租户系统**: 根据租户ID、权限级别等属性路由
3. **内容分发系统**: 根据内容类型、地区、语言等属性路由
4. **监控告警系统**: 根据告警级别、服务类型、责任人等路由
5. **工作流系统**: 根据任务类型、处理人、优先级等路由
6. **API网关**: 根据请求来源、认证级别、API版本等路由

## 与其他路由模式的对比

| 路由模式 | 路由依据 | 灵活性 | 复杂度 | 适用场景 |
|---------|---------|--------|--------|---------|
| **Headers** | 消息头属性 | 最高 | 最复杂 | 复杂的多维度路由 |
| **Topic** | 通配符路由键 | 高 | 中等 | 层次化的消息分类 |
| **Direct** | 精确路由键 | 中等 | 简单 | 点对点或简单分组 |
| **Fanout** | 无条件广播 | 最低 | 最简单 | 广播通知 |

## 注意事项

1. **参数匹配规则**: 发布者发布的字典 keys 必须与消费者函数的参数名完全一致
   - 发布: `{'user_id': '...', 'title': '...', 'content': '...', 'timestamp': '...'}`
   - 消费: `def consumer(user_id: str, title: str, content: str, timestamp: str):`

2. **头属性类型**: 所有头属性值都是字符串类型，需要注意类型转换

3. **性能考虑**: Headers 路由比其他模式稍慢，因为需要检查多个头属性

4. **路由键被忽略**: Headers 模式完全忽略路由键，只基于头属性路由

5. **匹配策略选择**: 
   - 使用 `all` 时要确保消息头包含所有必需属性
   - 使用 `any` 时要注意可能的意外匹配

6. **调试建议**: 建议在开发阶段添加审计队列来观察所有消息的路由情况
