# -*- coding: utf-8 -*-
"""
NATS Core Broker - 基于 NATS Core 的轻量级消息队列

设计理念：
    - 使用 nats-py (官方asyncio客户端) 实现 NATS Core 发布/订阅
    - 轻量高性能，适用于对延迟敏感但不需要持久化的场景
    - 不支持持久化和消费确认，消息丢失风险由业务层自行处理

使用方式：
    from funboost import boost, BoosterParams, BrokerEnum

    @boost(BoosterParams(
        queue_name='nats_core_queue',
        broker_kind=BrokerEnum.NATS_CORE,
    ))
    def process_message(x, y):
        return x + y

    如需持久化+ACK，请使用 BrokerEnum.NATS_JETSTREAM

依赖：
    pip install nats-py
"""

import asyncio
import threading

import nats

from funboost import register_custom_broker, AbstractConsumer, AbstractPublisher, BrokerEnum
from funboost.funboost_config_deafult import BrokerConnConfig


class NatsPublisher(AbstractPublisher):
    """NATS Core 发布者，使用 nats-py 官方 asyncio 客户端"""

    def custom_init(self):
        self._loop = asyncio.new_event_loop()
        self._loop_thread = threading.Thread(target=self._loop.run_forever, daemon=True)
        self._loop_thread.start()

        async def _connect():
            self._nc = await nats.connect(
                BrokerConnConfig.NATS_URL,
                reconnect_time_wait=2,
                max_reconnect_attempts=-1,
            )

        future = asyncio.run_coroutine_threadsafe(_connect(), self._loop)
        future.result(timeout=10)
        self.logger.info(f'NATS Core Publisher 连接成功: {BrokerConnConfig.NATS_URL}')

    def _publish_impl(self, msg):
        async def _pub():
            await self._nc.publish(self.queue_name, msg.encode() if isinstance(msg, str) else msg)

        future = asyncio.run_coroutine_threadsafe(_pub(), self._loop)
        future.result(timeout=5)

    def clear(self):
        pass

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


class NatsConsumer(AbstractConsumer):
    """
    NATS Core 消费者，使用 nats-py 官方 asyncio 客户端。

    注意: NATS Core 模式不支持持久化和消费确认。
    如需持久化+ACK，请使用 NATS_JETSTREAM broker。
    """

    def _dispatch_task(self):
        async def _run():
            nc = await nats.connect(
                BrokerConnConfig.NATS_URL,
                reconnect_time_wait=2,
                max_reconnect_attempts=-1,
            )
            self.logger.info(f'NATS Core 连接成功: {BrokerConnConfig.NATS_URL}')

            async def message_handler(msg):
                kw = {'body': msg.data}
                self._submit_task(kw)

            await nc.subscribe(self.queue_name, cb=message_handler)

            stop_event = asyncio.Event()
            await stop_event.wait()

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(_run())

    def _confirm_consume(self, kw):
        pass

    def _requeue(self, kw):
        self.publisher_of_same_queue.publish(kw['body'])


register_custom_broker(BrokerEnum.NATS_CORE, NatsPublisher, NatsConsumer)
