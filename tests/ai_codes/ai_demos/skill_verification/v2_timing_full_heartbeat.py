"""验证 funboost-timing-jobs SKILL — 完整示例（heartbeat + ApsJobAdder from timing_job）"""
import os
import time

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
_ts = int(time.time())
os.environ["PRINT_WRTIE_FILE_NAME"] = f"v2_timing_full_heartbeat_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"v2_timing_full_heartbeat_std_{_ts}"

from funboost import boost, BoosterParams, BrokerEnum
from funboost.timing_job import ApsJobAdder


@boost(BoosterParams(
    queue_name="v2_heartbeat_queue",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    concurrent_num=3,
))
def heartbeat(service_name: str):
    print(f"[{time.strftime('%H:%M:%S')}] 心跳来自 {service_name}")


if __name__ == "__main__":
    print("[START] v2_timing_full_heartbeat")
    heartbeat.consume()

    # SKILL 原文 job_store_kind='redis'，验证改用 memory
    ApsJobAdder(heartbeat, job_store_kind="memory").add_push_job(
        trigger="interval",
        seconds=3,
        kwargs={"service_name": "api-server"},
        id="api_heartbeat",
        replace_existing=True,
    )
    print("[OK] from funboost.timing_job import ApsJobAdder 可用")

    time.sleep(20)
    print("[DONE] v2_timing_full_heartbeat")
    os._exit(66)
