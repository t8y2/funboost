"""验证 round3 / funboost-troubleshooting SKILL §2 PYTHONPATH 与 funboost_config 加载"""
import os
import sys
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"obs_trouble_ts_04_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"obs_trouble_ts_04_std_{_ts}"

PROJECT_ROOT = r"D:\codes\funboost"
pythonpath = os.environ.get("PYTHONPATH", "")
root_norm = PROJECT_ROOT.replace("\\", "/")
paths_norm = [p.replace("\\", "/") for p in sys.path]

if root_norm in paths_norm or pythonpath.replace("\\", "/") == root_norm:
    print(f"[OK] PYTHONPATH 生效: {pythonpath!r}")
else:
    print(f"[WARN] 项目根可能不在 sys.path: PYTHONPATH={pythonpath!r}")

import funboost_config
print(f"[OK] funboost_config 路径: {funboost_config.__file__}")

from funboost import set_frame_config
import inspect
src = inspect.getsource(set_frame_config.use_config_form_funboost_config_module)
assert "importlib.import_module('funboost_config')" in src
print("[OK] set_frame_config 使用 importlib.import_module('funboost_config')")

if __name__ == "__main__":
    time.sleep(15)
    os._exit(66)
