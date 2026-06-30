"""验证 developing-funboost-broker SKILL.md §_dispatch_task 模式 A (143-149)"""
import os
import time
from collections import deque
from dataclasses import dataclass
from threading import Lock

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"v2_broker_03_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"v2_broker_03_std_{_ts}"

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

    def receive(self, timeout=5):
        import time as _t

        deadline = _t.time() + timeout
        while _t.time() < deadline:
            with _LOCK:
                q = _STORE.get(self.qname, deque())
                if q:
                    return _Msg(body=q.popleft())
            _t.sleep(0.05)
        return None


class PatAPublisher(AbstractPublisher):
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


class PatAConsumer(AbstractConsumer):
    def custom_init(self):
        super().custom_init()
        self._client = _Client(self.queue_name)

    def _dispatch_task(self):
        while True:
            msg = self._client.receive(timeout=5)
            if msg:
                self._submit_task({"body": msg.body, "raw_msg": msg})
                return

    def _confirm_consume(self, kw):
        pass

    def _requeue(self, kw):
        from funboost.core.serialization import Serialization

        body = kw["body"]
        if isinstance(body, dict):
            body = Serialization.to_json_str(body)
        with _LOCK:
            _STORE.setdefault(self.queue_name, deque()).append(body)


_KIND = f"PAT_A_V2_{_ts}"
register_custom_broker(_KIND, PatAPublisher, PatAConsumer)

DONE = []


@boost(BoosterParams(
    queue_name=f"pat_a_v2_{_ts}",
    broker_kind=_KIND,
    concurrent_num=1,
    create_logger_file=False,
    is_send_consumer_heartbeat_to_redis=False,
))
def task_a(x):
    DONE.append(x)
    print(f"[OK] pattern_a consumed {x}")


if __name__ == "__main__":
    print("[START] v2_broker_03_dispatch_pattern_a")
    task_a.push(1)
    task_a.consume()
    time.sleep(15)
    if DONE == [1]:
        print("[PASS] 模式 A (while True + receive) 运行成功")
    else:
        print(f"[FAIL] 消费异常: {DONE!r}")
    os._exit(66)
