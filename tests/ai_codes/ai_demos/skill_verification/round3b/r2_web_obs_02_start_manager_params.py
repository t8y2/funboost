"""round3b / funboost-funweb-ops §1 start_funboost_web_manager 参数签名与默认值"""
import inspect
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"r2_web_obs_02_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"r2_web_obs_02_std_{_ts}"


if __name__ == "__main__":
    from funboost.funweb.app import start_funboost_web_manager

    sig = inspect.signature(start_funboost_web_manager)
    expected = ["host", "port", "block", "debug", "care_project_name"]
    assert list(sig.parameters.keys()) == expected, f"params={list(sig.parameters.keys())}"

    defaults = {
        "host": "0.0.0.0",
        "port": 27018,
        "block": False,
        "debug": False,
        "care_project_name": None,
    }
    for name, val in defaults.items():
        assert sig.parameters[name].default == val, f"{name} default mismatch"

    bound = sig.bind(
        host="0.0.0.0",
        port=27018,
        block=False,
        debug=False,
        care_project_name="my_project",
    )
    bound.apply_defaults()
    assert bound.arguments["care_project_name"] == "my_project"
    print("[PASS] start_funboost_web_manager signature & defaults match skill")
    time.sleep(12)
    os._exit(66)
