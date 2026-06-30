"""验证 round3 / funboost-observability SKILL §1 Prometheus Push Gateway 模式"""
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"obs_trouble_obs_03_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"obs_trouble_obs_03_std_{_ts}"

from funboost import boost, BrokerEnum
from funboost.contrib.override_publisher_consumer_cls.funboost_promethus_mixin import (
    PrometheusPushGatewayBoosterParams,
)

@boost(PrometheusPushGatewayBoosterParams(
    queue_name=f"obs_trouble_obs_prom_push_{_ts}",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    concurrent_num=2,
    user_options={
        'prometheus_pushgateway_url': 'localhost:9091',
        'prometheus_push_interval': 10.0,
        'prometheus_job_name': 'my_app',
    },
))
def my_task_mp(x):
    print(f"prom push task: {x} -> {x * 2}")
    return x * 2

if __name__ == "__main__":
    my_task_mp.consume()
    my_task_mp.push(5)
    time.sleep(15)
    os._exit(66)
