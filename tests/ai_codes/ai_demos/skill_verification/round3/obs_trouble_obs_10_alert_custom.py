"""验证 round3 / funboost-observability SKILL §3 AlertNotifier 自定义告警渠道"""
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"obs_trouble_obs_10_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"obs_trouble_obs_10_std_{_ts}"

from funboost import boost, BoosterParams, BrokerEnum
from funboost.contrib.override_publisher_consumer_cls.alert_notifier_mixin import (
    AlertNotifierConsumerMixin,
)


def send_email(to, subject, body):
    print(f"[CUSTOM ALERT] to={to} subject={subject} body={body[:80]}")


class EmailAlertConsumer(AlertNotifierConsumerMixin):
    def custom_send_notification(self, message: str):
        send_email(to='ops@example.com', subject='任务告警', body=message)


@boost(BoosterParams(
    queue_name=f"obs_trouble_obs_alert_custom_{_ts}",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    consumer_override_cls=EmailAlertConsumer,
    concurrent_num=2,
    user_options={
        'alert_options': {
            'alert_app': 'custom',
            'failure_threshold': 3,
        },
    },
))
def my_task_custom(x):
    print(f"alert custom task: {x}")
    return x + 1

if __name__ == "__main__":
    assert issubclass(EmailAlertConsumer, AlertNotifierConsumerMixin)
    my_task_custom.consume()
    my_task_custom.push(1)
    time.sleep(15)
    os._exit(66)
