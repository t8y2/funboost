"""Round2 验证 funboost-timing-jobs SKILL — ApsJobAdder 定时 push 进队列（非直接执行函数）"""
import os
import sys
import time

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
_ts = int(time.time())
os.environ["PRINT_WRTIE_FILE_NAME"] = f"r2_timing_06_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"r2_timing_06_std_{_ts}"

PASS = True
EXEC_COUNT = {"n": 0}


def report(name: str, ok: bool, detail: str = ""):
    global PASS
    if not ok:
        PASS = False
    status = "PASS" if ok else "FAIL"
    msg = f"[{status}] {name}"
    if detail:
        msg += f" — {detail}"
    print(msg)


from funboost import boost, BoosterParams, BrokerEnum, ApsJobAdder


@boost(BoosterParams(
    queue_name=f"r2b_timing_push_{_ts}",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    concurrent_num=3,
))
def heartbeat(service_name: str):
    EXEC_COUNT["n"] += 1
    print(f"心跳来自 {service_name}, count={EXEC_COUNT['n']}")


if __name__ == "__main__":
    heartbeat.consume()

    ApsJobAdder(heartbeat).add_push_job(
        trigger="interval",
        seconds=2,
        kwargs={"service_name": "api-server"},
        id=f"r2b_heartbeat_{_ts}",
        replace_existing=True,
    )
    report("interval job 注册成功", True)

    before = EXEC_COUNT["n"]
    time.sleep(7)  # 应触发约 2-3 次
    after = EXEC_COUNT["n"]

    report(
        "SKILL: ApsJobAdder 定时 push 消息被消费者执行",
        after > before,
        f"before={before} after={after}",
    )
    report(
        "SKILL: 非直接调用函数（需 consume 消费）",
        after >= 2,
        f"executions={after}",
    )

    print(f"\n=== 最终结果: {'PASS' if PASS else 'FAIL'} ===")
    sys.stdout.flush()
    time.sleep(20)
    os._exit(66)
