"""round3b 验证：_submit_task(kw) 中 kw['body'] 必须是 JSON 字符串"""
import os
import time
from collections import deque
from threading import Lock

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"r2_dev_test_03_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"r2_dev_test_03_std_{_ts}"

from funboost import register_custom_broker, boost, BoosterParams
from funboost.publishers.base_publisher import AbstractPublisher
from funboost.consumers.base_consumer import AbstractConsumer
from funboost.core.serialization import Serialization

_STORE = {}
_LOCK = Lock()
KW_CAPTURE = []


class KwPublisher(AbstractPublisher):
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


class KwConsumer(AbstractConsumer):
    def _dispatch_task(self):
        with _LOCK:
            q = _STORE.get(self.queue_name, deque())
            if not q:
                return
            json_str = q.popleft()
        kw = {"body": json_str}
        KW_CAPTURE.append({"body_type": type(kw["body"]).__name__, "is_str": isinstance(kw["body"], str)})
        self._submit_task(kw)

    def _confirm_consume(self, kw):
        pass

    def _requeue(self, kw):
        with _LOCK:
            body = kw["body"]
            if isinstance(body, dict):
                body = Serialization.to_json_str(body)
            _STORE.setdefault(self.queue_name, deque()).append(body)


_KIND = f"KW_R2B_{_ts}"
register_custom_broker(_KIND, KwPublisher, KwConsumer)

RESULT = []


@boost(BoosterParams(
    queue_name=f"kw_r2b_{_ts}",
    broker_kind=_KIND,
    concurrent_num=1,
    create_logger_file=False,
    is_send_consumer_heartbeat_to_redis=False,
))
def kw_task(n):
    RESULT.append(n)
    print(f"[OK] kw_task n={n}")


if __name__ == "__main__":
    print("[START] r2_dev_test_03_kw_body_format")
    kw_task.push(42)
    kw_task.consume()
    time.sleep(15)
    ok = (
        len(KW_CAPTURE) == 1
        and KW_CAPTURE[0]["body_type"] == "str"
        and KW_CAPTURE[0]["is_str"] is True
        and RESULT == [42]
    )
    if ok:
        print("[PASS] kw={'body': json_str} 格式正确且消费成功")
    else:
        print(f"[FAIL] KW_CAPTURE={KW_CAPTURE!r}, RESULT={RESULT!r}")
    os._exit(66)
