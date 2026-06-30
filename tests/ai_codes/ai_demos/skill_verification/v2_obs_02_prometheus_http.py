"""验证 funboost-observability SKILL §1 Prometheus HTTP Server 模式"""
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"v2_obs_02_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"v2_obs_02_std_{_ts}"

from funboost import boost, BrokerEnum
from funboost.contrib.override_publisher_consumer_cls.funboost_promethus_mixin import (
    PrometheusBoosterParams,
    start_prometheus_http_server,
)

start_prometheus_http_server(port=18002)

@boost(PrometheusBoosterParams(
    queue_name=f"v2_obs_prom_http_{_ts}",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    concurrent_num=2,
))
def my_task(x):
    print(f"prom http task: {x} -> {x * 2}")
    return x * 2

if __name__ == "__main__":
    my_task.consume()
    my_task.push(10)
    time.sleep(15)
    os._exit(66)
