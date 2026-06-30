"""验证 funboost-timing-jobs SKILL — Redis 作业存储模式（本地改用 memory job_store）"""
import os
import time

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
_ts = int(time.time())
os.environ["PRINT_WRTIE_FILE_NAME"] = f"v2_timing_redis_job_store_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"v2_timing_redis_job_store_std_{_ts}"

from funboost import boost, BoosterParams, BrokerEnum, ApsJobAdder


@boost(BoosterParams(
    queue_name="v2_cleanup_cache_task",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    concurrent_num=3,
))
def cleanup_expired_data(table_name: str):
    print(f"清理 {table_name}")


if __name__ == "__main__":
    print("[START] v2_timing_redis_job_store (memory job_store)")
    cleanup_expired_data.consume()

    # SKILL 原文 job_store_kind='redis'，无 Redis 时用 memory 验证同等 API
    ApsJobAdder(cleanup_expired_data, job_store_kind="memory").add_push_job(
        trigger="interval",
        seconds=3,
        kwargs={"table_name": "cache"},
        id="cleanup_cache",
        replace_existing=True,
    )
    print("[OK] job_store_kind='memory' add_push_job 成功")

    time.sleep(20)
    print("[DONE] v2_timing_redis_job_store")
    os._exit(66)
