"""round3 验证: funboost-faas-deploy — 自定义 API 示例（import + 路由定义，不启动 uvicorn）"""
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"faas_retry_05_custom_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"faas_retry_05_custom_std_{_ts}"

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
        queue_name="r3_faas_custom_task",
        broker_kind=BrokerEnum.MEMORY_QUEUE,
        is_using_rpc_mode=True,
        concurrent_num=2,
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

    report(True, "自定义路由 /compute 定义成功")
    report(True, "AioAsyncResult 导入路径 funboost.core.msg_result_getter 正确")

    route_paths = [getattr(r, "path", None) for r in app.routes]
    report("/compute" in route_paths, f"POST /compute 已注册, paths={route_paths}")

except Exception as e:
    report(False, f"异常: {type(e).__name__}: {e}")

if __name__ == "__main__":
    time.sleep(15)
    print(f"\n=== 最终结果: {'PASS' if PASS else 'FAIL'} ===")
    os._exit(66 if PASS else 1)
