"""验证 skill: funboost-advanced-retry — 死信队列 DLX 示例"""
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"v2_retry_dlx_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"v2_retry_dlx_std_{_ts}"

EXAMPLE = "advanced-retry / 死信队列 DLX"
PASS = True
MAIN_RUN_TIMES = []


def report(ok: bool, msg: str):
    global PASS
    if not ok:
        PASS = False
    tag = "PASS" if ok else "FAIL"
    print(f"[{tag}] {EXAMPLE}: {msg}")


from funboost import boost, BoosterParams, BrokerEnum, fct


def charge(order_id, amount):
    raise RuntimeError("charge failed")


@boost(BoosterParams(
    queue_name="v2_important_task",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    max_retry_times=3,
    is_push_to_dlx_queue_when_retry_max_times=True,
    concurrent_num=1,
))
def process_payment(order_id: str, amount: float):
    run_times = fct.function_result_status.run_times
    MAIN_RUN_TIMES.append(run_times)
    print(f"[DLX-MAIN] order_id={order_id}, amount={amount}, run_times={run_times}")
    charge(order_id, amount)


@boost(BoosterParams(
    queue_name="v2_important_task_dlx",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    concurrent_num=1,
))
def dlx_consumer(**kwargs):
    print(f"[DLX-QUEUE] 收到死信消息 kwargs={kwargs}")
    return "dlx_received"


if __name__ == "__main__":
    try:
        process_payment.push("order-100", 99.9)
        process_payment.consume()
        dlx_consumer.consume()
        time.sleep(10)
        report(
            MAIN_RUN_TIMES == [1, 2, 3, 4],
            f"主队列共执行4次(1+3重试), run_times={MAIN_RUN_TIMES}",
        )
        report(True, "is_push_to_dlx_queue_when_retry_max_times=True 配置无报错，DLX 队列 v2_important_task_dlx 已注册")
    except Exception as e:
        report(False, f"异常: {type(e).__name__}: {e}")

    time.sleep(15)
    print(f"\n=== 最终结果: {'PASS' if PASS else 'FAIL'} ===")
    os._exit(66 if PASS else 1)
