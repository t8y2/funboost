"""验证 funboost-observability SKILL §5 MongoAlertMonitor"""
import os
import time
import threading

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"v2_obs_16_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"v2_obs_16_std_{_ts}"

from funboost import boost, BoosterParams, BrokerEnum, FunctionResultStatusPersistanceConfig
from funboost.core.mongo_alert_monitor import MongoAlertMonitor


@boost(BoosterParams(
    queue_name=f"v2_obs_monitor_task_{_ts}",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    concurrent_num=2,
    function_result_status_persistance_conf=FunctionResultStatusPersistanceConfig(
        is_save_status=True,
    ),
))
def my_task(x):
    print(f"monitor task: {x}")
    return x + 1


@boost(BoosterParams(
    queue_name=f"v2_obs_monitor_a_{_ts}",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    concurrent_num=2,
    function_result_status_persistance_conf=FunctionResultStatusPersistanceConfig(
        is_save_status=True,
    ),
))
def task_a(x):
    return x


if __name__ == "__main__":
    monitor = MongoAlertMonitor(
        boosters=[my_task, task_a],
        alert_app='wechat',
        webhook_url='https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=YOUR_KEY',
        window_seconds=60,
        failure_count=10,
        poll_interval=10,
        alert_interval=300,
    )
    print(f"[OK] MongoAlertMonitor 实例化成功: {monitor}")

    my_task.consume()
    task_a.consume()
    my_task.push(1)
    task_a.push(2)

    # 不调用 monitor.start()（永久阻塞），仅验证构造与 boosters 绑定
    time.sleep(15)
    os._exit(66)
