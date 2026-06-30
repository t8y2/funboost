"""验证 SKILL: developing-funboost-testing — 方式二 subprocess.run 外部超时（meta 示例）"""
import os
import subprocess
import sys
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"test_subprocess_parent_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"test_subprocess_parent_std_{_ts}"

# 子脚本：最小 funboost 任务，无 os._exit，由父进程 timeout 终止
CHILD_CODE = '''
import os, time
os.environ["LOG_PATH"] = r"D:\\pythonlogs\\ai_console_outs"
from funboost import boost, BoosterParams, BrokerEnum

@boost(BoosterParams(queue_name="subprocess_child_q", broker_kind=BrokerEnum.SQLITE_QUEUE, concurrent_num=1))
def child_task(x):
    print(f"child {x}")

if __name__ == "__main__":
    child_task.push(0)
    child_task.consume()
    time.sleep(60)
'''

if __name__ == "__main__":
    child_path = os.path.join(os.path.dirname(__file__), f"_subprocess_child_{_ts}.py")
    with open(child_path, "w", encoding="utf-8") as f:
        f.write(CHILD_CODE)

    try:
        result = subprocess.run(
            [sys.executable, child_path],
            cwd=r"D:\codes\funboost",
            timeout=20,
            env={**os.environ, "PYTHONPATH": r"D:\codes\funboost"},
        )
        print(f"subprocess returncode={result.returncode}")
    except subprocess.TimeoutExpired:
        print("subprocess timeout as expected (child has no os._exit)")

    time.sleep(15)
    os._exit(66)
