"""round3 验证 funboost-remote-deploy SKILL — 导入方式（fabric_deploy 不在顶层导出）"""
import inspect
import os
import sys
import time

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
_ts = int(time.time())
os.environ["PRINT_WRTIE_FILE_NAME"] = f"r3_remote_import_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"r3_remote_import_std_{_ts}"

PASS = True


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
    try:
        import funboost
        report("from funboost import fabric_deploy 不应存在", not hasattr(funboost, "fabric_deploy"))
    except Exception as e:
        report("检查 funboost 顶层导出", False, str(e))

    try:
        from funboost.core.fabric_deploy_helper import fabric_deploy, kill_all_remote_tasks
        report("from fabric_deploy_helper import fabric_deploy", callable(fabric_deploy))
        report("from fabric_deploy_helper import kill_all_remote_tasks", callable(kill_all_remote_tasks))
    except Exception as e:
        report("fabric_deploy_helper import", False, str(e))

    try:
        sig = inspect.signature(fabric_deploy)
        required = {"booster", "host", "port", "user", "password"}
        report("fabric_deploy 必填参数", required.issubset(sig.parameters.keys()))
        optional = {
            "process_num", "pkey_file_path", "extra_shell_str",
            "only_upload_within_the_last_modify_time", "file_volume_limit",
            "invoke_runner_kwargs", "python_interpreter",
        }
        report("fabric_deploy 可选参数", optional.issubset(sig.parameters.keys()))
    except Exception as e:
        report("fabric_deploy 签名检查", False, str(e))

    print(f"\n=== 最终结果: {'PASS' if PASS else 'FAIL'} ===")
    sys.stdout.flush()
    time.sleep(12)
    os._exit(66)
