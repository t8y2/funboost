"""验证 funboost-remote-deploy SKILL — kill_all_remote_tasks"""
import inspect
import os
import sys
import time

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
_ts = int(time.time())
os.environ["PRINT_WRTIE_FILE_NAME"] = f"v2_remote_kill_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"v2_remote_kill_std_{_ts}"

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
        from funboost.core.fabric_deploy_helper import kill_all_remote_tasks
        report("import kill_all_remote_tasks", callable(kill_all_remote_tasks))
        sig = inspect.signature(kill_all_remote_tasks)
        for p in ("host", "port", "user", "password"):
            report(f"kill_all_remote_tasks.{p} 参数", p in sig.parameters)
        report("未实际调用 kill_all_remote_tasks", True)
    except Exception as e:
        report("kill_all_remote_tasks 示例", False, str(e))

    print(f"\n=== 最终结果: {'PASS' if PASS else 'FAIL'} ===")
    sys.stdout.flush()
    time.sleep(15)
    os._exit(66)
