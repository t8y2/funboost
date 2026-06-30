"""验证 skill: funboost-funweb-ops §3 care_project_name 参数"""
import inspect
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"mem_funweb_11_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"mem_funweb_11_std_{_ts}"


if __name__ == "__main__":
    from funboost.funweb.app import start_funboost_web_manager

    sig = inspect.signature(start_funboost_web_manager)
    assert "care_project_name" in sig.parameters
    bound = sig.bind_partial(care_project_name="my_project")
    assert bound.arguments["care_project_name"] == "my_project"
    print("[PASS] care_project_name parameter")
    time.sleep(15)
    os._exit(66)
