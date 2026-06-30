"""验证 developing-funboost-broker SKILL.md §broker_exclusive_config (191-207)"""
import os
import time
from collections import deque
from threading import Lock

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"v2_broker_06_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"v2_broker_06_std_{_ts}"

from funboost import register_custom_broker, boost, BoosterParams, register_broker_exclusive_config_default
from funboost.publishers.base_publisher import AbstractPublisher
from funboost.consumers.base_consumer import AbstractConsumer

_STORE = {}
_LOCK = Lock()
CONFIG_LOG = {"publisher": None, "consumer": None}

_BROKER = f"MY_BROKER_CFG_V2_{_ts}"

register_broker_exclusive_config_default(_BROKER, {
    "my_key": "default_value",
})


class CfgPublisher(AbstractPublisher):
    def custom_init(self):
        super().custom_init()
        value = self.publisher_params.broker_exclusive_config["my_key"]
        CONFIG_LOG["publisher"] = value

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


class CfgConsumer(AbstractConsumer):
    def custom_init(self):
        super().custom_init()
        value = self.consumer_params.broker_exclusive_config["my_key"]
        CONFIG_LOG["consumer"] = value

    def _dispatch_task(self):
        with _LOCK:
            q = _STORE.get(self.queue_name, deque())
            if q:
                self._submit_task({"body": q.popleft()})

    def _confirm_consume(self, kw):
        pass

    def _requeue(self, kw):
        from funboost.core.serialization import Serialization

        body = kw["body"]
        if isinstance(body, dict):
            body = Serialization.to_json_str(body)
        with _LOCK:
            _STORE.setdefault(self.queue_name, deque()).append(body)


register_custom_broker(_BROKER, CfgPublisher, CfgConsumer)


@boost(BoosterParams(
    queue_name=f"cfg_v2_{_ts}",
    broker_kind=_BROKER,
    concurrent_num=1,
    create_logger_file=False,
    is_send_consumer_heartbeat_to_redis=False,
))
def cfg_task(x):
    print(f"[OK] cfg_task x={x}")


if __name__ == "__main__":
    print("[START] v2_broker_06_exclusive_config")
    cfg_task.push(1)
    cfg_task.consume()
    time.sleep(15)
    if CONFIG_LOG == {"publisher": "default_value", "consumer": "default_value"}:
        print("[PASS] broker_exclusive_config['my_key'] 读写正确")
    else:
        print(f"[FAIL] CONFIG_LOG={CONFIG_LOG!r}")
    os._exit(66)
