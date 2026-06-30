"""验证 SKILL: developing-funboost-testing — 方式一 os._exit + 日志文件"""
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"v2_testing_os_exit_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"v2_testing_os_exit_std_{_ts}"

from funboost import boost, BoosterParams, BrokerEnum


@boost(
    BoosterParams(
        queue_name=f"test_os_exit_v2_{_ts}",
        broker_kind=BrokerEnum.SQLITE_QUEUE,
        concurrent_num=2,
        qps=10,
    )
)
def mini_task(x: int):
    print(f"os_exit_pattern 处理 {x}")
    return x


if __name__ == "__main__":
    for i in range(3):
        mini_task.push(i)
    mini_task.consume()
    time.sleep(15)
    os._exit(66)
