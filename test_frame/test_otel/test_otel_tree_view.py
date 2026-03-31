# -*- coding: utf-8 -*-
"""
Funboost OpenTelemetry 链路追踪 Demo - 树状结构图版本

使用 TreeSpanExporter 在控制台直接显示树状链路追踪图，无需安装 Jaeger 等中间件。
生产环境强烈建议使用专业的 opentelemetry 链路追踪中间件，例如 Jaeger/Zipkin/SkyWalking 等。
"""

# 完美的树状结构图，能清的看到消息流转过程。
# task_entry 发布2个任务到otel_tree_task_process，otel_tree_task_process 再发布1个任务到otel_tree_task_notify
"""
================================================================================
🌳 链路追踪树状结构图
================================================================================

📍 Trace ID: f50f7a80f0b8f88b97788093157c4ae2
------------------------------------------------------------
└── 📤 otel_tree_task_entry send [PRODUCER] ✅ 11.0ms
       🆔 span_id: 0x1c167373656fdc13    parent_id: null
       📋 task_id: 019b4ed4-144d-76b2-86b0-7d4939fc94dc
    └── 📥 otel_tree_task_entry process [CONSUMER] ✅ 323.2ms
           🆔 span_id: 0xbc7fa8b030d5f600    parent_id: 0x1c167373656fdc13
           📋 task_id: 019b4ed4-144d-76b2-86b0-7d4939fc94dc
        ├── 📤 otel_tree_task_process send [PRODUCER] ✅ 2.0ms
        │      🆔 span_id: 0xc1a5e958ffd61344    parent_id: 0xbc7fa8b030d5f600
        │      📋 task_id: 019b4ed4-1a6d-7be3-8516-192449685f6d
        │   └── 📥 otel_tree_task_process process [CONSUMER] ✅ 215.9ms
        │          🆔 span_id: 0x575c4f47a70564b9    parent_id: 0xc1a5e958ffd61344
        │          📋 task_id: 019b4ed4-1a6d-7be3-8516-192449685f6d
        │       └── 📤 otel_tree_task_notify send [PRODUCER] ✅ 2.0ms
        │              🆔 span_id: 0x81e9758e44a4ba61    parent_id: 0x575c4f47a70564b9      
        │              📋 task_id: 019b4ed4-4118-79fd-965c-c080bb0ca775
        │           └── 📥 otel_tree_task_notify process [CONSUMER] ✅ 118.5ms
        │                  🆔 span_id: 0x669734d0fa7eae20    parent_id: 0x81e9758e44a4ba61  
        │                  📋 task_id: 019b4ed4-4118-79fd-965c-c080bb0ca775
        └── 📤 otel_tree_task_process send [PRODUCER] ✅ 2.3ms
               🆔 span_id: 0x986af7dffd837e77    parent_id: 0xbc7fa8b030d5f600
               📋 task_id: 019b4ed4-1a70-7d62-99cd-7e6e0f9038bf
            └── 📥 otel_tree_task_process process [CONSUMER] ✅ 212.6ms
                   🆔 span_id: 0xdb03f7288701f9bd    parent_id: 0x986af7dffd837e77
                   📋 task_id: 019b4ed4-1a70-7d62-99cd-7e6e0f9038bf
                └── 📤 otel_tree_task_notify send [PRODUCER] ✅ 2.0ms
                       🆔 span_id: 0x5ad4e057be91c960    parent_id: 0xdb03f7288701f9bd      
                       📋 task_id: 019b4ed4-4120-7c53-8a5f-4f653d4e486f
                    └── 📥 otel_tree_task_notify process [CONSUMER] ✅ 107.7ms
                           🆔 span_id: 0xff4fd0fdf38fed92    parent_id: 0x5ad4e057be91c960  
                           📋 task_id: 019b4ed4-4120-7c53-8a5f-4f653d4e486f

📍 Trace ID: 6b0053464b0d8649a7ff5a09e34a6813
------------------------------------------------------------
└── 📤 otel_tree_task_entry send [PRODUCER] ✅ 6.5ms
       🆔 span_id: 0xe0d40211831caab2    parent_id: null
       📋 task_id: 019b4ed4-145b-7dcf-8e0b-ff2e334ec309
    └── 📥 otel_tree_task_entry process [CONSUMER] ✅ 321.0ms
           🆔 span_id: 0x607c15d155921877    parent_id: 0xe0d40211831caab2
           📋 task_id: 019b4ed4-145b-7dcf-8e0b-ff2e334ec309
        ├── 📤 otel_tree_task_process send [PRODUCER] ✅ 2.3ms
        │      🆔 span_id: 0xb7e76886ba6b0ab0    parent_id: 0x607c15d155921877
        │      📋 task_id: 019b4ed4-1a6e-7a1d-ad82-5231ec9bc56e
        │   └── 📥 otel_tree_task_process process [CONSUMER] ✅ 214.6ms
        │          🆔 span_id: 0x9a1d938da26d9eb8    parent_id: 0xb7e76886ba6b0ab0
        │          📋 task_id: 019b4ed4-1a6e-7a1d-ad82-5231ec9bc56e
        │       └── 📤 otel_tree_task_notify send [PRODUCER] ✅ 1.8ms
        │              🆔 span_id: 0x6e66697fcee92094    parent_id: 0x9a1d938da26d9eb8      
        │              📋 task_id: 019b4ed4-411d-775c-b592-84396f0857b4
        │           └── 📥 otel_tree_task_notify process [CONSUMER] ✅ 115.8ms
        │                  🆔 span_id: 0xd1d7235f6b247456    parent_id: 0x6e66697fcee92094  
        │                  📋 task_id: 019b4ed4-411d-775c-b592-84396f0857b4
        └── 📤 otel_tree_task_process send [PRODUCER] ✅ 1.5ms
               🆔 span_id: 0xa22a5683b764f63b    parent_id: 0x607c15d155921877
               📋 task_id: 019b4ed4-1a71-741a-ad95-5cf65ce9b8f0
            └── 📥 otel_tree_task_process process [CONSUMER] ✅ 220.8ms
                   🆔 span_id: 0x14963a0749d609b8    parent_id: 0xa22a5683b764f63b
                   📋 task_id: 019b4ed4-1a71-741a-ad95-5cf65ce9b8f0
                └── 📤 otel_tree_task_notify send [PRODUCER] ✅ 5.1ms
                       🆔 span_id: 0x6056d9ba300a795f    parent_id: 0x14963a0749d609b8      
                       📋 task_id: 019b4ed4-41ff-7146-8766-7e2bbe5e97fd
                    └── 📥 otel_tree_task_notify process [CONSUMER] ✅ 106.6ms
                           🆔 span_id: 0x911ac90dd90b901d    parent_id: 0x6056d9ba300a795f  
                           📋 task_id: 019b4ed4-41ff-7146-8766-7e2bbe5e97fd
================================================================================
"""


