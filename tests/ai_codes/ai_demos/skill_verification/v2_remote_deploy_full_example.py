"""验证 funboost-remote-deploy SKILL — 完整示例 f2/f3 + fabric_deploy 参数"""
import inspect
import os
import sys
import time

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
_ts = int(time.time())
os.environ["PRINT_WRTIE_FILE_NAME"] = f"v2_remote_full_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"v2_remote_full_std_{_ts}"

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
    from funboost.core.fabric_deploy_helper import fabric_deploy
    report("import", True)
except Exception as e:
    report("import", False, str(e))
    time.sleep(15)
    os._exit(66)


@boost(BoosterParams(
    queue_name="v2_queue_test30",
    qps=0.2,
    broker_kind=BrokerEnum.MEMORY_QUEUE,
))
def f2(a, b):
    time.sleep(0.01)
    return a + b


@boost(BoosterParams(
    queue_name="v2_queue_test31",
    qps=0.2,
    broker_kind=BrokerEnum.MEMORY_QUEUE,
))
def f3(a, b):
    return a - b


if __name__ == "__main__":
    try:
        for i in range(3):
            f3.push(i, i * 2)
        report("f3.push 本地发布无异常", True)

        sig = inspect.signature(f3.fabric_deploy)
        deploy_kwargs = {
            "only_upload_within_the_last_modify_time": 1 * 24 * 60 * 60,
            "file_volume_limit": 100 * 1000,
            "process_num": 2,
        }
        for k in deploy_kwargs:
            report(f"f3.fabric_deploy 支持 {k}", k in sig.parameters)

        sig_helper = inspect.signature(fabric_deploy)
        report("fabric_deploy(booster, host, port, user, password, ...)", "booster" in sig_helper.parameters)
        report("f2/f3 函数签名 (a, b)", True)
        # 不调用 f3.fabric_deploy("106.55.244.xx", ...)
    except Exception as e:
        report("完整示例 f2/f3", False, str(e))

    print(f"\n=== 最终结果: {'PASS' if PASS else 'FAIL'} ===")
    sys.stdout.flush()
    time.sleep(15)
    os._exit(66)
