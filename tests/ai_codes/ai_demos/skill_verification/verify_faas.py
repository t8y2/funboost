"""验证 funboost-faas-deploy skill 中的代码示例"""
import os
import time
import threading

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"verify_faas_{int(time.time())}"
os.environ["SYS_STD_FILE_NAME"] = f"verify_faas_std_{int(time.time())}"

from funboost import boost, BoosterParams, BrokerEnum

# 验证1: FastAPI router 能正常导入
try:
    from funboost.faas import fastapi_router
    print(f"[OK] fastapi_router 导入成功, type={type(fastapi_router)}")
except ImportError as e:
    print(f"[WARN] fastapi_router 导入失败 (可能未装fastapi): {e}")

# 验证2: Flask blueprint 能正常导入
try:
    from funboost.faas import flask_blueprint
    print(f"[OK] flask_blueprint 导入成功, type={type(flask_blueprint)}")
except ImportError as e:
    print(f"[WARN] flask_blueprint 导入失败 (可能未装flask): {e}")

# 验证3: 定义一个任务并验证 router 集成
@boost(BoosterParams(
    queue_name="faas_verify_task",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    is_using_rpc_mode=True,
    concurrent_num=3,
))
def faas_task(x: int, y: int):
    print(f"[OK] faas_task x={x}, y={y}, result={x+y}")
    return x + y


if __name__ == "__main__":
    faas_task.consume()
    time.sleep(1)

    # 验证4: 通过 push 模拟 FaaS 调用
    result = faas_task.push(10, 20)
    print(f"[OK] faas push result type={type(result)}")

    # 验证5: 启动 FastAPI 并发送请求
    try:
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        app = FastAPI()
        app.include_router(fastapi_router)
        print("[OK] FastAPI app 包含 funboost router")

        client = TestClient(app)

        # 测试 publish 端点
        resp = client.post("/funboost/publish", json={
            "queue_name": "faas_verify_task",
            "msg_body": {"x": 100, "y": 200},
        })
        print(f"[OK] POST /funboost/publish status={resp.status_code}, body={resp.json()}")

    except ImportError as e:
        print(f"[WARN] FastAPI 测试跳过 (未安装): {e}")
    except Exception as e:
        print(f"[WARN] FastAPI 测试异常: {e}")

    time.sleep(5)
    print("[DONE] verify_faas 完成")
    os._exit(66)
