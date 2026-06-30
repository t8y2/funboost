"""验证 developing-funboost-broker SKILL.md §_dispatch_task 模式 B (153-158)"""
import os
import time
from collections import deque
from dataclasses import dataclass
from threading import Lock

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"dev_broker_mixin_04_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"dev_broker_mixin_04_std_{_ts}"

from funboost import register_custom_broker, boost, BoosterParams
from funboost.publishers.base_publisher import AbstractPublisher
from funboost.consumers.base_consumer import AbstractConsumer

_STORE = {}
_LOCK = Lock()


@dataclass
class _Msg:
    body: str


class _Client:
    def __init__(self, qname):
        self.qname = qname

    def poll(self, timeout=0.5):
        with _LOCK:
            q = _STORE.get(self.qname, deque())
            if q:
                return _Msg(body=q.popleft())
        return None


class PatBPublisher(AbstractPublisher):
    def _publish_impl(self, msg: str):
        with _LOCK:
            _STORE.setdefault(self.queue_name, deque()).append(msg)

    def clear(self):
        with _LOCK:
            _STORE[self.queue_name] = deque()

    def get_message_count(self):
        with _LOCK:
            return len(_STORE.get(self.queue_name, deque()))

    def close(self):
        pass


class PatBConsumer(AbstractConsumer):
    def custom_init(self):
        super().custom_init()
        self._client = _Client(self.queue_name)

    def _dispatch_task(self):
        msg = self._client.poll(timeout=0.5)
        if msg:
            self._submit_task({"body": msg.body})

    def _confirm_consume(self, kw):
        pass

    def _requeue(self, kw):
        from funboost.core.serialization import Serialization

        body = kw["body"]
        if isinstance(body, dict):
            body = Serialization.to_json_str(body)
        with _LOCK:
            _STORE.setdefault(self.queue_name, deque()).append(body)


_KIND = f"PAT_B_R3_{_ts}"
register_custom_broker(_KIND, PatBPublisher, PatBConsumer)

DONE = []


@boost(BoosterParams(
    queue_name=f"pat_b_r3_{_ts}",
    broker_kind=_KIND,
    concurrent_num=1,
    create_logger_file=False,
    is_send_consumer_heartbeat_to_redis=False,
))
def task_b(x):
    DONE.append(x)
    print(f"[OK] pattern_b consumed {x}")


if __name__ == "__main__":
    print("[START] dev_broker_mixin_04_dispatch_pattern_b")
    task_b.push(2)
    task_b.push(3)
    task_b.consume()
    time.sleep(15)
    if sorted(DONE) == [2, 3]:
        print("[PASS] 模式 B (单次 poll) 运行成功")
    else:
        print(f"[FAIL] 消费异常: {DONE!r}")
    os._exit(66)
