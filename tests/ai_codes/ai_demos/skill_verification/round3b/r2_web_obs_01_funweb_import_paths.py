"""round3b / funboost-funweb-ops §概述 start_funboost_web_manager 等价导入路径"""
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"r2_web_obs_01_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"r2_web_obs_01_std_{_ts}"


if __name__ == "__main__":
    from funboost.funweb.app import start_funboost_web_manager as fn1
    from funboost.funboost_web_manager.app import start_funboost_web_manager as fn2

    assert fn1 is fn2, "等价导入路径应指向同一函数"
    assert callable(fn1)
    print("[PASS] start_funboost_web_manager import paths (funweb + funboost_web_manager)")
    time.sleep(12)
    os._exit(66)
