"""验证 skill: funboost-faas-deploy — FastAPI 集成示例"""
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"v2_faas_fastapi_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"v2_faas_fastapi_std_{_ts}"

EXAMPLE = "faas-deploy / FastAPI 集成"
PASS = True


def report(ok: bool, msg: str):
    global PASS
    if not ok:
        PASS = False
    tag = "PASS" if ok else "FAIL"
    print(f"[{tag}] {EXAMPLE}: {msg}")


try:
    from fastapi import FastAPI
    from funboost.faas import fastapi_router
    from funboost import boost, BoosterParams, BrokerEnum

    app = FastAPI()
    app.include_router(fastapi_router)
    report(True, "FastAPI app.include_router(fastapi_router) 无报错")

    @boost(BoosterParams(
        queue_name="v2_faas_email_queue",
        broker_kind=BrokerEnum.MEMORY_QUEUE,
        is_using_rpc_mode=True,
        concurrent_num=3,
    ))
    def send_email(to: str, subject: str, body: str):
        print(f"发送邮件到 {to}")
        return {"status": "sent", "to": to}

    report(True, "@boost send_email 装饰器定义成功")

    if __name__ == "__main__":
        send_email.consume()
        time.sleep(1)
        ar = send_email.push("user@example.com", "Hello", "Hi")
        report(ar.task_id is not None, f"send_email.push 返回 task_id={ar.task_id}")

        from fastapi.testclient import TestClient

        client = TestClient(app)
        resp = client.post("/funboost/publish", json={
            "queue_name": "v2_faas_email_queue",
            "msg_body": {"to": "user@example.com", "subject": "Hello", "body": "Hi"},
            "need_result": True,
            "timeout": 10,
        })
        body = resp.json()
        sr = (body.get("data") or {}).get("status_and_result") or {}
        report(
            resp.status_code == 200 and body.get("succ") and sr.get("result", {}).get("status") == "sent",
            f"POST /funboost/publish need_result=true, status={resp.status_code}, result={sr.get('result')}",
        )

except Exception as e:
    report(False, f"异常: {type(e).__name__}: {e}")

if __name__ == "__main__":
    time.sleep(15)
    print(f"\n=== 最终结果: {'PASS' if PASS else 'FAIL'} ===")
    os._exit(66 if PASS else 1)
