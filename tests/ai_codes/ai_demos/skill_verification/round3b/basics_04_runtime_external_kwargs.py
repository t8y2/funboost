"""round3b: using-funboost-basics — should_check_publish_func_params + **kwargs"""
import os
import time

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
_ts = int(time.time())
os.environ["PRINT_WRTIE_FILE_NAME"] = f"r3b_basics_04_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"r3b_basics_04_std_{_ts}"

from funboost import boost, BoosterParams, BrokerEnum

RECEIVED = {}


@boost(BoosterParams(
    queue_name="external_queue_r3b",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    should_check_publish_func_params=False,
))
def handle_external(**kwargs):
    RECEIVED.update(kwargs)
    print(f"[OK] handle_external kwargs={kwargs}")
    return kwargs


if __name__ == "__main__":
    handle_external.publish({"foo": "bar", "n": 42})
    handle_external.consume()
    time.sleep(12)
    ok = RECEIVED == {"foo": "bar", "n": 42}
    print(f"[{'PASS' if ok else 'FAIL'}] external kwargs: {RECEIVED}")
    import os
    os._exit(66 if ok else 1)
