"""验证 skill: funboost-funweb-ops §5 ApsJobAdder 代码侧配合（import + 装饰器，不启动 consume）"""
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"mem_funweb_14_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"mem_funweb_14_std_{_ts}"

from funboost import boost, BoosterParams, BrokerEnum, ApsJobAdder


@boost(BoosterParams(queue_name=f"cron_queue_r3_{_ts}", broker_kind=BrokerEnum.REDIS_ACK_ABLE))
def daily_report(type: str):
    print(f"running daily report: {type}")


if __name__ == "__main__":
    adder = ApsJobAdder(daily_report, job_store_kind="redis")
    assert callable(adder.add_push_job)
    print("[PASS] ApsJobAdder import & instantiation")
    time.sleep(15)
    os._exit(66)
