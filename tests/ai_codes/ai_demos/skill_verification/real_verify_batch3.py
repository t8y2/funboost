"""验证 batch3 三个 Skill 的代码示例能否真实运行（MEMORY_QUEUE）"""
import asyncio
import inspect
import os
import sys
import time

os.environ["PYTHONPATH"] = r"D:\codes\funboost"
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = "real_verify_batch3_print.txt"
os.environ["SYS_STD_FILE_NAME"] = "real_verify_batch3_std.txt"
os.environ["funboost.faas.is_use_local_booster"] = "true"

from funboost import (
    boost,
    BoosterParams,
    BrokerEnum,
    ConcurrentModeEnum,
    TaskOptions,
    AioAsyncResult,
    fct,
)
from funboost.core.func_params_model import BoosterParams as BoosterParamsModel
from funboost.core.active_cousumer_info_getter import SingleQueueConusmerParamsGetter
from funboost.core.booster import booster_registry_default

PASS_COUNT = 0
FAIL_COUNT = 0

# FaaS local booster 模式下 __init__ 仍会先查 Redis 队列名；MEMORY_QUEUE 测试需放行本地已注册队列
_orig_faas_check_booster = SingleQueueConusmerParamsGetter._check_booster_exists
_orig_faas_get_queue_params = SingleQueueConusmerParamsGetter.get_one_queue_params_use_cache


def _patched_faas_check_booster(self):
    use_local = os.environ.get("funboost.faas.is_use_local_booster", "false").lower() == "true"
    if use_local and self.queue_name in booster_registry_default.queue_name__boost_params_map:
        return
    return _orig_faas_check_booster(self)


def _patched_faas_get_queue_params(self):
    use_local = os.environ.get("funboost.faas.is_use_local_booster", "false").lower() == "true"
    if use_local and self.queue_name in booster_registry_default.queue_name__boost_params_map:
        return booster_registry_default.get_boost_params(self.queue_name).get_str_dict()
    return _orig_faas_get_queue_params(self)


SingleQueueConusmerParamsGetter._check_booster_exists = _patched_faas_check_booster
SingleQueueConusmerParamsGetter.get_one_queue_params_use_cache = _patched_faas_get_queue_params

FAAS_EXEC = []
RETRY_RUN_TIMES = []
ASYNC_EXEC = []


def ok(msg):
    global PASS_COUNT
    PASS_COUNT += 1
    print(f"[PASS] {msg}")


def fail(msg):
    global FAIL_COUNT
    FAIL_COUNT += 1
    print(f"[FAIL] {msg}")


# ========== Skill: funboost-faas-deploy ==========


@boost(
    BoosterParams(
        queue_name="real_verify_batch3_email_queue",
        broker_kind=BrokerEnum.MEMORY_QUEUE,
        is_using_rpc_mode=True,
        concurrent_num=3,
    )
)
def send_email(to: str, subject: str, body: str):
    """SKILL faas-deploy 示例函数"""
    FAAS_EXEC.append({"to": to, "subject": subject, "body": body})
    print(f"[EXEC] send_email to={to}")
    return {"status": "sent", "to": to}


def check_faas_import():
    try:
        from funboost.faas import fastapi_router  # noqa: F401

        ok("from funboost.faas import fastapi_router 可导入")
    except ImportError as e:
        fail(f"fastapi_router 导入失败: {e}")


def check_faas_testclient():
    try:
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from funboost.faas import fastapi_router
    except ImportError as e:
        fail(f"FastAPI/TestClient 不可用: {e}")
        return

    send_email.consume()
    time.sleep(1)

    app = FastAPI()
    app.include_router(fastapi_router)
    client = TestClient(app)

    bad = client.post(
        "/funboost/publish",
        json={"queue_name": "real_verify_batch3_email_queue", "msg": {"to": "a@b.com"}},
    )
    if bad.status_code == 422:
        ok("TestClient 使用 msg 而非 msg_body 返回 422")
    else:
        fail(f"错误字段 msg 应 422, 实际 status={bad.status_code}")

    resp = client.post(
        "/funboost/publish",
        json={
            "queue_name": "real_verify_batch3_email_queue",
            "msg_body": {
                "to": "user@example.com",
                "subject": "Hello",
                "body": "Hi",
            },
            "need_result": False,
        },
    )
    body = resp.json()
    if resp.status_code == 200 and body.get("succ") and body.get("data", {}).get("task_id"):
        ok("TestClient POST msg_body 发布成功")
    else:
        fail(f"TestClient msg_body 发布失败: status={resp.status_code}, body={body}")


# ========== Skill: funboost-advanced-retry ==========


def check_retry_static():
    model_fields = set(BoosterParamsModel.model_fields.keys())
    for field in ("max_retry_times", "is_using_advanced_retry", "advanced_retry_config"):
        if field in model_fields:
            ok(f"BoosterParams.{field} 存在")
        else:
            fail(f"BoosterParams.{field} 不存在")

    cfg = BoosterParamsModel(queue_name="__retry_cfg__").advanced_retry_config
    skill_keys = {
        "retry_mode": "sleep",
        "retry_base_interval": 1.0,
        "retry_multiplier": 2.0,
        "retry_max_interval": 60.0,
        "retry_jitter": False,
    }
    for key, expected in skill_keys.items():
        if key not in cfg:
            fail(f"advanced_retry_config 缺少键 {key!r}")
        elif cfg[key] == expected:
            ok(f"advanced_retry_config[{key!r}] 默认值={expected!r}")
        else:
            fail(f"advanced_retry_config[{key!r}] 默认值错误: {cfg[key]!r}")


