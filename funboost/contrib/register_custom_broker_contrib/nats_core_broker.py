# -*- coding: utf-8 -*-
"""
NATS Core Broker - 基于 NATS Core 的轻量级消息队列

设计理念：
    - 使用 nats-py (官方asyncio客户端) 实现 NATS Core 发布/订阅
    - 轻量高性能，适用于对延迟敏感但不需要持久化的场景
    - 不支持持久化和消费确认，消息丢失风险由业务层自行处理
    - 支持 Queue Group（消费者组），多个消费者实例可负载均衡分摊消息
    - 支持 Request-Reply 模式，发布者可同步等待消费者响应结果

使用方式：
    from funboost import boost, BoosterParams, BrokerEnum

    # 默认模式（负载均衡）：多个消费者分摊消息
    @boost(BoosterParams(
        queue_name='nats_core_queue',
        broker_kind=BrokerEnum.NATS_CORE,
    ))
    def process_message(x, y):
        return x + y

    # 广播模式：每个消费者都收到全部消息
    @boost(BoosterParams(
        queue_name='nats_core_broadcast',
        broker_kind=BrokerEnum.NATS_CORE,
        broker_exclusive_config={'queue_group': ''},
    ))
    def broadcast_handler(x, y):
        return x + y

    # Request-Reply 模式：发布者同步等待消费者响应
    result = process_message.request({"x": 1, "y": 2}, timeout=5)
    print(result)  # b'3'

    如需持久化+ACK，请使用 BrokerEnum.NATS_JETSTREAM

依赖：
    pip install nats-py
"""

import asyncio
import json
import threading

import nats

from funboost import register_custom_broker, AbstractConsumer, AbstractPublisher, BrokerEnum
from funboost.core.broker_kind__exclusive_config_default_define import register_broker_exclusive_config_default
from funboost.funboost_config_deafult import BrokerConnConfig

register_broker_exclusive_config_default(BrokerEnum.NATS_CORE, {
    'nats_url': '',          # 可选，覆盖全局 BrokerConnConfig.NATS_URL
    'queue_group': 'funboost_group',  # 消费者组名；非空=负载均衡，空字符串=广播模式
})


