"""Round2 验证 funboost-rpc-mode SKILL — 未设 is_using_rpc_mode 时 status_and_result 超时返回 None"""
import os
import sys
import time

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
_ts = int(time.time())
os.environ["PRINT_WRTIE_FILE_NAME"] = f"r2_rpc_04_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"r2_rpc_04_std_{_ts}"

PASS = True


def report(name: str, ok: bool, detail: str = ""):
    global PASS
    if not ok:
        PASS = False
    status = "PASS" if ok else "FAIL"
    msg = f"[{status}] {name}"
    if detail:
        msg += f" — {detail}"
    print(msg)


from funboost import boost, BoosterParams, BrokerEnum, AsyncResult, HasNotAsyncResult


@boost(BoosterParams(
    queue_name=f"r2b_rpc_no_rpc_{_ts}",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    is_using_rpc_mode=False,  # SKILL 铁律: 未设置则不持久化结果
    concurrent_num=5,
))
def task_no_rpc(x: int):
    return x * 10


if __name__ == "__main__":
    task_no_rpc.consume()
    time.sleep(1)

    ar = task_no_rpc.push(5)
    time.sleep(2)  # 等待消费完成

    # 短超时验证 SKILL 描述: 超时返回 None
    ar_short = AsyncResult(ar.task_id, timeout=1)
    status_dict = ar_short.status_and_result
    report(
        "SKILL: 未设 is_using_rpc_mode 时 status_and_result 超时返回 None",
        status_dict is None,
        f"actual={status_dict!r}",
    )

    ar_short2 = AsyncResult(ar.task_id, timeout=1)
    try:
        _ = ar_short2.result
        report("SKILL: 未设 is_using_rpc_mode 时 .result 抛出 HasNotAsyncResult", False, "未抛异常")
    except HasNotAsyncResult:
        report("SKILL: 未设 is_using_rpc_mode 时 .result 抛出 HasNotAsyncResult", True)
    except Exception as e:
        report("SKILL: 未设 is_using_rpc_mode 时 .result 抛出 HasNotAsyncResult", False, str(e))

    print(f"\n=== 最终结果: {'PASS' if PASS else 'FAIL'} ===")
    sys.stdout.flush()
    time.sleep(20)
    os._exit(66)
