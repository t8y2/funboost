"""round3 验证 funboost-remote-deploy SKILL — 本地 multi_process_consume 对照"""
import inspect
import os
import sys
import time

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
_ts = int(time.time())
os.environ["PRINT_WRTIE_FILE_NAME"] = f"r3_remote_mp_consume_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"r3_remote_mp_consume_std_{_ts}"

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


@boost(BoosterParams(queue_name="r3_my_task_mp", broker_kind=BrokerEnum.MEMORY_QUEUE))
def my_task(x):
    return x * 2


if __name__ == "__main__":
    try:
        report("multi_process_consume 存在", hasattr(my_task, "multi_process_consume"))
        report("mp_consume 别名存在", hasattr(my_task, "mp_consume"))
        sig = inspect.signature(my_task.multi_process_consume)
        report("multi_process_consume(process_num) 签名", "process_num" in sig.parameters)
        report("未实际调用 multi_process_consume(2)", True)
    except Exception as e:
        report("multi_process_consume 对照示例", False, str(e))

    print(f"\n=== 最终结果: {'PASS' if PASS else 'FAIL'} ===")
    sys.stdout.flush()
    time.sleep(12)
    os._exit(66)