@boost(
    BoosterParams(
        queue_name="real_verify_batch3_retry_task",
        broker_kind=BrokerEnum.MEMORY_QUEUE,
        max_retry_times=3,
        is_using_advanced_retry=True,
        advanced_retry_config={
            "retry_mode": "sleep",
            "retry_base_interval": 0.1,
            "retry_multiplier": 1.0,
            "retry_max_interval": 0.5,
            "retry_jitter": False,
        },
        concurrent_num=1,
    )
)
def fragile_retry_task(x: int):
    run_times = fct.function_result_status.run_times
    RETRY_RUN_TIMES.append(run_times)
    print(f"[RETRY] x={x}, run_times={run_times}")
    if run_times <= 2:
        raise ValueError(f"模拟失败 run_times={run_times}")
    return x * 10


def run_retry_runtime():
    fragile_retry_task.push(7)
    fragile_retry_task.consume()
    ok("retry 任务 push + consume 启动成功")

    deadline = time.time() + 12
    while time.time() < deadline:
        if len(RETRY_RUN_TIMES) >= 3 and RETRY_RUN_TIMES[-1] == 3:
            break
        time.sleep(0.3)

    if len(RETRY_RUN_TIMES) >= 3:
        ok(f"任务失败后重试执行，run_times 序列={RETRY_RUN_TIMES[:5]}")
    else:
        fail(f"重试未按预期发生，RETRY_RUN_TIMES={RETRY_RUN_TIMES}")

    if RETRY_RUN_TIMES and max(RETRY_RUN_TIMES) >= 3:
        ok("max_retry_times + is_using_advanced_retry 重试后最终成功")
    else:
        fail(f"重试次数不足，RETRY_RUN_TIMES={RETRY_RUN_TIMES}")


# ========== Skill: funboost-async-programming ==========


@boost(
    BoosterParams(
        queue_name="real_verify_batch3_async_queue",
        broker_kind=BrokerEnum.MEMORY_QUEUE,
        concurrent_mode=ConcurrentModeEnum.ASYNC,
        concurrent_num=20,
    )
)
async def async_fetch(url: str):
    await asyncio.sleep(0.05)
    ASYNC_EXEC.append(url)
    print(f"[EXEC] async_fetch url={url}")
    return url


def check_async_static():
    if hasattr(ConcurrentModeEnum, "ASYNC"):
        ok(f"ConcurrentModeEnum.ASYNC = {ConcurrentModeEnum.ASYNC!r}")
    else:
        fail("ConcurrentModeEnum.ASYNC 不存在")

    params = async_fetch.consumer.consumer_params
    if params.broker_kind == BrokerEnum.MEMORY_QUEUE:
        ok("async_fetch broker_kind=MEMORY_QUEUE 配置生效")
    else:
        fail(f"async_fetch broker_kind 错误: {params.broker_kind!r}")

    if params.concurrent_mode == ConcurrentModeEnum.ASYNC:
        ok("async_fetch concurrent_mode=ASYNC 配置生效")
    else:
        fail(f"async_fetch concurrent_mode 错误: {params.concurrent_mode!r}")

    if inspect.iscoroutinefunction(async_fetch.consuming_function):
        ok("async def 消费函数装饰后 consuming_function 是协程")
    else:
        fail("async def 消费函数不是协程")

    pub = async_fetch.publisher
    if hasattr(pub, "aio_push") and inspect.iscoroutinefunction(pub.aio_push):
        ok("aio_push 是 async 方法")
    else:
        fail("aio_push 不存在或不是 async 方法")


async def run_async_publish():
    r = await async_fetch.aio_push("https://example.com/async-test")
    if isinstance(r, AioAsyncResult) and r.task_id:
        ok(f"aio_push 发布成功 task_id={r.task_id[:8]}...")
    else:
        fail(f"aio_push 返回异常: {type(r)}")


def run_async_runtime():
    async_fetch.consume()
    ok("MEMORY_QUEUE + ASYNC consume() 启动成功")
    asyncio.run(run_async_publish())

    deadline = time.time() + 8
    while time.time() < deadline:
        if "https://example.com/async-test" in ASYNC_EXEC:
            break
        time.sleep(0.2)

    if "https://example.com/async-test" in ASYNC_EXEC:
        ok("异步函数 async_fetch 被消费执行")
    else:
        fail(f"async_fetch 未被消费，ASYNC_EXEC={ASYNC_EXEC}")


def verify_faas_execution():
    deadline = time.time() + 8
    while time.time() < deadline:
        if FAAS_EXEC:
            break
        time.sleep(0.2)

    if any(item.get("to") == "user@example.com" for item in FAAS_EXEC):
        ok("FaaS msg_body 触发的 send_email 任务被消费")
    else:
        fail(f"send_email 未被消费，FAAS_EXEC={FAAS_EXEC}")


if __name__ == "__main__":
    print("=== real_verify_batch3: FaaS ===")
    check_faas_import()
    check_faas_testclient()

    print("\n=== real_verify_batch3: Advanced Retry ===")
    check_retry_static()
    run_retry_runtime()

    print("\n=== real_verify_batch3: Async ===")
    check_async_static()
    run_async_runtime()

    print("\n=== real_verify_batch3: FaaS 消费确认 ===")
    verify_faas_execution()

    print(f"\n=== 汇总: PASS={PASS_COUNT}, FAIL={FAIL_COUNT} ===")
    time.sleep(15)
    os._exit(66)
