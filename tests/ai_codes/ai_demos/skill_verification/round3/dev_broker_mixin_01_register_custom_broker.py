"""验证 developing-funboost-broker SKILL.md §register_custom_broker 示例 (43-91)"""
import os
import time
from collections import deque
from dataclasses import dataclass
from threading import Lock

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"dev_broker_mixin_01_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"dev_broker_mixin_01_std_{_ts}"

from funboost import register_custom_broker, boost, BoosterParams
from funboost.publishers.base_publisher import AbstractPublisher
from funboost.consumers.base_consumer import AbstractConsumer

_MQ_STORE = {}
_MQ_LOCK = Lock()


@dataclass
class _RawMsg:
    body: str

    def ack(self):
        pass


class _MockMqClient:
    def __init__(self):
        self._queues = {}

    def _q(self, name):
        with _MQ_LOCK:
            if name not in self._queues:
                self._queues[name] = deque()
            return self._queues[name]

    def send(self, queue_name, msg):
        self._q(queue_name).append(msg)

    def receive(self, queue_name, timeout=5):
        import time as _t

        deadline = _t.time() + timeout
        while _t.time() < deadline:
            q = self._q(queue_name)
            if q:
                return _RawMsg(body=q.popleft())
            _t.sleep(0.05)
        return None

    def purge(self, queue_name):
        self._q(queue_name).clear()

    def queue_length(self, queue_name):
        return len(self._q(queue_name))

    def close(self):
        pass


_SHARED_MQ_CLIENT = _MockMqClient()


def connect_to_my_mq():
    return _SHARED_MQ_CLIENT


class MyPublisher(AbstractPublisher):
    def custom_init(self):
        super().custom_init()
        self._client = connect_to_my_mq()

    def _publish_impl(self, msg: str):
        self._client.send(self.queue_name, msg)

    def clear(self):
        self._client.purge(self.queue_name)

    def get_message_count(self):
        return self._client.queue_length(self.queue_name)

    def close(self):
        self._client.close()


class MyConsumer(AbstractConsumer):
    def custom_init(self):
        super().custom_init()
        self._client = connect_to_my_mq()

    def _dispatch_task(self):
        while True:
            msg = self._client.receive(self.queue_name, timeout=5)
            if msg:
                kw = {"body": msg.body, "raw_msg": msg}
                self._submit_task(kw)
                return

    def _confirm_consume(self, kw):
        kw["raw_msg"].ack()

    def _requeue(self, kw):
        from funboost.core.serialization import Serialization

        self._client.send(self.queue_name, Serialization.to_json_str(kw["body"]))


_BROKER_KIND = f"MY_BROKER_R3_{_ts}"
register_custom_broker(_BROKER_KIND, MyPublisher, MyConsumer)

RESULTS = []


@boost(BoosterParams(
    queue_name=f"test_dev_broker_mixin_01_{_ts}",
    broker_kind=_BROKER_KIND,
    concurrent_num=1,
    is_send_consumer_heartbeat_to_redis=False,
    create_logger_file=False,
))
def my_task(x):
    RESULTS.append(x * 2)
    print(f"[OK] my_task({x}) -> {x * 2}")
    return x * 2


if __name__ == "__main__":
    print("[START] dev_broker_mixin_01_register_custom_broker")
    my_task.push(7)
    assert my_task.publisher.get_message_count() == 1, "发布后队列深度应为 1"
    my_task.consume()
    time.sleep(15)
    if RESULTS == [14]:
        print("[PASS] register_custom_broker 示例运行成功")
    else:
        print(f"[FAIL] 消费结果异常: {RESULTS!r}")
    os._exit(66)