import asyncio

import time
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource

from funboost import boost, BrokerEnum, BoosterParams, ConcurrentModeEnum,fct
from funboost.contrib.override_publisher_consumer_cls.funboost_otel_mixin import (
    AutoOtelPublisherMixin,
    AutoOtelConsumerMixin,
    OtelBoosterParams
)
from funboost.contrib.override_publisher_consumer_cls.otel_tree_span_exporter import (
    TreeSpanExporter,
    print_trace_tree
)


# =============================================================================
# 第1步: 初始化 OpenTelemetry（使用 TreeSpanExporter）
# =============================================================================
tree_exporter = None  # 全局变量，方便手动调用打印


def init_opentelemetry():
    """
    初始化 OpenTelemetry 配置
    使用 TreeSpanExporter 在控制台显示树状结构图
    """
    global tree_exporter
    
    # 创建资源标识
    resource = Resource.create({
        "service.name": "funboost-otel-demo",
        "service.version": "1.0.0",
    })

    # 创建 TracerProvider
    provider = TracerProvider(resource=resource)

    # 使用 TreeSpanExporter - 任务完成后手动调用 print_tree() 打印树状图
    tree_exporter = TreeSpanExporter()
    provider.add_span_processor(BatchSpanProcessor(tree_exporter))

    # 设置全局 TracerProvider
    trace.set_tracer_provider(provider)

    print("✅ OpenTelemetry 初始化完成（使用 TreeSpanExporter）")


