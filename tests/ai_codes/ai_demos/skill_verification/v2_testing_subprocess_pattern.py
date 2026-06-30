"""验证 SKILL: developing-funboost-testing — 方式二 subprocess.run 外部超时"""
import os
import subprocess
import sys
import time

PROJECT_ROOT = r"D:\codes\funboost"
CHILD = os.path.join(
    PROJECT_ROOT,
    "tests",
    "ai_codes",
    "ai_demos",
    "skill_verification",
    "v2_testing_subprocess_child.py",
)

if __name__ == "__main__":
    result = subprocess.run(
        [sys.executable, CHILD],
        cwd=PROJECT_ROOT,
        timeout=30,
        env={**os.environ, "PYTHONPATH": PROJECT_ROOT},
    )
    print(f"subprocess 退出码: {result.returncode}")
    time.sleep(1)
    os._exit(66)
