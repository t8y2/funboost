"""验证 SKILL: developing-funboost-testing — 测试 Mixin"""
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"test_mixin_run1_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"test_mixin_std1_{_ts}"

from funboost import boost, BoosterParams, BrokerEnum
from funboost.consumers.base_consumer import AbstractConsumer


class CounterMixin(AbstractConsumer):
    def custom_init(self):
        super().custom_init()
        self._success_count = 0
        self._fail_count = 0

    def _both_sync_and_aio_frame_custom_record_process_info_func(self, status, kw):
        super()._both_sync_and_aio_frame_custom_record_process_info_func(status, kw)
        if status.success:
            self._success_count += 1
        else:
            self._fail_count += 1
        print(f"[COUNTER] success={self._success_count}, fail={self._fail_count}")


@boost(
    BoosterParams(
        queue_name=f"test_counter_mixin_{_ts}",
        broker_kind=BrokerEnum.SQLITE_QUEUE,
        consumer_override_cls=CounterMixin,
        concurrent_num=2,
        qps=5,
    )
)
def counted_task(x: int):
    if x % 3 == 0:
        raise ValueError(f"模拟失败 {x}")
    return x * 2


if __name__ == "__main__":
    for i in range(10):
        counted_task.push(i)

    counted_task.consume()
    time.sleep(15)
    os._exit(66)
