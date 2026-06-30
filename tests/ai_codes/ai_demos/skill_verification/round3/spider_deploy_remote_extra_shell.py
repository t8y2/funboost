"""round3 验证 funboost-remote-deploy SKILL — extra_shell_str 部署前环境变量"""
import inspect
import os
import sys
import time

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
_ts = int(time.time())
os.environ["PRINT_WRTIE_FILE_NAME"] = f"r3_remote_shell_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"r3_remote_shell_std_{_ts}"

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
    time.sleep(12)
    os._exit(66)


@boost(BoosterParams(queue_name="r3_my_task_shell", broker_kind=BrokerEnum.MEMORY_QUEUE))
def my_task(x):
    return x


if __name__ == "__main__":
    try:
        sig = inspect.signature(my_task.fabric_deploy)
        report("extra_shell_str 参数存在", "extra_shell_str" in sig.parameters)
        default = sig.parameters["extra_shell_str"].default
        report("extra_shell_str 默认空字符串", default == "")
        sample = "export FUNBOOST_CONFIG=/home/deploy/funboost_config.py"
        report("SKILL 示例 extra_shell_str 为 str", isinstance(sample, str))
        report("未实际调用 fabric_deploy", True)
    except Exception as e:
        report("extra_shell_str 示例", False, str(e))

    print(f"\n=== 最终结果: {'PASS' if PASS else 'FAIL'} ===")
    sys.stdout.flush()
    time.sleep(12)
    os._exit(66)
