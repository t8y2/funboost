"""round3b 验证：register_custom_broker 函数签名与 SKILL 文档一致"""
import inspect
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"r2_dev_test_01_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"r2_dev_test_01_std_{_ts}"

from funboost.factories.broker_kind__publsiher_consumer_type_map import register_custom_broker
from funboost.publishers.base_publisher import AbstractPublisher
from funboost.consumers.base_consumer import AbstractConsumer

EXPECTED_PARAMS = ["broker_kind", "publisher_class", "consumer_class"]
sig = inspect.signature(register_custom_broker)
actual_params = list(sig.parameters.keys())

checks = []
checks.append(("param_count", len(actual_params) == 3, f"expected 3, got {len(actual_params)}: {actual_params}"))
checks.append(("param_names", actual_params == EXPECTED_PARAMS, f"expected {EXPECTED_PARAMS}, got {actual_params}"))

hints = sig.parameters["publisher_class"].annotation
hint_ok = "AbstractPublisher" in str(hints)
checks.append(("publisher_class_annotation", hint_ok, f"annotation={hints!r}"))

hints2 = sig.parameters["consumer_class"].annotation
hint2_ok = "AbstractConsumer" in str(hints2)
checks.append(("consumer_class_annotation", hint2_ok, f"annotation={hints2!r}"))

# SKILL 示例调用形式：register_custom_broker("MY_BROKER", MyPublisher, MyConsumer)
from collections import deque
from threading import Lock

_STORE = {}
_LOCK = Lock()


class _SigPub(AbstractPublisher):
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


class _SigCon(AbstractConsumer):
    def _dispatch_task(self):
        with _LOCK:
            q = _STORE.get(self.queue_name, deque())
            if q:
                self._submit_task({"body": q.popleft()})

    def _confirm_consume(self, kw):
        pass

    def _requeue(self, kw):
        pass


_KIND = f"SIG_R2_{_ts}"
try:
    register_custom_broker(_KIND, _SigPub, _SigCon)
    checks.append(("callable_example", True, "register_custom_broker(str, Pub, Con) 调用成功"))
except Exception as e:
    checks.append(("callable_example", False, str(e)))

if __name__ == "__main__":
    print("[START] r2_dev_test_01_register_custom_broker_signature")
    all_ok = True
    for name, ok, detail in checks:
        tag = "PASS" if ok else "FAIL"
        print(f"[{tag}] {name}: {detail}")
        all_ok = all_ok and ok
    if all_ok:
        print("[PASS] register_custom_broker 签名与 SKILL 一致")
    else:
        print("[FAIL] register_custom_broker 签名验证失败")
    time.sleep(15)
    os._exit(66)
