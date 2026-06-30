"""验证 funboost-observability SKILL §6 组合多种 Mixin"""
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"v2_obs_17_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"v2_obs_17_std_{_ts}"

from funboost import boost, BoosterParams, BrokerEnum
from funboost.contrib.override_publisher_consumer_cls.funboost_promethus_mixin import (
    PrometheusConsumerMixin, PrometheusPublisherMixin, start_prometheus_http_server,
)
from funboost.contrib.override_publisher_consumer_cls.alert_notifier_mixin import AlertNotifierConsumerMixin


class ObservabilityMixin(PrometheusConsumerMixin, AlertNotifierConsumerMixin):
    """Prometheus 指标 + 失败告警"""
    pass


def process(x):
    return x * 3


start_prometheus_http_server(port=18017)

@boost(BoosterParams(
    queue_name=f"v2_obs_combined_{_ts}",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    consumer_override_cls=ObservabilityMixin,
    publisher_override_cls=PrometheusPublisherMixin,
    concurrent_num=2,
    user_options={
        'alert_options': {
            'failure_threshold': 5,
            'alert_app': 'wechat',
            'webhook_url': 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=YOUR_KEY',
        },
    },
))
def observable_task(x):
    result = process(x)
    print(f"observable_task: {x} -> {result}")
    return result

if __name__ == "__main__":
    mro_names = [c.__name__ for c in ObservabilityMixin.__mro__]
    assert 'PrometheusConsumerMixin' in mro_names
    assert 'AlertNotifierConsumerMixin' in mro_names
    print(f"[OK] ObservabilityMixin MRO: {mro_names[:5]}")
    observable_task.consume()
    observable_task.push(2)
    time.sleep(15)
    os._exit(66)
