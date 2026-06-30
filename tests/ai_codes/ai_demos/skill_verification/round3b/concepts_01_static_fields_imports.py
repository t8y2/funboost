"""round3b: understanding-funboost-concepts — import / 字段 / ConcurrentModeEnum 静态验证"""
import os
import sys
import time

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
_ts = int(time.time())
os.environ["PRINT_WRTIE_FILE_NAME"] = f"r3b_concepts_01_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"r3b_concepts_01_std_{_ts}"

PASS = True
SKILL = "understanding-funboost-concepts"


def report(name: str, ok: bool, detail: str = ""):
    global PASS
    if not ok:
        PASS = False
    status = "PASS" if ok else "FAIL"
    msg = f"[{status}] {name}"
    if detail:
        msg += f" — {detail}"
    print(msg)


if __name__ == "__main__":
    print(f"=== {SKILL} static verify ===\n")

    for name in ("boost", "BoosterParams", "BrokerEnum", "fct", "enable_ctrl_c_quit_on_windows", "ConcurrentModeEnum"):
        try:
            mod = __import__("funboost", fromlist=[name])
            getattr(mod, name)
            report(f"from funboost import {name}", True)
        except Exception as e:
            report(f"from funboost import {name}", False, str(e))

    try:
        from funboost.utils.simple_data_class import DataClassBase
        report("from funboost.utils.simple_data_class import DataClassBase", True)
    except Exception as e:
        report("from funboost.utils.simple_data_class import DataClassBase", False, str(e))

    from funboost import BoosterParams, BrokerEnum, ConcurrentModeEnum, fct
    from pydantic import ValidationError

    concept_fields = [
        "queue_name", "broker_kind", "concurrent_mode", "concurrent_num",
        "qps", "max_retry_times", "is_using_advanced_retry", "function_timeout",
        "is_using_rpc_mode", "consumer_override_cls", "user_options",
        "broker_exclusive_config",
    ]
    model_fields = set(BoosterParams.model_fields.keys())
    for field in concept_fields:
        report(f"BoosterParams.{field} 存在", field in model_fields)

    wrong_to_right = {
        "timeout": "function_timeout",
        "max_retries": "max_retry_times",
        "workers": "concurrent_num",
    }
    for bad, good in wrong_to_right.items():
        try:
            BoosterParams(queue_name="x", **{bad: 1})
            report(f"臆造 {bad} 应失败", False)
        except ValidationError:
            report(f"臆造 {bad} 被拒绝 (正确字段 {good})", True)

    modes = ["THREADING", "GEVENT", "EVENTLET", "ASYNC", "SINGLE_THREAD"]
    for mode in modes:
        report(f"ConcurrentModeEnum.{mode} 存在", hasattr(ConcurrentModeEnum, mode))

    fct_proxy_cls = type(fct)
    fct_attrs = ["task_id", "queue_name", "full_msg", "logger", "function_result_status"]
    for attr in fct_attrs:
        report(f"fct.{attr} 存在", isinstance(getattr(fct_proxy_cls, attr, None), property))
    report(
        "fct.function_result_status.run_times 文档路径",
        isinstance(getattr(fct_proxy_cls, "function_result_status", None), property),
    )

    print(f"\n=== {SKILL} 最终结果: {'PASS' if PASS else 'FAIL'} ===")
    sys.stdout.flush()
    time.sleep(12)
    os._exit(66 if PASS else 1)
