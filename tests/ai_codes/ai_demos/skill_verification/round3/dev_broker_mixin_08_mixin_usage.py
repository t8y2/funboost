"""验证 developing-funboost-mixin SKILL.md §使用方式 (80-95)"""
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"dev_broker_mixin_08_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"dev_broker_mixin_08_std_{_ts}"

from funboost import boost, BoosterParams, BrokerEnum
from funboost.consumers.base_consumer import AbstractConsumer

RESULTS = []


class MyConsumerMixin(AbstractConsumer):
    def custom_init(self):
        super().custom_init()
        opts = self.consumer_params.user_options.get("my_mixin_options", {})
        self._threshold = opts.get("threshold", 10)

    def _submit_task(self, kw):
        super()._submit_task(kw)


@boost(BoosterParams(
    queue_name=f"monitored_task_r3_{_ts}",
    broker_kind=BrokerEnum.SQLITE_QUEUE,
    consumer_override_cls=MyConsumerMixin,
    user_options={
        "my_mixin_options": {
            "threshold": 100,
        }
    },
    concurrent_num=1,
    create_logger_file=False,
    is_send_consumer_heartbeat_to_redis=False,
))
def my_task(x):
    RESULTS.append(x * 2)
    print(f"[OK] my_task({x}) -> {x * 2}")
    return x * 2


if __name__ == "__main__":
    print("[START] dev_broker_mixin_08_mixin_usage")
    my_task.push(11)
    my_task.consume()
    time.sleep(15)
    if RESULTS == [22]:
        print("[PASS] @boost + consumer_override_cls + user_options 示例运行成功")
    else:
        print(f"[FAIL] RESULTS={RESULTS!r}")
    os._exit(66)