class NatsPublisher(AbstractPublisher):
    """NATS Core 发布者，使用 nats-py 官方 asyncio 客户端"""

    def custom_init(self):
        super().custom_init()
        config = self.publisher_params.broker_exclusive_config
        self._nats_url = config['nats_url'] or BrokerConnConfig.NATS_URL

        self._loop = asyncio.new_event_loop()
        self._loop_thread = threading.Thread(target=self._loop.run_forever, daemon=True)
        self._loop_thread.start()

        async def _connect():
            self._nc = await nats.connect(
                self._nats_url,
                reconnect_time_wait=2,
                max_reconnect_attempts=-1,
            )

        future = asyncio.run_coroutine_threadsafe(_connect(), self._loop)
        future.result(timeout=10)
        self.logger.info(f'NATS Core Publisher 连接成功: {self._nats_url}')

    def _publish_impl(self, msg):
        async def _pub():
            await self._nc.publish(self.queue_name, msg.encode() if isinstance(msg, str) else msg)

        future = asyncio.run_coroutine_threadsafe(_pub(), self._loop)
        future.result(timeout=5)

    def request(self, msg: dict, timeout: float = 5):
        """
        NATS Request-Reply 模式：发送消息并同步等待消费者响应。

        消费者端无需任何修改，当消费者检测到消息 extra.other_extra_params._nats_need_reply=True 时，
        框架会自动将函数返回值响应回去。

        :param msg: 消费函数的入参字典，例如 {"x": 1, "y": 2}
        :param timeout: 等待响应的超时秒数，默认5秒
        :return: 消费者响应的原始 bytes 数据
        :raises nats.errors.TimeoutError: 超时未收到响应
        """
        future = asyncio.run_coroutine_threadsafe(self.aio_request(msg, timeout), self._loop)
        return future.result(timeout=timeout + 2)

    async def aio_request(self, msg: dict, timeout: float = 5):
        msg = dict(msg)
        msg.setdefault('extra', {}).setdefault('other_extra_params', {})['_nats_need_reply'] = True
        publish_msg_context = self.generate_msg_context_for_publish(msg)
        data = publish_msg_context.msg_json.encode() if isinstance(publish_msg_context.msg_json, str) else publish_msg_context.msg_json
        response = await self._nc.request(self.queue_name, data, timeout=timeout)
        return json.loads(response.data) # 可以直接返回真实类型，而不返回bytes 和字符串

    def clear(self):
        pass

    def get_message_count(self):
        # nats core 不支持消息存储，那么获取数量是无稽之谈，压根不需要。
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

    消费者组(Queue Group)：
        - queue_group 非空时，同组消费者负载均衡分摊消息（默认行为）
        - queue_group 为空字符串时，所有消费者都会收到每条消息（广播模式）

    Request-Reply 模式：
        - 当发布者使用 request() 发送消息时，NATS 会自动在消息上设置 reply subject
        - 消费者通过框架钩子自动检测并响应，无需用户额外编码
    """

    def custom_init(self):
        super().custom_init()
        config = self.consumer_params.broker_exclusive_config
        self._nats_url = config['nats_url'] or BrokerConnConfig.NATS_URL
        self._queue_group = config['queue_group']
        self._consumer_loop = None
        self._consumer_nc = None

    def _dispatch_task(self):
        async def _run():
            self._consumer_nc = await nats.connect(
                self._nats_url,
                reconnect_time_wait=2,
                max_reconnect_attempts=-1,
            )
            self._consumer_loop = asyncio.get_event_loop()

            async def message_handler(msg):
                kw = {'body': msg.data}
                msg_dict = json.loads(msg.data)
                if msg_dict.get('extra', {}).get('other_extra_params', {}).get('_nats_need_reply'):
                    kw['_nats_need_reply'] = True
                    kw['_nats_msg'] = msg
                self._submit_task(kw)

            subscribe_kwargs = dict(subject=self.queue_name, cb=message_handler)
            if self._queue_group:
                subscribe_kwargs['queue'] = self._queue_group
            await self._consumer_nc.subscribe(**subscribe_kwargs)

            mode_desc = f'负载均衡(group={self._queue_group})' if self._queue_group else '广播模式'
            self.logger.info(f'NATS Core 消费者启动: {self._nats_url}, subject={self.queue_name}, {mode_desc}')

            stop_event = asyncio.Event()
            await stop_event.wait()

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(_run())

    async def _nats_reply(self, current_function_result_status, kw: dict):
        if not kw.get('_nats_need_reply'):
            return
        if current_function_result_status.success:
            result = current_function_result_status.result
            response_data = json.dumps(result).encode() if not isinstance(result, bytes) else result
        else:
            response_data = json.dumps({'error': 'function failed after retries'}).encode()
        nats_msg = kw['_nats_msg']
        try:
            await nats_msg.respond(response_data)
        except Exception as e:
            self.logger.warning(f'NATS request-reply 响应失败: {e}')

    def _frame_custom_record_process_info_func(self, current_function_result_status, kw: dict):
        super()._frame_custom_record_process_info_func(current_function_result_status, kw)
        asyncio.run_coroutine_threadsafe(self._nats_reply(current_function_result_status, kw), self._consumer_loop)

    async def _aio_frame_custom_record_process_info_func(self, current_function_result_status, kw: dict):
        await super()._aio_frame_custom_record_process_info_func(current_function_result_status, kw)
        await self._nats_reply(current_function_result_status, kw)

    def _confirm_consume(self, kw):
        pass

    def _requeue(self, kw):
        self.publisher_of_same_queue.publish(kw['body'])


register_custom_broker(BrokerEnum.NATS_CORE, NatsPublisher, NatsConsumer)
