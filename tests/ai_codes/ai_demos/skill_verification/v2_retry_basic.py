"""验证 skill: funboost-advanced-retry — 基础重试示例"""
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"v2_retry_basic_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"v2_retry_basic_std_{_ts}"

EXAMPLE = "advanced-retry / 基础重试"
PASS = True
SUCCESS_RUN_TIMES = []


def report(ok: bool, msg: str):
    global PASS
    if not ok:
        PASS = False
    tag = "PASS" if ok else "FAIL"
    print(f"[{tag}] {EXAMPLE}: {msg}")


from funboost import boost, BoosterParams, BrokerEnum, fct


@boost(BoosterParams(
    queue_name="v2_fragile_task",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    max_retry_times=5,
    function_timeout=30,
    concurrent_num=2,
))
def call_external_api(url: str):
    run_times = fct.function_result_status.run_times
    print(f"[RETRY] url={url}, run_times={run_times}")
    if run_times <= 3:
        raise ValueError(f"模拟 API 失败 run_times={run_times}")
    SUCCESS_RUN_TIMES.append(run_times)
    return {"url": url, "mock": True}


if __name__ == "__main__":
    try:
        call_external_api.push("https://example.com/api")
        call_external_api.consume()
        time.sleep(8)
        report(
            SUCCESS_RUN_TIMES and SUCCESS_RUN_TIMES[-1] == 4,
            f"max_retry_times=5 时第4次执行成功, run_times={SUCCESS_RUN_TIMES}",
        )
    except Exception as e:
        report(False, f"异常: {type(e).__name__}: {e}")

    time.sleep(15)
    print(f"\n=== 最终结果: {'PASS' if PASS else 'FAIL'} ===")
    os._exit(66 if PASS else 1)
