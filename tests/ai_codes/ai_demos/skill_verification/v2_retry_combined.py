"""验证 skill: funboost-advanced-retry — 组合多种策略 resilient_task 示例"""
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"v2_retry_combined_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"v2_retry_combined_std_{_ts}"

EXAMPLE = "advanced-retry / 组合策略"
PASS = True
PROCESSED = []


def report(ok: bool, msg: str):
    global PASS
    if not ok:
        PASS = False
    tag = "PASS" if ok else "FAIL"
    print(f"[{tag}] {EXAMPLE}: {msg}")


from funboost import boost, BoosterParams, BrokerEnum, fct


def process(job_id, payload):
    PROCESSED.append({"job_id": job_id, "payload": payload})
    return {"job_id": job_id, "ok": True}


@boost(BoosterParams(
    queue_name="v2_resilient_pipeline",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    max_retry_times=5,
    is_using_advanced_retry=True,
    is_push_to_dlx_queue_when_retry_max_times=True,
    function_timeout=60,
    do_task_filtering=False,
    concurrent_num=1,
))
def resilient_task(job_id: str, payload: dict):
    run_times = fct.function_result_status.run_times
    print(f"[RESILIENT] job_id={job_id}, run_times={run_times}")
    if run_times <= 1:
        raise Exception("transient failure")
    return process(job_id, payload)


if __name__ == "__main__":
    try:
        p = resilient_task.consumer_params
        report(p.max_retry_times == 5, "max_retry_times=5")
        report(p.is_using_advanced_retry is True, "is_using_advanced_retry=True")
        report(p.is_push_to_dlx_queue_when_retry_max_times is True, "is_push_to_dlx_queue_when_retry_max_times=True")
        report(p.function_timeout == 60, "function_timeout=60")
        report(p.do_task_filtering is False, "do_task_filtering 在 MEMORY_QUEUE 测试中设为 False（skill 原例需 Redis）")

        resilient_task.push("job-1", {"step": "a"})
        resilient_task.consume()
        time.sleep(8)
        report(len(PROCESSED) == 1, f"组合策略退避重试后成功, PROCESSED={PROCESSED}")
    except Exception as e:
        report(False, f"异常: {type(e).__name__}: {e}")

    time.sleep(15)
    print(f"\n=== 最终结果: {'PASS' if PASS else 'FAIL'} ===")
    os._exit(66 if PASS else 1)
