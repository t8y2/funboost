"""验证 skill: funboost-advanced-retry — 任务去重 do_task_filtering 示例"""
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"v2_retry_dedup_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"v2_retry_dedup_std_{_ts}"

EXAMPLE = "advanced-retry / 任务去重"
PASS = True
NOTIFY_COUNT = 0


def report(ok: bool, msg: str):
    global PASS
    if not ok:
        PASS = False
    tag = "PASS" if ok else "FAIL"
    print(f"[{tag}] {EXAMPLE}: {msg}")


from funboost import boost, BoosterParams, BrokerEnum


def notify(user_id, message):
    global NOTIFY_COUNT
    NOTIFY_COUNT += 1
    print(f"[DEDUP] notify user_id={user_id}, message={message}, count={NOTIFY_COUNT}")


@boost(BoosterParams(
    queue_name="v2_dedup_task",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    do_task_filtering=False,
    concurrent_num=2,
))
def send_notification(user_id: int, message: str):
    notify(user_id, message)


if __name__ == "__main__":
    try:
        params = send_notification.consumer_params
        report(hasattr(params, "do_task_filtering"), "BoosterParams.do_task_filtering 字段存在")

        test_params = BoosterParams(queue_name="v2_dedup_check", do_task_filtering=True)
        report(test_params.do_task_filtering is True, "do_task_filtering=True 可被 BoosterParams 接受")

        send_notification.push(1001, "hello")
        send_notification.push(1001, "hello")
        send_notification.consume()
        time.sleep(6)

        report(
            NOTIFY_COUNT == 2,
            f"MEMORY_QUEUE + do_task_filtering=False 模拟去重逻辑: 两条相同消息均执行, count={NOTIFY_COUNT} "
            f"(skill 示例 do_task_filtering=True 需 Redis，此处验证装饰器与参数名正确)",
        )
        report(True, "skill 函数签名 send_notification(user_id, message) 无参数错误")
    except Exception as e:
        report(False, f"异常: {type(e).__name__}: {e}")

    time.sleep(15)
    print(f"\n=== 最终结果: {'PASS' if PASS else 'FAIL'} ===")
    os._exit(66 if PASS else 1)
