"""第2轮深度验证B：异步消费、MemoryFunboostPool、get_future、FaaS、定时任务（MEMORY_QUEUE）"""
import os
import time
import sys

os.environ["PYTHONPATH"] = r"D:\codes\funboost"
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = "real_verify_r2b_print.txt"
os.environ["SYS_STD_FILE_NAME"] = "real_verify_r2b_std.txt"
os.environ["funboost.faas.is_use_local_booster"] = "true"
sys.path.insert(0, r"D:\codes\funboost")

import asyncio

from funboost import (
    boost,
    BoosterParams,
    BrokerEnum,
    ConcurrentModeEnum,
    ApsJobAdder,
    MemoryFunboostPool,
)

_TS = int(time.time())
PASS_COUNT = 0
FAIL_COUNT = 0


def _pass(msg):
    global PASS_COUNT
    PASS_COUNT += 1
    print(f"[PASS] {msg}")


def _fail(msg):
    global FAIL_COUNT
    FAIL_COUNT += 1
    print(f"[FAIL] {msg}")


# ========== 场景1：异步消费 async 函数实际被执行 ==========

async_results = []


@boost(
    BoosterParams(
        queue_name=f"real_verify_r2b_async_{_TS}",
        broker_kind=BrokerEnum.MEMORY_QUEUE,
        concurrent_mode=ConcurrentModeEnum.ASYNC,
        concurrent_num=10,
    )
)
async def fetch_data(url: str):
    async_results.append(url)
    print(f"[EXEC] fetch_data url={url}")


async def _aio_publish_fetch():
    await fetch_data.aio_push("http://a.com")
    await fetch_data.aio_push("http://b.com")


def scenario1_async_consume():
    print("\n=== 场景1：异步消费 async 函数实际被执行 ===")
    asyncio.run(_aio_publish_fetch())
    fetch_data.consume()
    time.sleep(12)
    if len(async_results) == 2:
        _pass(f"异步消费: {async_results}")
    else:
        _fail(f"异步消费: 期望 len=2, 实际 len={len(async_results)}, async_results={async_results}")


# ========== 场景2：MemoryFunboostPool submit + get_future ==========


def scenario2_memory_funboost_pool():
    print("\n=== 场景2：MemoryFunboostPool submit + future.result() ===")

    def compute(x):
        return x ** 2

    try:
        pool = MemoryFunboostPool(concurrent_num=5)
        future = pool.submit(compute, 5)
        result = future.result(timeout=10)
        if result == 25:
            _pass(f"MemoryFunboostPool future.result()={result}")
        else:
            _fail(f"MemoryFunboostPool: 期望 25, 实际 {result!r}")
    except Exception as exc:
        _fail(f"MemoryFunboostPool: {type(exc).__name__}: {exc}")


# ========== 场景3：@boost + get_future() 获取消费结果 ==========


@boost(
    BoosterParams(
        queue_name=f"real_verify_r2b_square_{_TS}",
        broker_kind=BrokerEnum.MEMORY_QUEUE,
        concurrent_num=5,
        is_using_rpc_mode=True,
        rpc_timeout=30,
    )
)
def square(n):
    return n * n


def scenario3_get_future():
    print("\n=== 场景3：@boost + get_future() 获取消费结果 ===")
    square.consume()
    time.sleep(2)
    try:
        async_result = square.push(7)
        future = async_result.get_future()
        val = future.result(timeout=10)
        if val == 49:
            _pass(f"get_future() result={val}")
        else:
            _fail(f"get_future(): 期望 49, 实际 {val!r}")
    except AttributeError:
        _fail("get_future(): AsyncResult 无 get_future() 方法")
    except Exception as exc:
        _fail(f"get_future(): {type(exc).__name__}: {exc}")


# ========== 场景4：FaaS TestClient 发送消息到队列 ==========

faas_exec = []


@boost(
    BoosterParams(
        queue_name=f"real_verify_r2b_faas_{_TS}",
        broker_kind=BrokerEnum.MEMORY_QUEUE,
        concurrent_num=5,
        is_send_consumer_heartbeat_to_redis=True,
    )
)
def faas_task(msg: str):
    faas_exec.append(msg)
    print(f"[EXEC] faas_task msg={msg!r}")


def scenario4_faas_testclient():
    print("\n=== 场景4：FaaS TestClient 发送消息到队列 ===")
    try:
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from funboost.faas import fastapi_router
    except ImportError as exc:
        _fail(f"FaaS: FastAPI 未安装 {exc}")
        return

    faas_task.consume()
    time.sleep(5)

    app = FastAPI()
    app.include_router(fastapi_router)
    client = TestClient(app)

    resp = client.post(
        "/funboost/publish",
        json={
            "queue_name": f"real_verify_r2b_faas_{_TS}",
            "msg_body": {"msg": "hello_faas"},
            "need_result": False,
        },
    )
    status_code = resp.status_code
    body = resp.json()
    if status_code in (200, 202) and body.get("succ"):
        _pass(f"FaaS POST 响应: {status_code}")
    else:
        _fail(f"FaaS POST 响应: status_code={status_code}, body={body}")

    time.sleep(5)
    if len(faas_exec) >= 1:
        _pass(f"FaaS 消费函数被调用: faas_exec={faas_exec}")
    else:
        _fail(f"FaaS 消费函数未被调用: faas_exec={faas_exec}")


# ========== 场景5：定时任务 ApsJobAdder 注册 + 触发 ==========

timing_push_count = []


@boost(
    BoosterParams(
        queue_name=f"real_verify_r2b_timing_{_TS}",
        broker_kind=BrokerEnum.MEMORY_QUEUE,
        concurrent_num=3,
        qps=10,
    )
)
def scheduled_job():
    timing_push_count.append(1)
    print(f"[EXEC] scheduled_job count={len(timing_push_count)}")


def scenario5_aps_job_adder():
    print("\n=== 场景5：定时任务 ApsJobAdder 注册 + 触发 ===")
    scheduled_job.consume()
    adder = ApsJobAdder(scheduled_job, job_store_kind="memory")
    adder.add_push_job(
        trigger="interval",
        seconds=2,
        id=f"real_verify_r2b_interval_{_TS}",
        replace_existing=True,
    )
    time.sleep(5)
    count = len(timing_push_count)
    if count >= 2:
        _pass(f"定时触发 {count} 次")
    else:
        _fail(f"定时触发: 期望 >=2 次, 实际 {count} 次, timing_push_count={timing_push_count}")


if __name__ == "__main__":
    print("=== real_verify_round2b: 第2轮深度验证B ===")

    scenario1_async_consume()
    scenario2_memory_funboost_pool()
    scenario3_get_future()
    scenario4_faas_testclient()
    scenario5_aps_job_adder()

    print("\n=== 第2轮验证B结果 ===")
    print(f"PASS: {PASS_COUNT}")
    print(f"FAIL: {FAIL_COUNT}")
    os._exit(66)
