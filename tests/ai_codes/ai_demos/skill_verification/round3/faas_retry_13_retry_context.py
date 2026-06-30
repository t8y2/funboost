"""round3 验证: funboost-advanced-retry — 获取重试上下文 fct 示例"""
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"faas_retry_13_context_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"faas_retry_13_context_std_{_ts}"

EXAMPLE = "advanced-retry / 重试上下文 fct"
PASS = True
CTX_LOGS = []


def report(ok: bool, msg: str):
    global PASS
    if not ok:
        PASS = False
    tag = "PASS" if ok else "FAIL"
    print(f"[{tag}] {EXAMPLE}: {msg}")


from funboost import boost, BoosterParams, BrokerEnum, fct


def fetch(url):
    return {"url": url, "fetched": True}


@boost(BoosterParams(
    queue_name="r3_ctx_retry",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    max_retry_times=3,
    concurrent_num=1,
))
def task_with_context(url: str):
    run_times = fct.function_result_status.run_times
    if run_times > 1:
        msg = f"第 {run_times} 次执行（第 {run_times - 1} 次重试）"
        print(msg)
        CTX_LOGS.append(msg)
    if run_times <= 1:
        raise Exception("ctx retry")
    return fetch(url)


if __name__ == "__main__":
    try:
        task_with_context.push("https://ctx.example.com")
        task_with_context.consume()
        time.sleep(8)
        report(len(CTX_LOGS) >= 1, f"fct.function_result_status.run_times 上下文可用, logs={CTX_LOGS}")
    except Exception as e:
        report(False, f"异常: {type(e).__name__}: {e}")

    time.sleep(15)
    print(f"\n=== 最终结果: {'PASS' if PASS else 'FAIL'} ===")
    os._exit(66 if PASS else 1)