# =============================================================================
# 第2步: 定义带 OTEL 追踪的任务函数
# =============================================================================

@boost(OtelBoosterParams(
    queue_name='otel_tree_task_entry',
    broker_kind=BrokerEnum.SQLITE_QUEUE,
    concurrent_num=2,
   
))
def task_entry(order_id: int, user_name: str):
    """入口任务：处理订单入口"""

    print(fct.full_msg)
    print(f"📦 [任务入口] 开始处理订单 #{order_id}，用户: {user_name}")
    time.sleep(0.3)

    # 触发下游任务
    aio_task_process.push(order_id=order_id, step="验证库存")
    aio_task_process.push(order_id=order_id, step="计算价格")

    print(f"✅ [任务入口] 订单 #{order_id} 已分发")
    return {"status": "dispatched", "order_id": order_id}


@boost(OtelBoosterParams(
    queue_name='otel_tree_task_process',
    broker_kind=BrokerEnum.SQLITE_QUEUE,
    concurrent_num=3,
    concurrent_mode=ConcurrentModeEnum.ASYNC,
   
))
async def aio_task_process(order_id: int, step: str):
    """处理任务：执行具体的订单处理步骤"""
    print(fct.full_msg)
    print(f"⚙️ [处理任务] 订单 #{order_id} - 执行步骤: {step}")
    await asyncio.sleep(0.2)

    # 触发通知任务
    task_notify.push(order_id=order_id, message=f"步骤 '{step}' 已完成")

    print(f"✅ [处理任务] 订单 #{order_id} - 步骤 '{step}' 完成")
    return {"order_id": order_id, "step": step, "status": "completed"}


@boost(OtelBoosterParams(
    queue_name='otel_tree_task_notify',
    broker_kind=BrokerEnum.SQLITE_QUEUE,
    concurrent_num=2,
   
))
def task_notify(order_id: int, message: str):
    """通知任务：发送通知"""
    print(fct.full_msg)
    print(f"📧 [通知任务] 订单 #{order_id} - 发送通知: {message}")
    time.sleep(0.1)
    print(f"✅ [通知任务] 订单 #{order_id} - 通知发送完成")
    return {"order_id": order_id, "notified": True}


# =============================================================================
# 主程序入口
# =============================================================================
if __name__ == '__main__':
    # 初始化 OpenTelemetry
    init_opentelemetry()

    print("\n" + "=" * 60)
    print("🚀 Funboost OpenTelemetry 链路追踪 Demo - 树状图版本")
    print("=" * 60 + "\n")

    # 发布任务
    print("【发布任务】")
    task_entry.push(order_id=1, user_name="张三")
    task_entry.push(order_id=2, user_name="李四")

    print("\n" + "-" * 60)
    print("📡 开始消费任务...")
    print("-" * 60 + "\n")

    # 启动所有消费者（非阻塞方式）
    task_notify.consume()
    aio_task_process.consume()
    task_entry.consume()

    # 使用 wait_for_possible_has_finish_all_tasks 判断任务是否消费完成
    # 这比固定 sleep 更准确
    from funboost.consumers.base_consumer import wait_for_possible_has_finish_all_tasks_by_conusmer_list
    
    print("⏳ 等待所有任务消费完成...")
    
    # 获取消费者实例列表
    consumer_list = [
        task_entry.consumer,
        aio_task_process.consumer,
        task_notify.consumer,
    ]
    
    # 等待所有消费者完成任务（连续 2 分钟没有新任务且队列为空则认为完成）
    # wait_for_possible_has_finish_all_tasks_by_conusmer_list(consumer_list, minutes=2)
    time.sleep(30)
    
    print("\n✅ 所有任务已消费完成！")

    # 打印树状图
    print("\n" + "=" * 60)
    print("🎯 链路追踪树状图")
    print("=" * 60)
    tree_exporter.print_tree()

    print("\n✅ Demo 完成！")
    
    # 退出程序
    import os
    os._exit(0)

