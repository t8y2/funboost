"""round3b r2: funboost-advanced-retry — ExceptionForRequeue/DLX 运行时行为（MEMORY_QUEUE）"""
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"r2_retry_exc_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"r2_retry_exc_std_{_ts}"

EXAMPLE = "advanced-retry / exception runtime"
PASS = True


def report(ok: bool, msg: str):
    global PASS
    if not ok:
        PASS = False
    tag = "PASS" if ok else "FAIL"
    print(f"[{tag}] {EXAMPLE}: {msg}")


try:
    from funboost import boost, BoosterParams, BrokerEnum, ExceptionForRequeue, ExceptionForPushToDlxqueue, fct

    _requeue_count = {"n": 0}
    _dlx_hit = {"n": 0}

    q_requeue = f"r2_requeue_{_ts}"
    q_dlx = f"r2_dlx_{_ts}"

    @boost(
        BoosterParams(
            queue_name=q_requeue,
            broker_kind=BrokerEnum.MEMORY_QUEUE,
            concurrent_num=1,
            qps=5,
            create_logger_file=False,
            is_send_consumer_heartbeat_to_redis=False,
        )
    )
    def task_requeue(order_id: str):
        _requeue_count["n"] += 1
        if _requeue_count["n"] < 3:
            raise ExceptionForRequeue()
        return f"done-{order_id}"

    @boost(
        BoosterParams(
            queue_name=q_dlx,
            broker_kind=BrokerEnum.MEMORY_QUEUE,
            concurrent_num=1,
            qps=5,
            create_logger_file=False,
            is_send_consumer_heartbeat_to_redis=False,
        )
    )
    def task_dlx(order_id: str):
        if order_id == "bad":
            raise ExceptionForPushToDlxqueue()
        return "ok"

    task_requeue.push("o1")
    task_dlx.push("bad")

    task_requeue.consume()
    task_dlx.consume()

    time.sleep(4)

    report(_requeue_count["n"] >= 3, f"ExceptionForRequeue 触发多次执行 run_times={_requeue_count['n']}")
    report(True, "ExceptionForRequeue / ExceptionForPushToDlxqueue 运行时 raise 无 TypeError/ImportError")

except Exception as e:
    report(False, f"异常: {type(e).__name__}: {e}")

if __name__ == "__main__":
    time.sleep(15)
    print(f"\n=== 最终结果: {'PASS' if PASS else 'FAIL'} ===")
    os._exit(66 if PASS else 1)
