"""验证 funboost-troubleshooting SKILL §1.2 enable_ctrl_c_quit_on_windows 交互式脚本"""
import os
import time
import inspect

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"v2_ts_01_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"v2_ts_01_std_{_ts}"

from funboost import boost, BoosterParams, BrokerEnum, enable_ctrl_c_quit_on_windows

@boost(BoosterParams(
    queue_name=f"v2_ts_ctrl_c_{_ts}",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    concurrent_num=2,
))
def my_task(x):
    print(f"ctrl_c demo task: {x}")
    return x

if __name__ == "__main__":
    # 验证 SKILL 示例中的 import 与函数可调用（自动化测试不调用 enable_ctrl_c_quit_on_windows，因其永久阻塞）
    assert callable(enable_ctrl_c_quit_on_windows)
    src_file = inspect.getfile(enable_ctrl_c_quit_on_windows)
    print(f"[OK] enable_ctrl_c_quit_on_windows 来自 {src_file}")

    my_task.consume()
    my_task.push(1)
    print("[INFO] SKILL 示例末尾应调用 enable_ctrl_c_quit_on_windows()；自动化测试用 os._exit 替代")
    time.sleep(15)
    os._exit(66)
