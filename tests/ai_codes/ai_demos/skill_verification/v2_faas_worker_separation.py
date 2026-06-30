"""验证 skill: funboost-faas-deploy — 消费端 Worker 分离示例"""
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"v2_faas_worker_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"v2_faas_worker_std_{_ts}"

EXAMPLE = "faas-deploy / 消费端 Worker"
PASS = True


def report(ok: bool, msg: str):
    global PASS
    if not ok:
        PASS = False
    tag = "PASS" if ok else "FAIL"
    print(f"[{tag}] {EXAMPLE}: {msg}")


try:
    from funboost import boost, BoosterParams, BrokerEnum, enable_ctrl_c_quit_on_windows

    @boost(BoosterParams(
        queue_name="v2_faas_send_email",
        broker_kind=BrokerEnum.MEMORY_QUEUE,
        is_using_rpc_mode=True,
        concurrent_num=2,
    ))
    def send_email(to: str, subject: str, body: str):
        print(f"worker send_email to={to}")
        return {"status": "sent", "to": to}

    @boost(BoosterParams(
        queue_name="v2_faas_process_order",
        broker_kind=BrokerEnum.MEMORY_QUEUE,
        concurrent_num=2,
    ))
    def process_order(order_id: str):
        print(f"worker process_order order_id={order_id}")
        return {"order_id": order_id, "done": True}

    report(True, "tasks 模块任务 send_email / process_order 定义成功")

    send_email.push("a@x.com", "sub", "body")
    process_order.push("order-001")
    report(True, "发布消息成功")

    send_email.consume()
    process_order.consume()
    report(True, "send_email.consume(); process_order.consume() 启动无报错")

    enable_ctrl_c_quit_on_windows()
    report(callable(enable_ctrl_c_quit_on_windows), "enable_ctrl_c_quit_on_windows() 可调用")

except Exception as e:
    report(False, f"异常: {type(e).__name__}: {e}")

if __name__ == "__main__":
    time.sleep(15)
    print(f"\n=== 最终结果: {'PASS' if PASS else 'FAIL'} ===")
    os._exit(66 if PASS else 1)
