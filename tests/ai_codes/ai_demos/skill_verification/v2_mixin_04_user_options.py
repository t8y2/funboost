"""验证 developing-funboost-mixin SKILL.md §配置规范 user_options (185-195)"""
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"v2_mixin_04_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"v2_mixin_04_std_{_ts}"

from funboost import boost, BoosterParams, BrokerEnum
from funboost.consumers.base_consumer import AbstractConsumer

READ_OPTIONS = {}


class OptionsReaderMixin(AbstractConsumer):
    def custom_init(self):
        super().custom_init()
        uo = self.consumer_params.user_options
        READ_OPTIONS["circuit_breaker"] = uo.get("circuit_breaker_options", {})
        READ_OPTIONS["custom"] = uo.get("my_custom_mixin_options", {})


@boost(BoosterParams(
    queue_name=f"user_options_v2_{_ts}",
    broker_kind=BrokerEnum.SQLITE_QUEUE,
    consumer_override_cls=OptionsReaderMixin,
    user_options={
        "circuit_breaker_options": {
            "failure_threshold": 5,
            "recovery_timeout": 60,
        },
        "my_custom_mixin_options": {
            "my_key": "my_value",
        },
    },
    concurrent_num=1,
    create_logger_file=False,
    is_send_consumer_heartbeat_to_redis=False,
))
def opts_task(x):
    print(f"[OK] opts_task x={x}")


if __name__ == "__main__":
    print("[START] v2_mixin_04_user_options")
    opts_task.push(1)
    opts_task.consume()
    time.sleep(15)
    expected_cb = {"failure_threshold": 5, "recovery_timeout": 60}
    expected_custom = {"my_key": "my_value"}
    if READ_OPTIONS.get("circuit_breaker") == expected_cb and READ_OPTIONS.get("custom") == expected_custom:
        print("[PASS] user_options 嵌套命名空间配置读取正确")
    else:
        print(f"[FAIL] READ_OPTIONS={READ_OPTIONS!r}")
    os._exit(66)
