"""验证 SKILL: developing-funboost-testing — 测试脚本模板"""
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"v2_testing_template_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"v2_testing_template_std_{_ts}"

from funboost import boost, BoosterParams, BrokerEnum


@boost(
    BoosterParams(
        queue_name=f"test_feature_xyz_v2_{_ts}",
        broker_kind=BrokerEnum.SQLITE_QUEUE,
        concurrent_num=5,
        qps=10,
    )
)
def test_task(x: int):
    print(f"处理 {x}，结果 = {x * 2}")
    return x * 2


if __name__ == "__main__":
    for i in range(10):
        test_task.push(i)

    test_task.consume()

    time.sleep(15)
    os._exit(66)
