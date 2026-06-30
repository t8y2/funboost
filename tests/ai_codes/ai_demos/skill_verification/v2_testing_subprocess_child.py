"""subprocess 方式二的子脚本（无 os._exit，由外层 timeout 终止）"""
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"v2_subprocess_child_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"v2_subprocess_child_std_{_ts}"

from funboost import boost, BoosterParams, BrokerEnum


@boost(
    BoosterParams(
        queue_name=f"test_subprocess_child_v2_{_ts}",
        broker_kind=BrokerEnum.SQLITE_QUEUE,
        concurrent_num=2,
        qps=10,
    )
)
def sub_task(x: int):
    print(f"subprocess child 处理 {x}")
    return x


if __name__ == "__main__":
    for i in range(3):
        sub_task.push(i)
    sub_task.consume()
    time.sleep(60)
