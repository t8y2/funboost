"""验证 round3 / funboost-observability SKILL §1 手动指定 Prometheus Mixin"""
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"obs_trouble_obs_04_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"obs_trouble_obs_04_std_{_ts}"

from funboost import boost, BoosterParams, BrokerEnum
from funboost.contrib.override_publisher_consumer_cls.funboost_promethus_mixin import (
    PrometheusConsumerMixin,
    PrometheusPublisherMixin,
    start_prometheus_http_server,
)

start_prometheus_http_server(port=18304)

@boost(BoosterParams(
    queue_name=f"obs_trouble_obs_prom_manual_{_ts}",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    consumer_override_cls=PrometheusConsumerMixin,
    publisher_override_cls=PrometheusPublisherMixin,
    concurrent_num=2,
))
def my_task(x):
    print(f"prom manual mixin: {x * 2}")
    return x * 2

if __name__ == "__main__":
    my_task.consume()
    my_task.push(3)
    time.sleep(15)
    os._exit(66)
