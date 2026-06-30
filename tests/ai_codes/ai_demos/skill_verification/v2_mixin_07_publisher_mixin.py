"""验证 developing-funboost-mixin SKILL.md §Publisher Mixin 示例 (253-266)"""
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"v2_mixin_07_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"v2_mixin_07_std_{_ts}"

from funboost import boost, BoosterParams, BrokerEnum
from funboost.publishers.base_publisher import AbstractPublisher

PUBLISH_LOG = {"logged": 0, "metrics": 0}


class MyPublisherMixin(AbstractPublisher):

    def _log_publish(self, msg):
        PUBLISH_LOG["logged"] += 1
        print(f"[LOG] publish msg len={len(msg)}")

    def _record_publish_metric(self):
        PUBLISH_LOG["metrics"] += 1

    def _publish_impl(self, msg: str):
        """拦截发布，添加日志/指标"""
        self._log_publish(msg)
        super()._publish_impl(msg)

    def _after_publish(self, publish_msg_context):
        super()._after_publish(publish_msg_context)
        self._record_publish_metric()


@boost(BoosterParams(
    queue_name=f"pub_mixin_v2_{_ts}",
    broker_kind=BrokerEnum.SQLITE_QUEUE,
    publisher_override_cls=MyPublisherMixin,
    concurrent_num=1,
    create_logger_file=False,
    is_send_consumer_heartbeat_to_redis=False,
))
def pub_task(x):
    print(f"[OK] pub_task consumed x={x}")
    return x


if __name__ == "__main__":
    print("[START] v2_mixin_07_publisher_mixin")
    pub_task.push(3)
    pub_task.consume()
    time.sleep(15)
    if PUBLISH_LOG["logged"] >= 1 and PUBLISH_LOG["metrics"] >= 1:
        print(f"[PASS] MyPublisherMixin 发布拦截正常: {PUBLISH_LOG}")
    else:
        print(f"[FAIL] PUBLISH_LOG={PUBLISH_LOG!r}")
    os._exit(66)
