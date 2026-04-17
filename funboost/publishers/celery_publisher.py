# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 12:12
import os
import sys
import time

import celery
import celery.result

from funboost.assist.celery_helper import celery_app
from funboost.publishers.base_publisher import AbstractPublisher, PublishMsgContext


class CeleryPublisher(AbstractPublisher):
    """
    使用 celery 作为中间件。

    Celery 的发布走 celery_app.send_task()，不走普通的 _publish_impl，
    因此覆写 _execute_publish 而非 _publish_impl。
    publish() / push() / delay() 均走基类流程，最终进入 _execute_publish。
    返回值为 celery.result.AsyncResult，可直接 .get() 获取远端结果。
    """

    def _execute_publish(self, publish_msg_context: PublishMsgContext) -> celery.result.AsyncResult:
        t_start = time.time()
        celery_result = celery_app.send_task(
            name=self.queue_name,
            kwargs=publish_msg_context.msg_function_kw,
            task_id=publish_msg_context.task_id,
        )
        self._post_publish_log_and_count(t_start, publish_msg_context)
        return celery_result

    def _publish_impl(self, msg):
        pass

    def clear(self):
        python_executable = sys.executable
        cmd = f''' {python_executable} -m celery -A funboost.publishers.celery_publisher purge -Q {self.queue_name} -f'''
        self.logger.warning(f'刪除celery {self.queue_name} 隊列中的消息  {cmd}')
        os.system(cmd)

    def get_message_count(self):
        with celery_app.connection_or_acquire() as conn:
            msg_cnt = conn.default_channel.queue_declare(
                queue=self.queue_name, passive=False, durable=True, auto_delete=False).message_count
        return msg_cnt

    def close(self):
        pass
