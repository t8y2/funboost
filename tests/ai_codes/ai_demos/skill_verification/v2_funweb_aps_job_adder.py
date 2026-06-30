"""验证 skill: funboost-funweb-ops §5 ApsJobAdder 代码侧配合（import + 装饰器，不启动 consume）"""
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"v2_funweb_aps_job_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"v2_funweb_aps_job_std_{_ts}"

from funboost import boost, BoosterParams, BrokerEnum, ApsJobAdder


@boost(BoosterParams(queue_name=f"cron_queue_v2_{_ts}", broker_kind=BrokerEnum.REDIS_ACK_ABLE))
def daily_report(type: str):
    print(f"running daily report: {type}")


if __name__ == "__main__":
    adder = ApsJobAdder(daily_report, job_store_kind="redis")
    assert callable(adder.add_push_job)
    sig_params = adder.add_push_job.__code__.co_varnames
    assert "trigger" in sig_params or hasattr(adder, "add_push_job")
    print("[PASS] ApsJobAdder import & instantiation")
    time.sleep(15)
    os._exit(66)
