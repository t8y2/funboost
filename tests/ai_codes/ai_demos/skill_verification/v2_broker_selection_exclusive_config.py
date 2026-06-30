"""验证 funboost-broker-selection SKILL.md — broker_exclusive_config 示例"""
import os
import sys
import time

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
_ts = int(time.time())
os.environ["PRINT_WRTIE_FILE_NAME"] = f"v2_broker_exclusive_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"v2_broker_exclusive_std_{_ts}"

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
    time.sleep(15)
    os._exit(66)


@boost(BoosterParams(
    queue_name="v2_rabbit_task",
    broker_kind=BrokerEnum.MEMORY_QUEUE,  # SKILL 示例为 RABBITMQ_AMQPSTORM
    broker_exclusive_config={
        "queue_durable": True,
        "no_ack": False,
    },
    concurrent_num=3,
    qps=10,
))
def task(x):
    print(f"[OK] task x={x}")
    return x


if __name__ == "__main__":
    try:
        task.push(42)
        task.consume()
        time.sleep(15)
        report("broker_exclusive_config 参数 + push + consume 无异常", True)
    except Exception as e:
        report("broker_exclusive_config 参数 + push + consume 无异常", False, str(e))

    print(f"\n=== 最终结果: {'PASS' if PASS else 'FAIL'} ===")
    sys.stdout.flush()
    os._exit(66)
