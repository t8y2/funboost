"""round3b: using-funboost-basics — import / BoosterParams 字段 / 方法名静态验证"""
import os
import sys
import time

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
_ts = int(time.time())
os.environ["PRINT_WRTIE_FILE_NAME"] = f"r3b_basics_01_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"r3b_basics_01_std_{_ts}"

PASS = True
SKILL = "using-funboost-basics"


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

    # --- imports from skill ---
    imports = [
        "boost", "BoosterParams", "BrokerEnum", "TaskOptions",
        "fct", "enable_ctrl_c_quit_on_windows", "ConcurrentModeEnum",
    ]
    for name in imports:
        try:
            mod = __import__("funboost", fromlist=[name])
            getattr(mod, name)
            report(f"from funboost import {name}", True)
        except Exception as e:
            report(f"from funboost import {name}", False, str(e))

    from funboost import boost, BoosterParams, BrokerEnum, TaskOptions, fct

    # --- BoosterParams fields mentioned in skill ---
    from pydantic import ValidationError

    skill_fields = [
        "queue_name", "broker_kind", "concurrent_num", "concurrent_mode",
        "qps", "max_retry_times", "function_timeout", "log_level",
        "is_using_rpc_mode", "should_check_publish_func_params",
    ]
    model_fields = set(BoosterParams.model_fields.keys())
    for field in skill_fields:
        report(f"BoosterParams.{field} 存在", field in model_fields)

    # --- wrong field names must fail ---
    for bad_kw in ("concurrency", "timeout", "max_retries", "workers"):
        try:
            BoosterParams(queue_name="bad_field_test", **{bad_kw: 10})
            report(f"臆造字段 {bad_kw} 应报错", False, "未抛出 ValidationError")
        except ValidationError:
            report(f"臆造字段 {bad_kw} 被 Pydantic 拒绝", True)
        except Exception as e:
            report(f"臆造字段 {bad_kw} 应报错", False, str(e))

    # --- valid BoosterParams with skill fields ---
    try:
        BoosterParams(
            queue_name="r3b_static",
            broker_kind=BrokerEnum.MEMORY_QUEUE,
            concurrent_num=30,
            qps=10,
            max_retry_times=3,
            log_level=20,
            function_timeout=30,
            is_using_rpc_mode=False,
            should_check_publish_func_params=False,
        )
        report("BoosterParams(skill 字段组合) 实例化", True)
    except Exception as e:
        report("BoosterParams(skill 字段组合) 实例化", False, str(e))

    # --- method names on @boost decorated function ---
    @boost(BoosterParams(queue_name="r3b_method_check", broker_kind=BrokerEnum.MEMORY_QUEUE))
    def sample_task(x):
        return x

    methods = [
        "push", "publish", "consume", "aio_push", "aio_publish",
        "multi_process_consume", "mp_consume",
    ]
    for m in methods:
        report(f"sample_task.{m} 存在", hasattr(sample_task, m) and callable(getattr(sample_task, m)))

    # --- TaskOptions fields from skill ---
    to_fields = ["countdown", "task_id", "eta"]
    for field in to_fields:
        report(f"TaskOptions.{field} 存在", field in TaskOptions.model_fields)

    try:
        TaskOptions(countdown=10, task_id="custom-id-1")
        report("TaskOptions(countdown, task_id) 实例化", True)
    except Exception as e:
        report("TaskOptions(countdown, task_id) 实例化", False, str(e))

    # --- fct attributes from skill table (check @property on proxy class, not runtime access) ---
    fct_proxy_cls = type(fct)
    fct_attrs = ["task_id", "queue_name", "function_params", "full_msg", "logger", "function_result_status"]
    for attr in fct_attrs:
        report(f"fct.{attr} 属性存在", isinstance(getattr(fct_proxy_cls, attr, None), property))

    print(f"\n=== {SKILL} 最终结果: {'PASS' if PASS else 'FAIL'} ===")
    sys.stdout.flush()
    time.sleep(12)
    os._exit(66 if PASS else 1)
