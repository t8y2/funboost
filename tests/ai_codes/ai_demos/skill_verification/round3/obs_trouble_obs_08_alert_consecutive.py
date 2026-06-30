"""验证 round3 / funboost-observability SKILL §3 AlertNotifier 连续失败策略"""
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"obs_trouble_obs_08_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"obs_trouble_obs_08_std_{_ts}"

from funboost import boost, BrokerEnum
from funboost.contrib.override_publisher_consumer_cls.alert_notifier_mixin import (
    AlertNotifierBoosterParams,
)

@boost(AlertNotifierBoosterParams(
    queue_name=f"obs_trouble_obs_alert_consec_{_ts}",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    concurrent_num=2,
    user_options={
        'alert_options': {
            'failure_threshold': 5,
            'alert_app': 'wechat',
            'webhook_url': 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=YOUR_KEY',
        },
    },
))
def my_task(x):
    print(f"alert consec task ok: {x}")
    return x * 2

if __name__ == "__main__":
    my_task.consume()
    for i in range(3):
        my_task.push(i)
    time.sleep(15)
    os._exit(66)
