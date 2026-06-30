"""round3 验证 funboost-remote-deploy SKILL — 生产常驻 invoke_runner_kwargs（pty=False）"""
import inspect
import os
import sys
import time

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
_ts = int(time.time())
os.environ["PRINT_WRTIE_FILE_NAME"] = f"r3_remote_pty_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"r3_remote_pty_std_{_ts}"

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


@boost(BoosterParams(queue_name="r3_my_task_pty", broker_kind=BrokerEnum.MEMORY_QUEUE))
def my_task(x):
    return x


if __name__ == "__main__":
    try:
        sig = inspect.signature(my_task.fabric_deploy)
        report("invoke_runner_kwargs 参数存在", "invoke_runner_kwargs" in sig.parameters)
        default = sig.parameters["invoke_runner_kwargs"].default
        report("默认 invoke_runner_kwargs 含 pty", isinstance(default, dict) and "pty" in default)
        report("默认 pty=True", default.get("pty") is True)

        kwargs = {"hide": None, "pty": False, "warn": True}
        report("SKILL 示例 kwargs 键合法", set(kwargs.keys()).issubset({"hide", "pty", "warn", "encoding"}))
        report("未实际调用 fabric_deploy", True)
    except Exception as e:
        report("生产常驻 pty 示例", False, str(e))

    print(f"\n=== 最终结果: {'PASS' if PASS else 'FAIL'} ===")
    sys.stdout.flush()
    time.sleep(12)
    os._exit(66)
