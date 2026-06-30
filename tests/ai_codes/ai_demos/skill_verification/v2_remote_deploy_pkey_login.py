"""验证 funboost-remote-deploy SKILL — SSH 私钥登录 pkey_file_path"""
import inspect
import os
import sys
import time

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
_ts = int(time.time())
os.environ["PRINT_WRTIE_FILE_NAME"] = f"v2_remote_pkey_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"v2_remote_pkey_std_{_ts}"

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


try:
    from funboost import boost, BoosterParams, BrokerEnum
    report("import", True)
except Exception as e:
    report("import", False, str(e))
    time.sleep(15)
    os._exit(66)


@boost(BoosterParams(queue_name="v2_my_task_pkey", broker_kind=BrokerEnum.MEMORY_QUEUE))
def my_task(x):
    return x


if __name__ == "__main__":
    try:
        sig = inspect.signature(my_task.fabric_deploy)
        report("pkey_file_path 参数存在", "pkey_file_path" in sig.parameters)
        report("password 参数存在（可为空）", "password" in sig.parameters)
        report("process_num 参数存在", "process_num" in sig.parameters)
        report("未实际调用 fabric_deploy", True)
    except Exception as e:
        report("SSH 私钥登录示例", False, str(e))

    print(f"\n=== 最终结果: {'PASS' if PASS else 'FAIL'} ===")
    sys.stdout.flush()
    time.sleep(15)
    os._exit(66)
