"""round3 验证: funboost-advanced-retry — advanced_retry_config 自定义退避示例"""
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"faas_retry_08_custom_cfg_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"faas_retry_08_custom_cfg_std_{_ts}"

EXAMPLE = "advanced-retry / custom_backoff_config"
PASS = True
SUCCESS = False


def report(ok: bool, msg: str):
    global PASS
    if not ok:
        PASS = False
    tag = "PASS" if ok else "FAIL"
    print(f"[{tag}] {EXAMPLE}: {msg}")


from funboost import boost, BoosterParams, BrokerEnum, fct


def process(data):
    return {"processed": data}


@boost(BoosterParams(
    queue_name="r3_custom_backoff_task",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    max_retry_times=8,
    is_using_advanced_retry=True,
    advanced_retry_config={
        "retry_mode": "sleep",
        "retry_base_interval": 0.5,
        "retry_multiplier": 2.0,
        "retry_max_interval": 5.0,
        "retry_jitter": False,
    },
    concurrent_num=1,
))
def custom_backoff_task(data: dict):
    global SUCCESS
    run_times = fct.function_result_status.run_times
    print(f"[CUSTOM] data={data}, run_times={run_times}")
    if run_times <= 1:
        raise Exception("custom backoff fail")
    SUCCESS = True
    return process(data)


if __name__ == "__main__":
    try:
        params = custom_backoff_task.boost_params
        cfg = params.advanced_retry_config
        report(cfg.get("retry_mode") == "sleep", f"advanced_retry_config retry_mode={cfg.get('retry_mode')!r}")
        report(cfg.get("retry_jitter") is False, f"retry_jitter={cfg.get('retry_jitter')}")

        custom_backoff_task.push({"k": "v"})
        custom_backoff_task.consume()
        time.sleep(6)
        report(SUCCESS, "custom_backoff_task 自定义退避配置后执行成功")
    except Exception as e:
        report(False, f"异常: {type(e).__name__}: {e}")

    time.sleep(15)
    print(f"\n=== 最终结果: {'PASS' if PASS else 'FAIL'} ===")
    os._exit(66 if PASS else 1)
