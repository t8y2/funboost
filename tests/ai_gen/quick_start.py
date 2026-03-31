#!/usr/bin/env python3
"""
KafkaManyThreadsConsumer 快速开始示例

运行前准备:
1. pip install kafka-python
2. 启动Kafka服务器 (localhost:9092)  
3. 创建测试topic: kafka-topics.sh --create --topic test-topic --partitions 2 --bootstrap-server localhost:9092

运行方式:
python quick_start.py
"""

import time
import random
from kafka_many_threads_consumer import KafkaManyThreadsConsumer


def simple_message_handler(message):
    """
    简单的消息处理函数
    演示如何处理Kafka消息
    """
    # 模拟业务处理时间
    processing_time = random.uniform(0.1, 2.0)
    time.sleep(processing_time)
    
    print(f"✅ 处理完成: partition={message.partition}, offset={message.offset}, "
          f"耗时={processing_time:.2f}s")
    
    # 模拟偶尔的处理失败 (5%几率)
    if random.random() < 0.05:
        print(f"❌ 模拟处理失败: partition={message.partition}, offset={message.offset}")
        raise Exception("模拟的业务处理失败")


def main():
    print("🚀 启动 KafkaManyThreadsConsumer 演示")
    print("=" * 50)
    
    # 创建消费者实例
    consumer = KafkaManyThreadsConsumer(
        kafka_broker_address="localhost:9092",  # Kafka地址
        topic="test-topic",                     # 主题名称
        group_id="demo-group",                  # 消费者组
        num_threads=20,                         # 线程数 (可以远超分区数)
        callback_func=simple_message_handler   # 消息处理函数
    )
    
    try:
        # 启动消费者
        print("📡 启动消费者...")
        consumer.start()
        print("✅ 消费者启动成功!")
        print()
        
        # 运行60秒，每10秒打印一次统计信息
        for i in range(6):
            time.sleep(10)
            
            stats = consumer.get_stats()
            print(f"📊 统计信息 ({(i+1)*10}秒):")
            print(f"   消费消息数: {stats['consumed_count']}")
            print(f"   处理成功数: {stats['processed_count']}")
            print(f"   处理失败数: {stats['failed_count']}")
            print(f"   已提交数: {stats['committed_count']}")
            
            # 显示详细的offset状态
            offset_status = stats['offset_manager_status']
            if offset_status['pending_count']:
                print(f"   待处理队列: {offset_status['pending_count']}")
            if offset_status['committable_offsets']:
                print(f"   可提交offset: {offset_status['committable_offsets']}")
            print()
            
    except KeyboardInterrupt:
        print("\n🛑 接收到中断信号，正在优雅停止...")
        
    finally:
        # 停止消费者
        print("⏹️  停止消费者...")
        consumer.stop()
        print("✅ 消费者已停止")
        
        # 显示最终统计
        final_stats = consumer.get_stats()
        print("\n📈 最终统计:")
        print(f"   总消费: {final_stats['consumed_count']}")
        print(f"   总处理成功: {final_stats['processed_count']}")
        print(f"   总处理失败: {final_stats['failed_count']}")
        print(f"   总提交: {final_stats['committed_count']}")


if __name__ == "__main__":
    # 检查依赖
    try:
        import kafka
        print(f"✅ kafka-python 版本: {kafka.__version__}")
    except ImportError:
        print("❌ 请先安装kafka-python: pip install kafka-python")
        exit(1)
    
    print("🔧 配置检查:")
    print("   Kafka地址: localhost:9092")
    print("   主题: test-topic")
    print("   消费者组: demo-group")
    print("   线程数: 20")
    print()
    
    input("按Enter键开始演示... (确保Kafka服务器已启动并创建了test-topic)")
    
    main()
    
    print("\n🎉 演示完成!")
    print("💡 提示:")
    print("   - 这个实现确保了消息不丢失")
    print("   - 支持kill -9重启后继续消费")
    print("   - 线程数可以远超分区数")
    print("   - 自动管理offset提交顺序")