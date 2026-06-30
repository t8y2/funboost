"""验证 funboost-remote-deploy SKILL — 函数级粒度部署（.fabric_deploy 方法）"""
import inspect
import os
import sys
import time

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
_ts = int(time.time())
os.environ["PRINT_WRTIE_FILE_NAME"] = f"v2_remote_task_level_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"v2_remote_task_level_std_{_ts}"

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
    report("import boost, BoosterParams, BrokerEnum", True)
except Exception as e:
    report("import", False, str(e))
    time.sleep(15)
    os._exit(66)


@boost(BoosterParams(queue_name="v2_queue_a", broker_kind=BrokerEnum.MEMORY_QUEUE))
def task_a(x):
    return x * 2


@boost(BoosterParams(queue_name="v2_queue_b", broker_kind=BrokerEnum.MEMORY_QUEUE))
def task_b(x):
    return x + 1


if __name__ == "__main__":
    try:
        report("task_a.fabric_deploy 存在", hasattr(task_a, "fabric_deploy"))
        report("task_b.fabric_deploy 存在", hasattr(task_b, "fabric_deploy"))
        sig_a = inspect.signature(task_a.fabric_deploy)
        sig_b = inspect.signature(task_b.fabric_deploy)
        for name in ("host", "port", "user", "password", "process_num"):
            report(f"task_a.fabric_deploy.{name} 参数", name in sig_a.parameters)
            report(f"task_b.fabric_deploy.{name} 参数", name in sig_b.parameters)
        report("task_a/task_b 队列名不同", task_a.queue_name != task_b.queue_name)
        # 不实际调用 fabric_deploy，避免 SSH 连接
        report("未调用 fabric_deploy（无远程连接）", True)
    except Exception as e:
        report("函数级部署示例", False, str(e))

    print(f"\n=== 最终结果: {'PASS' if PASS else 'FAIL'} ===")
    sys.stdout.flush()
    time.sleep(15)
    os._exit(66)
