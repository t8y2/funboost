"""验证 skill: funboost-funweb-ops §4 多进程消费示例（import + 装饰器，不启动 web/consume）"""
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"mem_funweb_13_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"mem_funweb_13_std_{_ts}"

from funboost import boost, BoosterParams, BrokerEnum, FunctionResultStatusPersistanceConfig, enable_ctrl_c_quit_on_windows
from funboost.funweb.app import start_funboost_web_manager


class WebOpsBoosterParams(BoosterParams):
    project_name: str = "my_project"
    broker_kind: str = BrokerEnum.REDIS_ACK_ABLE
    is_send_consumer_heartbeat_to_redis: bool = True
    is_using_rpc_mode: bool = True
    function_result_status_persistance_conf: FunctionResultStatusPersistanceConfig = (
        FunctionResultStatusPersistanceConfig(
            is_save_result=True,
            is_save_status=True,
            expire_seconds=7 * 24 * 3600,
        )
    )


@boost(WebOpsBoosterParams(queue_name=f"worker_queue_r3_{_ts}", qps=2, concurrent_num=10))
def process_task(x):
    return x * 2


if __name__ == "__main__":
    assert callable(start_funboost_web_manager)
    assert callable(process_task.multi_process_consume)
    assert callable(process_task.push)
    assert callable(enable_ctrl_c_quit_on_windows)
    assert process_task.boost_params.is_send_consumer_heartbeat_to_redis is True
    print("[PASS] multi consumer example imports & decorator")
    time.sleep(15)
    os._exit(66)
