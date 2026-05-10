# -*- coding: utf-8 -*-
"""
NATS JetStream Broker - 基于 NATS JetStream 的持久化消息队列

设计理念：
    - 使用 NATS JetStream 实现消息持久化、消费确认、分组消费
    - 比 NATS Core 更可靠，支持 ACK、消息回放、持久化订阅
    - 适用于需要可靠消息传递但不想部署 RabbitMQ/Kafka 重型中间件的场景

使用方式：
    from funboost.contrib.register_custom_broker_contrib.nats_jetstream_broker import BROKER_KIND_NATS_JETSTREAM
    
    @boost(BoosterParams(
        queue_name='jetstream_queue',
        broker_kind=BROKER_KIND_NATS_JETSTREAM,
        broker_exclusive_config={
            'nats_url': 'nats://localhost:4222',  # 可选，默认从 BrokerConnConfig.NATS_URL 读
            'stream_name': 'funboost',            # 可选，默认 'funboost'
            'consumer_group': 'default',          # 可选，消费者组名
            'ack_wait': 60,                       # 可选，ACK 超时秒数
            'max_deliver': 3,                     # 可选，最大重投次数
        }
    ))
    def process_message(x, y):
        return x + y

依赖：
    pip install nats-py
"""

import asyncio
import threading

import nats
import nats.errors
from nats.js.api import ConsumerConfig

from funboost import register_custom_broker, AbstractConsumer, AbstractPublisher, BrokerEnum
from funboost.core.broker_kind__exclusive_config_default_define import register_broker_exclusive_config_default
from funboost.funboost_config_deafult import BrokerConnConfig

BROKER_KIND_NATS_JETSTREAM = BrokerEnum.NATS_JETSTREAM

register_broker_exclusive_config_default(BROKER_KIND_NATS_JETSTREAM, {
    'nats_url': '',
    'stream_name': 'funboost',
    'consumer_group': 'default',
    'ack_wait': 60,
    'max_deliver': 3,
})


class NatsJetStreamPublisher(AbstractPublisher):
    """NATS JetStream 发布者，消息持久化到 Stream"""

    def custom_init(self):
        super().custom_init()
        config = self.publisher_params.broker_exclusive_config
        self._nats_url = config['nats_url'] or BrokerConnConfig.NATS_URL
        self._stream_name = config['stream_name']

        self._loop = asyncio.new_event_loop()
        self._loop_thread = threading.Thread(target=self._loop.run_forever, daemon=True)
        self._loop_thread.start()

        async def _init():
            self._nc = await nats.connect(
                self._nats_url,
                reconnect_time_wait=2,
                max_reconnect_attempts=-1,
            )
            self._js = self._nc.jetstream()
            try:
                await self._js.find_stream_name_by_subject(self._subject)
            except Exception:
                await self._js.add_stream(
                    name=self._stream_name,
                    subjects=[f"{self._stream_name}.*"],
                    retention="workqueue",
                )

        future = asyncio.run_coroutine_threadsafe(_init(), self._loop)
        future.result(timeout=15)
        self.logger.info(f'NATS JetStream Publisher 初始化完成, stream={self._stream_name}')

    @property
    def _subject(self):
        return f"{self._stream_name}.{self.queue_name}"

    def _publish_impl(self, msg):
        async def _pub():
            data = msg.encode() if isinstance(msg, str) else msg
            await self._js.publish(self._subject, data)

        future = asyncio.run_coroutine_threadsafe(_pub(), self._loop)
        future.result(timeout=10)

    def clear(self):
        async def _purge():
            try:
                await self._js.purge_stream(self._stream_name, subject=self._subject)
            except Exception as e:
                self.logger.warning(f'清空 JetStream 消息失败: {e}')

        future = asyncio.run_coroutine_threadsafe(_purge(), self._loop)
        future.result(timeout=10)

    def get_message_count(self):
        return -1

    def close(self):
        if hasattr(self, '_nc'):
            async def _close():
                await self._nc.close()
            try:
                future = asyncio.run_coroutine_threadsafe(_close(), self._loop)
                future.result(timeout=5)
            except Exception:
                pass
        if hasattr(self, '_loop'):
            self._loop.call_soon_threadsafe(self._loop.stop)


class NatsJetStreamConsumer(AbstractConsumer):
    """
    NATS JetStream 消费者

    特点：
    - 持久化消费（durable consumer），重启不丢失消费位置
    - 支持消费确认（ACK），未确认的消息会重投
    - 支持消费者组（多个消费者分摊消息）
    - Pull 模式拉取消息
    """
    _REQUEUE_IS_NATIVE_NACK = True

    def custom_init(self):
        super().custom_init()
        config = self.consumer_params.broker_exclusive_config
        self._nats_url = config['nats_url'] or BrokerConnConfig.NATS_URL
        self._stream_name = config['stream_name']
        self._consumer_group = config['consumer_group']
        self._ack_wait = config['ack_wait']
        self._max_deliver = config['max_deliver']

    @property
    def _subject(self):
        return f"{self._stream_name}.{self.queue_name}"

    @property
    def _durable_name(self):
        return f"{self.queue_name}_{self._consumer_group}"

    def _dispatch_task(self):
        self._loop = asyncio.new_event_loop()

        async def _run():
            nc = await nats.connect(
                self._nats_url,
                reconnect_time_wait=2,
                max_reconnect_attempts=-1,
            )
            js = nc.jetstream()

            try:
                await js.find_stream_name_by_subject(self._subject)
            except Exception:
                await js.add_stream(
                    name=self._stream_name,
                    subjects=[f"{self._stream_name}.*"],
                    retention="workqueue",
                )

            sub = await js.pull_subscribe(
                self._subject,
                durable=self._durable_name,
                config=ConsumerConfig(
                    ack_wait=self._ack_wait,
                    max_deliver=self._max_deliver,
                ),
            )
            self.logger.info(
                f'NATS JetStream 消费者启动, subject={self._subject}, '
                f'durable={self._durable_name}'
            )

            while True:
                try:
                    msgs = await sub.fetch(batch=1, timeout=5)
                    for msg in msgs:
                        kw = {'body': msg.data, '_nats_msg': msg}
                        self._submit_task(kw)
                except nats.errors.TimeoutError:
                    pass
                except Exception as e:
                    self.logger.error(f'JetStream 拉取消息异常: {e}')
                    await asyncio.sleep(1)

        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(_run())

    def _confirm_consume(self, kw):
        nats_msg = kw['_nats_msg']
        future = asyncio.run_coroutine_threadsafe(nats_msg.ack(), self._loop)
        future.result(timeout=5)

    def _requeue(self, kw):
        nats_msg = kw['_nats_msg']
        future = asyncio.run_coroutine_threadsafe(nats_msg.nak(), self._loop)
        future.result(timeout=5)


register_custom_broker(BROKER_KIND_NATS_JETSTREAM, NatsJetStreamPublisher, NatsJetStreamConsumer)
