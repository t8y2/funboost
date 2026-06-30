"""验证 developing-funboost-broker SKILL.md §override_cls 示例 (96-116)"""
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"v2_broker_02_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"v2_broker_02_std_{_ts}"

from funboost import boost, BoosterParams, BrokerEnum

HOOK_LOG = []


class MyConsumerMixin:
    """Mixin 混入到任意 broker 的 consumer 中"""

    def _submit_task(self, kw):
        self._pre_check(kw)
        super()._submit_task(kw)

    def _pre_check(self, kw):
        HOOK_LOG.append("pre_check")
        pass


@boost(BoosterParams(
    queue_name=f"custom_task_v2_{_ts}",
    broker_kind=BrokerEnum.SQLITE_QUEUE,
    consumer_override_cls=MyConsumerMixin,
    concurrent_num=1,
    create_logger_file=False,
    is_send_consumer_heartbeat_to_redis=False,
))
def my_task(x):
    print(f"[OK] my_task x={x}")
    return x


if __name__ == "__main__":
    print("[START] v2_broker_02_override_cls_mixin")
    my_task.push(42)
    my_task.consume()
    time.sleep(15)
    if "pre_check" in HOOK_LOG:
        print("[PASS] MyConsumerMixin._pre_check 被调用")
    else:
        print(f"[FAIL] _pre_check 未触发, HOOK_LOG={HOOK_LOG!r}")
    os._exit(66)
