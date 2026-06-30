"""验证 round3 / funboost-observability SKILL §4 PeriodicQuota 滑动窗口"""
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"obs_trouble_obs_11_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"obs_trouble_obs_11_std_{_ts}"

from funboost import boost, BoosterParams, BrokerEnum
from funboost.contrib.override_publisher_consumer_cls.periodic_quota_mixin import (
    PeriodicQuotaConsumerMixin,
)

@boost(BoosterParams(
    queue_name=f"obs_trouble_obs_quota_slide_{_ts}",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    consumer_override_cls=PeriodicQuotaConsumerMixin,
    user_options={
        'quota_limit': 6,
        'quota_period': 'm',
        'sliding_window': True,
    },
    qps=1,
    concurrent_num=2,
))
def my_task(x):
    print(f'Processing {x}')

if __name__ == "__main__":
    my_task.consume()
    for i in range(2):
        my_task.push(i)
    time.sleep(15)
    os._exit(66)
