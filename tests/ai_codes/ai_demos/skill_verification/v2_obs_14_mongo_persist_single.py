"""验证 funboost-observability SKILL §5 单队列 MongoDB 持久化"""
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"v2_obs_14_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"v2_obs_14_std_{_ts}"

from funboost import boost, BoosterParams, BrokerEnum, FunctionResultStatusPersistanceConfig

@boost(BoosterParams(
    queue_name=f"v2_obs_persist_single_{_ts}",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    concurrent_num=2,
    function_result_status_persistance_conf=FunctionResultStatusPersistanceConfig(
        is_save_status=True,
        is_save_result=True,
        expire_seconds=7 * 24 * 3600,
    ),
))
def my_task(x):
    print(f"persist single: {x + 1}")
    return x + 1

if __name__ == "__main__":
    my_task.consume()
    my_task.push(5)
    time.sleep(15)
    os._exit(66)
