"""验证 funboost-timing-jobs SKILL — 核心代码模式（interval + cron）"""
import os
import time

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
_ts = int(time.time())
os.environ["PRINT_WRTIE_FILE_NAME"] = f"v2_timing_core_pattern_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"v2_timing_core_pattern_std_{_ts}"

from funboost import boost, BoosterParams, BrokerEnum, ApsJobAdder


@boost(BoosterParams(
    queue_name="v2_scheduled_task",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    qps=5,
    concurrent_num=3,
))
def cleanup_expired_data(table_name: str):
    print(f"清理 {table_name}")


if __name__ == "__main__":
    print("[START] v2_timing_core_pattern")
    cleanup_expired_data.consume()

    # SKILL 示例 interval=30，验证时用 3 秒以便在 sleep 内触发
    ApsJobAdder(cleanup_expired_data).add_push_job(
        trigger="interval",
        seconds=3,
        kwargs={"table_name": "sessions"},
        id="cleanup_sessions",
        replace_existing=True,
    )

    ApsJobAdder(cleanup_expired_data).add_push_job(
        trigger="cron",
        hour=2,
        minute=0,
        kwargs={"table_name": "logs"},
        id="cleanup_logs_daily",
        replace_existing=True,
    )
    print("[OK] interval + cron 注册成功")

    time.sleep(20)
    print("[DONE] v2_timing_core_pattern")
    os._exit(66)
