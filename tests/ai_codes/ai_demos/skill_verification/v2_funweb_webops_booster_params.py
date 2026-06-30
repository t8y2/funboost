"""验证 skill: funboost-funweb-ops §3 WebOpsBoosterParams 配置示例"""
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"v2_funweb_booster_params_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"v2_funweb_booster_params_std_{_ts}"

from funboost import BoosterParams, FunctionResultStatusPersistanceConfig, BrokerEnum


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


if __name__ == "__main__":
    bp = WebOpsBoosterParams(queue_name=f"webops_v2_{_ts}")
    assert bp.project_name == "my_project"
    assert bp.is_send_consumer_heartbeat_to_redis is True
    assert bp.is_using_rpc_mode is True
    assert bp.function_result_status_persistance_conf.is_save_result is True
    print("[PASS] WebOpsBoosterParams")
    time.sleep(15)
    os._exit(66)
