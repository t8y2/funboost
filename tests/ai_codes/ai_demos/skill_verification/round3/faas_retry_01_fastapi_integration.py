"""round3 验证: funboost-faas-deploy — FastAPI 集成示例（仅 import + router 挂载）"""
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"faas_retry_01_fastapi_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"faas_retry_01_fastapi_std_{_ts}"

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

    routes = [r.path for r in app.routes if hasattr(r, "path") and r.path.startswith("/funboost")]
    report("/funboost/publish" in routes, f"路由 /funboost/publish 已挂载, routes={routes[:5]}...")

    @boost(BoosterParams(
        queue_name="r3_faas_email_queue",
        broker_kind=BrokerEnum.MEMORY_QUEUE,
        is_using_rpc_mode=True,
        concurrent_num=2,
    ))
    def send_email(to: str, subject: str, body: str):
        print(f"发送邮件到 {to}")
        return {"status": "sent", "to": to}

    report(True, "@boost send_email 装饰器定义成功（skill 示例签名无参数错误）")

except Exception as e:
    report(False, f"异常: {type(e).__name__}: {e}")

if __name__ == "__main__":
    time.sleep(15)
    print(f"\n=== 最终结果: {'PASS' if PASS else 'FAIL'} ===")
    os._exit(66 if PASS else 1)
