# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2023/8/6 0006 12:12

import abc

from funboost.concurrent_pool.async_helper import get_or_create_event_loop
from funboost.core.serialization import Serialization
from funboost.publishers.base_publisher import AbstractPublisher
from funboost.assist.faststream_helper import app, get_broker


class FastStreamPublisher(AbstractPublisher, metaclass=abc.ABCMeta):
    """
    使用 FastStream 作为中间件。

    FastStream 的发布通过 broker.publish() 异步方法完成。
    只需覆写 _publish_impl 适配 FastStream 的异步接口，
    日志、计数、AsyncResult 返回等由基类 _execute_publish 统一处理。
    """

    def custom_init(self):
        self.broker = get_broker()
        get_or_create_event_loop().run_until_complete(self.broker.connect())

    def _publish_impl(self, msg):
        get_or_create_event_loop().run_until_complete(
            self.broker.publish(Serialization.to_json_str(msg), self.queue_name))

    def clear(self):
        pass

    def get_message_count(self):
        return -1

    def close(self):
        pass
