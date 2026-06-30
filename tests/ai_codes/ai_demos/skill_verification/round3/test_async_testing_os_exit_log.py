"""验证 SKILL: developing-funboost-testing — 方式一 os._exit + 日志文件"""
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"test_xyz_run1_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"test_xyz_std1_{_ts}"

from funboost import boost, BoosterParams, BrokerEnum


@boost(
    BoosterParams(
        queue_name=f"test_os_exit_log_{_ts}",
        broker_kind=BrokerEnum.SQLITE_QUEUE,
        concurrent_num=2,
        qps=10,
    )
)
def log_demo_task(x: int):
    print(f"[LOG_DEMO] x={x}")
    return x


if __name__ == "__main__":
    log_demo_task.push(1)
    log_demo_task.consume()
    print("[VERIFY] os._exit + log env pattern")
    time.sleep(15)
    os._exit(66)
