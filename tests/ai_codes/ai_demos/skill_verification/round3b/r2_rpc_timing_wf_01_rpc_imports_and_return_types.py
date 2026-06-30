"""Round2 验证 funboost-rpc-mode SKILL — import 路径与 push/publish 返回类型"""
import os
import sys
import time

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
_ts = int(time.time())
os.environ["PRINT_WRTIE_FILE_NAME"] = f"r2_rpc_01_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"r2_rpc_01_std_{_ts}"

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


try:
    from funboost import boost, BoosterParams, BrokerEnum, AsyncResult, AioAsyncResult, TaskOptions
    report("from funboost import AsyncResult, AioAsyncResult, TaskOptions", True)
    report(
        "TaskOptions 类存在且可实例化",
        TaskOptions(max_retry_times=1).max_retry_times == 1,
        f"max_retry_times={TaskOptions(max_retry_times=1).max_retry_times}",
    )
except Exception as e:
    report("from funboost import AsyncResult, AioAsyncResult, TaskOptions", False, str(e))
    time.sleep(20)
    os._exit(66)


@boost(BoosterParams(
    queue_name=f"r2b_rpc_types_{_ts}",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    is_using_rpc_mode=True,
    concurrent_num=5,
    qps=10,
    rpc_timeout=15,
))
def add(x: int, y: int):
    return x + y


if __name__ == "__main__":
    add.consume()
    time.sleep(1)

    ar_push = add.push(1, 2)
    report(
        "SKILL: push() 返回 AsyncResult",
        isinstance(ar_push, AsyncResult),
        f"type={type(ar_push).__name__}",
    )
    report(
        "AsyncResult 有 task_id 属性",
        hasattr(ar_push, "task_id") and bool(ar_push.task_id),
        f"task_id={ar_push.task_id}",
    )

    ar_publish = add.publish({"x": 3, "y": 4})
    report(
        "SKILL: publish() 返回 AsyncResult",
        isinstance(ar_publish, AsyncResult),
        f"type={type(ar_publish).__name__}",
    )

    time.sleep(3)
    status = ar_push.status_and_result
    report(
        "SKILL: status_and_result 阻塞返回结果字典",
        isinstance(status, dict) and status.get("result") == 3,
        f"result={status.get('result') if status else None}",
    )
    report(
        "SKILL: async_result.result 阻塞返回函数返回值",
        ar_push.result == 3,
        f"result={ar_push.result}",
    )

    print(f"\n=== 最终结果: {'PASS' if PASS else 'FAIL'} ===")
    sys.stdout.flush()
    time.sleep(20)
    os._exit(66)
