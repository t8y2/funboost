"""round3 验证: funboost-advanced-retry — 指数退避重试示例"""
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"faas_retry_07_backoff_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"faas_retry_07_backoff_std_{_ts}"

EXAMPLE = "advanced-retry / 指数退避"
PASS = True
SUCCESS = False


def report(ok: bool, msg: str):
    global PASS
    if not ok:
        PASS = False
    tag = "PASS" if ok else "FAIL"
    print(f"[{tag}] {EXAMPLE}: {msg}")


from funboost import boost, BoosterParams, BrokerEnum, fct


@boost(BoosterParams(
    queue_name="r3_backoff_task",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    max_retry_times=5,
    is_using_advanced_retry=True,
    concurrent_num=1,
))
def rate_limited_api(endpoint: str):
    global SUCCESS
    run_times = fct.function_result_status.run_times
    print(f"[BACKOFF] endpoint={endpoint}, run_times={run_times}, time={time.strftime('%H:%M:%S')}")
    if run_times <= 2:
        raise Exception("被限流了")
    SUCCESS = True
    return {"endpoint": endpoint, "ok": True}


if __name__ == "__main__":
    try:
        rate_limited_api.push("https://api.example.com/rate")
        rate_limited_api.consume()
        time.sleep(12)
        report(SUCCESS, "is_using_advanced_retry=True 指数退避后第3次执行成功")
    except Exception as e:
        report(False, f"异常: {type(e).__name__}: {e}")

    time.sleep(15)
    print(f"\n=== 最终结果: {'PASS' if PASS else 'FAIL'} ===")
    os._exit(66 if PASS else 1)
