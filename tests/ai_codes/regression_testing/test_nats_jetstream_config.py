# -*- coding: utf-8 -*-
"""
NATS JetStream broker 回归测试
验证简化后的设计：stream_name = queue_name, subject = queue_name
"""
import sys
sys.path.insert(0, r'd:\codes\funboost')

from funboost.core.broker_kind__exclusive_config_default_define import broker_kind__exclusive_config_default_map
from funboost.constant import BrokerEnum


def test_exclusive_config_no_stream_name():
    """验证 broker_exclusive_config 中已移除 stream_name 字段"""
    from funboost.contrib.register_custom_broker_contrib import nats_jetstream_broker
    config = broker_kind__exclusive_config_default_map[BrokerEnum.NATS_JETSTREAM]
    assert 'stream_name' not in config, "stream_name 应该已被移除"
    assert 'nats_url' in config
    assert 'consumer_group' in config
    assert 'ack_wait' in config
    assert 'max_deliver' in config
    print("[PASS] test_exclusive_config_no_stream_name")


def test_publisher_no_stream_name_attr():
    """验证 Publisher 类不再使用 self._stream_name 属性和 self._subject 属性"""
    from funboost.contrib.register_custom_broker_contrib.nats_jetstream_broker import NatsJetStreamPublisher
    import inspect
    source = inspect.getsource(NatsJetStreamPublisher)
    assert 'self._stream_name' not in source, "Publisher 不应再引用 self._stream_name"
    assert 'self._subject' not in source, "Publisher 不应再引用 self._subject 属性"
    assert 'self.queue_name' in source, "Publisher 应直接使用 self.queue_name"
    print("[PASS] test_publisher_no_stream_name_attr")


def test_consumer_no_stream_name_attr():
    """验证 Consumer 类不再使用 self._stream_name 属性和 self._subject 属性"""
    from funboost.contrib.register_custom_broker_contrib.nats_jetstream_broker import NatsJetStreamConsumer
    import inspect
    source = inspect.getsource(NatsJetStreamConsumer)
    assert 'self._stream_name' not in source, "Consumer 不应再引用 self._stream_name"
    assert 'self._subject' not in source, "Consumer 不应再引用 self._subject 属性"
    assert 'self.queue_name' in source, "Consumer 应直接使用 self.queue_name"
    print("[PASS] test_consumer_no_stream_name_attr")


def test_consumer_durable_name():
    """验证 _durable_name 属性逻辑正确"""
    from funboost.contrib.register_custom_broker_contrib.nats_jetstream_broker import NatsJetStreamConsumer
    import inspect
    source = inspect.getsource(NatsJetStreamConsumer._durable_name.fget)
    assert 'queue_name' in source
    assert '_consumer_group' in source
    print("[PASS] test_consumer_durable_name")


if __name__ == '__main__':
    test_exclusive_config_no_stream_name()
    test_publisher_no_stream_name_attr()
    test_consumer_no_stream_name_attr()
    test_consumer_durable_name()
    print("\n[ALL PASS] NATS JetStream 配置回归测试全部通过")
