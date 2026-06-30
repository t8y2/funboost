"""验证 funboost-observability SKILL §3 AlertNotifier 错误率策略"""
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"v2_obs_09_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"v2_obs_09_std_{_ts}"

from funboost import boost, BoosterParams, BrokerEnum
from funboost.contrib.override_publisher_consumer_cls.alert_notifier_mixin import (
    AlertNotifierConsumerMixin,
)

@boost(BoosterParams(
    queue_name=f"v2_obs_alert_rate_{_ts}",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    consumer_override_cls=AlertNotifierConsumerMixin,
    concurrent_num=2,
    user_options={
        'alert_options': {
            'strategy': 'rate',
            'errors_rate': 0.5,
            'period': 60,
            'min_calls': 10,
            'alert_app': 'dingtalk',
            'webhook_url': 'https://oapi.dingtalk.com/robot/send?access_token=YOUR_TOKEN',
            'alert_interval': 600,
        },
    },
))
def my_task_rate(x):
    print(f"alert rate task ok: {x}")
    return x * 2

if __name__ == "__main__":
    my_task_rate.consume()
    for i in range(3):
        my_task_rate.push(i)
    time.sleep(15)
    os._exit(66)
