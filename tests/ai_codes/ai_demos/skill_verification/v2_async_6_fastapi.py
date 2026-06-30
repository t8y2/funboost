"""验证 SKILL: funboost-async-programming §6 FastAPI（MEMORY_QUEUE + get_aio_future 替代 Redis RPC）"""
import asyncio
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"v2_async_6_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"v2_async_6_std_{_ts}"

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.testclient import TestClient

from funboost import boost, BoosterParams, BrokerEnum, ConcurrentModeEnum


@boost(
    BoosterParams(
        queue_name=f"web_async_task_v2_{_ts}",
        broker_kind=BrokerEnum.MEMORY_QUEUE,
        concurrent_mode=ConcurrentModeEnum.ASYNC,
    )
)
async def handle_order(order_id: int):
    await asyncio.sleep(0.3)
    return f"order {order_id} done"


@asynccontextmanager
async def lifespan(app: FastAPI):
    handle_order.consume()
    yield


app = FastAPI(lifespan=lifespan)


@app.post("/order/{order_id}")
async def create_order(order_id: int):
    status = await handle_order.publisher.get_aio_future(order_id)
    return {"result": status.result}


@app.post("/order/sync-push/{order_id}")
async def create_order_sync_push(order_id: int):
    status = await handle_order.publisher.get_aio_future(order_id)
    return {"result": status.result}


if __name__ == "__main__":
    with TestClient(app) as client:
        r1 = client.post("/order/42")
        print(f"/order/42 => {r1.json()}")
        r2 = client.post("/order/sync-push/99")
        print(f"/order/sync-push/99 => {r2.json()}")
    time.sleep(15)
    os._exit(66)
