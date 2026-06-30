"""验证 round3 / funboost-troubleshooting SKILL §7.2 方式A subprocess + timeout 模式"""
import os
import subprocess
import sys
import time

_ts = int(time.time())

# 内嵌一个极简被测脚本路径（本文件同时作为 runner 验证 subprocess 模式）
TARGET = os.path.join(os.path.dirname(__file__), "obs_trouble_ts_03_ai_test_exit.py")

if __name__ == "__main__":
    result = subprocess.run(
        [sys.executable, TARGET],
        cwd=r"D:\codes\funboost",
        timeout=30,
        env={**os.environ, "PYTHONPATH": r"D:\codes\funboost"},
        capture_output=True,
        text=True,
    )
    print(f"returncode={result.returncode}")
    if result.stdout:
        print(result.stdout[-2000:])
    if result.stderr:
        print(result.stderr[-2000:])
    # obs_trouble_ts_03 使用 os._exit(66)，Windows 上 returncode 可能为 66
    assert result.returncode in (0, 66), f"unexpected returncode {result.returncode}"
    print("[OK] subprocess.run + timeout 模式验证通过")
    time.sleep(15)
    os._exit(66)
