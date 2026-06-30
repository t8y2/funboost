"""验证 skill: funboost-funweb-ops §6 完整代码示例（import + 类/装饰器定义，不启动 web/consume）"""
import asyncio
import os
import random
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"v2_funweb_full_example_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"v2_funweb_full_example_std_{_ts}"

from funboost import (
    boost,
    BoosterParams,
    BrokerEnum,
    ConcurrentModeEnum,
    FunctionResultStatusPersistanceConfig,
    enable_ctrl_c_quit_on_windows,
)
from funboost.funweb.app import start_funboost_web_manager


class MyBoosterParams(BoosterParams):
    project_name: str = "test_project1"
    broker_kind: str = BrokerEnum.REDIS_ACK_ABLE
    is_send_consumer_heartbeat_to_redis: bool = True
    is_using_rpc_mode: bool = True
    booster_group: str = "test_group1"
    function_result_status_persistance_conf: FunctionResultStatusPersistanceConfig = (
        FunctionResultStatusPersistanceConfig(
            is_save_result=True,
            is_save_status=True,
            expire_seconds=7 * 24 * 3600,
        )
    )


@boost(MyBoosterParams(queue_name=f"queue_test_g01t_v2_{_ts}", qps=1))
def f(x):
    time.sleep(0.01)
    if random.random() > 0.9:
        raise ValueError("f error")
    return x + 1


@boost(MyBoosterParams(queue_name=f"queue_test_g02t_v2_{_ts}", qps=0.5, max_retry_times=0))
def f2(x, y):
    time.sleep(0.01)
    if random.random() > 0.5:
        raise ValueError("f2 error")
    return x + y


@boost(MyBoosterParams(
    queue_name=f"queue_test_g03t_v2_{_ts}",
    qps=0.5,
    max_retry_times=0,
    concurrent_mode=ConcurrentModeEnum.ASYNC,
))
async def aio_f3(x):
    await asyncio.sleep(0.01)
    if random.random() > 0.5:
        raise ValueError("f3 error")
    return x + 1


if __name__ == "__main__":
    assert callable(start_funboost_web_manager)
    assert callable(f.multi_process_consume)
    assert callable(f2.multi_process_consume)
    assert callable(aio_f3.consume)
    assert callable(f.push)
    assert callable(enable_ctrl_c_quit_on_windows)
    assert f.boost_params.project_name == "test_project1"
    print("[PASS] funweb full example imports & definitions")
    time.sleep(15)
    os._exit(66)
