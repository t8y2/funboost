"""验证 funboost-timing-jobs SKILL — 一次性 date 定时任务"""
import os
import time
from datetime import datetime, timedelta

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
_ts = int(time.time())
os.environ["PRINT_WRTIE_FILE_NAME"] = f"timing_wf_timing_date_once_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"timing_wf_timing_date_once_std_{_ts}"

from funboost import boost, BoosterParams, BrokerEnum, ApsJobAdder


@boost(BoosterParams(
    queue_name="r3_send_report_task",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    concurrent_num=3,
))
def send_report(report_type: str):
    print(f"发送报告 report_type={report_type}")


if __name__ == "__main__":
    print("[START] timing_wf_timing_date_once")
    send_report.consume()

    run_at = datetime.now() + timedelta(seconds=5)
    ApsJobAdder(send_report).add_push_job(
        trigger="date",
        run_date=run_at,
        kwargs={"report_type": "monthly"},
        id="july_report",
        replace_existing=True,
    )
    print(f"[OK] date trigger 注册成功 run_at={run_at}")

    time.sleep(20)
    print("[DONE] timing_wf_timing_date_once")
    os._exit(66)
