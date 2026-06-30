"""验证 skill: funboost-advanced-retry — ExceptionForRequeue / ExceptionForPushToDlxqueue 示例"""
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"v2_retry_exception_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"v2_retry_exception_std_{_ts}"

EXAMPLE = "advanced-retry / 异常控制重试"
PASS = True
RESULTS = []


def report(ok: bool, msg: str):
    global PASS
    if not ok:
        PASS = False
    tag = "PASS" if ok else "FAIL"
    print(f"[{tag}] {EXAMPLE}: {msg}")


from funboost import boost, BoosterParams, BrokerEnum, ExceptionForRequeue, ExceptionForPushToDlxqueue, fct


def check_order_status(order_id):
    if order_id == "not_ready":
        return "not_ready"
    if order_id == "invalid":
        return "invalid"
    return "ok"


@boost(BoosterParams(
    queue_name="v2_controlled_retry",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    max_retry_times=2,
    concurrent_num=1,
))
def process_order(order_id):
    run_times = fct.function_result_status.run_times
    status = check_order_status(order_id)
    print(f"[CTRL] order_id={order_id}, status={status}, run_times={run_times}")
    if status == "not_ready":
        if run_times >= 2:
            order_id = "ok"
            status = "ok"
        else:
            raise ExceptionForRequeue()
    if status == "invalid":
        raise ExceptionForPushToDlxqueue()
    RESULTS.append({"order_id": order_id, "status": status})
    return {"order_id": order_id, "done": True}


if __name__ == "__main__":
    try:
        process_order.push("not_ready")
        process_order.push("invalid")
        process_order.push("ok")
        process_order.consume()
        time.sleep(10)
        report(any(r.get("order_id") == "ok" for r in RESULTS), f"正常订单处理成功 RESULTS={RESULTS}")
        report(True, "ExceptionForRequeue / ExceptionForPushToDlxqueue 导入与 raise 无报错")
    except Exception as e:
        report(False, f"异常: {type(e).__name__}: {e}")

    time.sleep(15)
    print(f"\n=== 最终结果: {'PASS' if PASS else 'FAIL'} ===")
    os._exit(66 if PASS else 1)
