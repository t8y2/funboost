"""验证 skill: funboost-faas-deploy — 自定义 API 示例"""
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"v2_faas_custom_api_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"v2_faas_custom_api_std_{_ts}"

EXAMPLE = "faas-deploy / 自定义 API"
PASS = True


def report(ok: bool, msg: str):
    global PASS
    if not ok:
        PASS = False
    tag = "PASS" if ok else "FAIL"
    print(f"[{tag}] {EXAMPLE}: {msg}")


try:
    from fastapi import FastAPI
    from funboost import boost, BoosterParams, BrokerEnum

    app = FastAPI()

    @boost(BoosterParams(
        queue_name="v2_faas_custom_task",
        broker_kind=BrokerEnum.MEMORY_QUEUE,
        is_using_rpc_mode=True,
        concurrent_num=3,
    ))
    def heavy_computation(data: list):
        return sum(data)

    @app.post("/compute")
    async def submit_computation(data: list):
        result = await heavy_computation.aio_push(data)
        return {"task_id": result.task_id}

    @app.get("/compute/{task_id}")
    async def get_result(task_id: str):
        from funboost.core.msg_result_getter import AioAsyncResult
        aio_result = AioAsyncResult(task_id)
        status_dict = await aio_result.status_and_result
        return {"success": status_dict.get("success"), "result": status_dict.get("result")}

    report(True, "自定义路由 /compute 定义成功，AioAsyncResult 导入路径正确")

    heavy_computation.consume()
    time.sleep(1)

    from fastapi.testclient import TestClient

    client = TestClient(app)
    submit_resp = client.post("/compute", json=[1, 2, 3, 4])
    submit_body = submit_resp.json()
    task_id = submit_body.get("task_id")
    report(
        submit_resp.status_code == 200 and task_id,
        f"POST /compute status={submit_resp.status_code}, task_id={task_id}",
    )

    time.sleep(2)
    result_resp = client.get(f"/compute/{task_id}")
    result_body = result_resp.json()
    report(
        result_resp.status_code == 200 and result_body.get("success") and result_body.get("result") == 10,
        f"GET /compute/{{task_id}} success={result_body.get('success')}, result={result_body.get('result')}",
    )

except Exception as e:
    report(False, f"异常: {type(e).__name__}: {e}")

if __name__ == "__main__":
    time.sleep(15)
    print(f"\n=== 最终结果: {'PASS' if PASS else 'FAIL'} ===")
    os._exit(66 if PASS else 1)
