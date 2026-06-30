"""验证 funboost-observability SKILL §4 PeriodicQuota 固定窗口每日额度"""
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"v2_obs_12_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"v2_obs_12_std_{_ts}"

from funboost import boost, BrokerEnum
from funboost.contrib.override_publisher_consumer_cls.periodic_quota_mixin import (
    PeriodicQuotaBoosterParams,
)


def process(x):
    return x * 10


@boost(PeriodicQuotaBoosterParams(
    queue_name=f"v2_obs_quota_daily_{_ts}",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    user_options={
        'quota_limit': 30,
        'quota_period': 'd',
        'sliding_window': False,
    },
    qps=1 / 600,
    concurrent_num=2,
))
def daily_task(x):
    result = process(x)
    print(f"daily quota task: {x} -> {result}")
    return result

if __name__ == "__main__":
    daily_task.consume()
    daily_task.push(1)
    time.sleep(15)
    os._exit(66)
