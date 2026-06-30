"""验证 funboost-observability SKILL §5 多队列共享 MongoDB 集合"""
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"v2_obs_15_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"v2_obs_15_std_{_ts}"

from funboost import boost, BoosterParams, BrokerEnum, FunctionResultStatusPersistanceConfig


class PersistBoosterParams(BoosterParams):
    function_result_status_persistance_conf = FunctionResultStatusPersistanceConfig(
        is_save_status=True,
        is_save_result=True,
        expire_seconds=17 * 24 * 3600,
        table_name=f'v2_obs_project_all_tasks_{_ts}',
        is_use_bulk_insert=True,
    )

@boost(PersistBoosterParams(queue_name=f"v2_obs_queue_a_{_ts}", broker_kind=BrokerEnum.MEMORY_QUEUE, concurrent_num=2))
def task_a(x):
    print(f"task_a: {x}")
    return x

@boost(PersistBoosterParams(queue_name=f"v2_obs_queue_b_{_ts}", broker_kind=BrokerEnum.MEMORY_QUEUE, concurrent_num=2))
def task_b(x):
    print(f"task_b: {x}")
    return x

if __name__ == "__main__":
    task_a.consume()
    task_b.consume()
    task_a.push(1)
    task_b.push(2)
    time.sleep(15)
    os._exit(66)
