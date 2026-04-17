# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2023/8/6 0006 12:12
import time

from nameko.standalone.rpc import ClusterRpcProxy

from funboost.funboost_config_deafult import BrokerConnConfig
from funboost.publishers.base_publisher import AbstractPublisher, PublishMsgContext


def get_nameko_config():
    return {'AMQP_URI': f'amqp://{BrokerConnConfig.RABBITMQ_USER}:{BrokerConnConfig.RABBITMQ_PASS}@{BrokerConnConfig.RABBITMQ_HOST}:{BrokerConnConfig.RABBITMQ_PORT}/{BrokerConnConfig.RABBITMQ_VIRTUAL_HOST}'}


class NamekoPublisher(AbstractPublisher):
    """
    使用 nameko 作为中间件（同步 RPC 调用模式）。

    Nameko 的发布是同步 RPC，通过 ClusterRpcProxy 调用远端 service 的 call 方法。
    覆写 _execute_publish 以返回 nameko RPC 调用结果而非 funboost AsyncResult。
    publish() / push() / delay() 均走基类流程，最终进入 _execute_publish。
    """

    def custom_init(self):
        self._rpc = ClusterRpcProxy(get_nameko_config())

    def _execute_publish(self, publish_msg_context: PublishMsgContext):
        t_start = time.time()
        with self._rpc as rpc:
            res = getattr(rpc, self.queue_name).call(**publish_msg_context.msg_function_kw)
        self._post_publish_log_and_count(t_start, publish_msg_context)
        return res

    def _publish_impl(self, msg):
        pass

    def clear(self):
        self.logger.warning('還沒開始實現')

    def get_message_count(self):
        return -1

    def close(self):
        pass
