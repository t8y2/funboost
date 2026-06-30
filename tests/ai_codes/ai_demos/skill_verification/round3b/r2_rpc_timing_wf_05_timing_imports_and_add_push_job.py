"""Round2 验证 funboost-timing-jobs SKILL — import 路径与 add_push_job 方法存在"""
import os
import sys
import time

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
_ts = int(time.time())
os.environ["PRINT_WRTIE_FILE_NAME"] = f"r2_timing_05_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"r2_timing_05_std_{_ts}"

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


# SKILL 核心模式: from funboost import ... ApsJobAdder
try:
    from funboost import boost, BoosterParams, BrokerEnum, ApsJobAdder as ApsJobAdderFromFunboost
    report("from funboost import ApsJobAdder", True)
except Exception as e:
    report("from funboost import ApsJobAdder", False, str(e))

# SKILL 完整示例: from funboost.timing_job import ApsJobAdder
try:
    from funboost.timing_job import ApsJobAdder as ApsJobAdderFromTimingJob
    report("from funboost.timing_job import ApsJobAdder", True)
except Exception as e:
    report("from funboost.timing_job import ApsJobAdder", False, str(e))

report(
    "两种 import 路径指向同一类",
    ApsJobAdderFromFunboost is ApsJobAdderFromTimingJob,
    f"funboost={ApsJobAdderFromFunboost} timing_job={ApsJobAdderFromTimingJob}",
)

report(
    "ApsJobAdder 有 add_push_job 方法",
    callable(getattr(ApsJobAdderFromFunboost, "add_push_job", None)),
)

from datetime import datetime, timedelta


@boost(BoosterParams(
    queue_name=f"r2b_timing_{_ts}",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    concurrent_num=3,
))
def scheduled_task(table_name: str):
    print(f"清理 {table_name}")


if __name__ == "__main__":
    scheduled_task.consume()

    adder = ApsJobAdderFromFunboost(scheduled_task)
    report("ApsJobAdder(booster) 实例化", hasattr(adder, "booster"))

    # interval
    try:
        adder.add_push_job(
            trigger="interval",
            seconds=30,
            kwargs={"table_name": "sessions"},
            id=f"r2b_interval_{_ts}",
            replace_existing=True,
        )
        report("add_push_job(trigger='interval', seconds=...)", True)
    except Exception as e:
        report("add_push_job(trigger='interval')", False, str(e))

    # cron
    try:
        adder.add_push_job(
            trigger="cron",
            hour=2,
            minute=0,
            kwargs={"table_name": "logs"},
            id=f"r2b_cron_{_ts}",
            replace_existing=True,
        )
        report("add_push_job(trigger='cron', hour=, minute=)", True)
    except Exception as e:
        report("add_push_job(trigger='cron')", False, str(e))

    # date — SKILL 一次性定时
    try:
        adder.add_push_job(
            trigger="date",
            run_date=datetime.now() + timedelta(seconds=60),
            kwargs={"table_name": "once"},
            id=f"r2b_date_{_ts}",
            replace_existing=True,
        )
        report("add_push_job(trigger='date', run_date=datetime(...))", True)
    except Exception as e:
        report("add_push_job(trigger='date')", False, str(e))

    # args — SKILL 位置参数
    try:
        adder.add_push_job(
            trigger="interval",
            seconds=60,
            args=("positional_table",),
            id=f"r2b_args_{_ts}",
            replace_existing=True,
        )
        report("add_push_job(args=(...)) 参数存在", True)
    except Exception as e:
        report("add_push_job(args=(...))", False, str(e))

    print(f"\n=== 最终结果: {'PASS' if PASS else 'FAIL'} ===")
    sys.stdout.flush()
    time.sleep(20)
    os._exit(66)
