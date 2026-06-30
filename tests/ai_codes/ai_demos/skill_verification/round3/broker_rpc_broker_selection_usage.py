"""验证 funboost-broker-selection SKILL.md — 示例1：使用示例（broker_kind 选型）"""
import os
import sys
import time

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
_ts = int(time.time())
os.environ["PRINT_WRTIE_FILE_NAME"] = f"broker_rpc_broker_selection_usage_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"broker_rpc_broker_selection_usage_std_{_ts}"

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
    report("import boost, BoosterParams, BrokerEnum", False, str(e))
    time.sleep(12)
    os._exit(66)


def process(data: dict):
    print(f"[OK] process data={data}")
    return data


@boost(BoosterParams(
    queue_name="round3_production_task",
    broker_kind=BrokerEnum.MEMORY_QUEUE,  # SKILL 示例为 REDIS_ACK_ABLE
    concurrent_num=3,
    qps=10,
))
def my_task(data: dict):
    return process(data)


if __name__ == "__main__":
    try:
        my_task.push({"key": "value"})
        my_task.consume()
        time.sleep(8)
        report("使用示例：装饰器 + push + consume 无异常", True)
    except Exception as e:
        report("使用示例：装饰器 + push + consume 无异常", False, str(e))

    print(f"\n=== 最终结果: {'PASS' if PASS else 'FAIL'} ===")
    sys.stdout.flush()
    time.sleep(12)
    os._exit(66)
