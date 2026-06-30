"""验证 using-funboost-basics SKILL.md 的技术准确性（r1）"""
import asyncio
import inspect
import os
import sys
import time

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
_ts = int(time.time())
os.environ["PRINT_WRTIE_FILE_NAME"] = f"verify_basics_r1_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"verify_basics_r1_std_{_ts}"

from funboost import (
    boost,
    BoosterParams,
    BrokerEnum,
    ConcurrentModeEnum,
    TaskOptions,
    fct,
    enable_ctrl_c_quit_on_windows,
)
from funboost.core.func_params_model import BoosterParams as BoosterParamsModel
from funboost.publishers.base_publisher import AbstractPublisher

PASS = []
FAIL = []


def ok(msg):
    PASS.append(msg)
    print(f"[PASS] {msg}")


def fail(msg):
    FAIL.append(msg)
    print(f"[FAIL] {msg}")


def check_booster_params_fields():
    """SKILL.md BoosterParams 核心字段表 + 文中提到的其他字段"""
    skill_fields = [
        "queue_name",
        "broker_kind",
        "concurrent_num",
        "concurrent_mode",
        "qps",
        "max_retry_times",
        "function_timeout",
        "log_level",
        "is_using_rpc_mode",
        "should_check_publish_func_params",
    ]
    model_fields = set(BoosterParamsModel.model_fields.keys())
    for field in skill_fields:
        if field in model_fields:
            ok(f"BoosterParams.{field} 存在")
        else:
            fail(f"BoosterParams.{field} 不存在于源码")

    defaults = BoosterParamsModel(queue_name="__defaults_check__")
    checks = [
        ("broker_kind", defaults.broker_kind, BrokerEnum.SQLITE_QUEUE),
        ("concurrent_num", defaults.concurrent_num, 50),
        ("concurrent_mode", defaults.concurrent_mode, ConcurrentModeEnum.THREADING),
        ("qps", defaults.qps, None),
        ("max_retry_times", defaults.max_retry_times, 3),
        ("function_timeout", defaults.function_timeout, None),
        ("log_level", defaults.log_level, 10),
        ("is_using_rpc_mode", defaults.is_using_rpc_mode, False),
    ]
    for name, actual, expected in checks:
        if actual == expected:
            ok(f"BoosterParams.{name} 默认值={expected!r}")
        else:
            fail(f"BoosterParams.{name} 默认值错误: 文档/预期 {expected!r}, 实际 {actual!r}")


def check_task_options_fields():
    for field in ("countdown", "task_id", "eta"):
        if field in TaskOptions.model_fields:
            ok(f"TaskOptions.{field} 存在")
        else:
            fail(f"TaskOptions.{field} 不存在")


def check_method_signatures(booster_obj):
    """核对 push/publish/aio_push/aio_publish 签名"""
    pub = booster_obj.publisher
    push_sig = inspect.signature(pub.push)
    publish_sig = inspect.signature(pub.publish)
    aio_push_sig = inspect.signature(pub.aio_push)
    aio_publish_sig = inspect.signature(pub.aio_publish)

    if list(push_sig.parameters.keys()) == ["func_args", "func_kwargs"]:
        ok("push(*func_args, **func_kwargs) 签名正确")
    else:
        fail(f"push 签名不符: {push_sig}")

    pub_params = list(publish_sig.parameters.keys())
    if pub_params == ["msg", "task_id", "task_options"]:
        ok("publish(msg, task_id=None, task_options=None) 签名正确")
    else:
        fail(f"publish 签名不符: {publish_sig}")

    if list(aio_push_sig.parameters.keys()) == ["func_args", "func_kwargs"]:
        ok("aio_push(*func_args, **func_kwargs) 签名正确")
    else:
        fail(f"aio_push 签名不符: {aio_push_sig}")

    aio_pub_params = list(aio_publish_sig.parameters.keys())
    if aio_pub_params == ["msg", "task_id", "task_options"]:
        ok("aio_publish(msg, task_id=None, task_options=None) 签名正确")
    else:
        fail(f"aio_publish 签名不符: {aio_publish_sig}")

    for name in ("consume", "multi_process_consume", "mp_consume", "push", "publish", "aio_push", "aio_publish"):
        if hasattr(booster_obj, name) and callable(getattr(booster_obj, name)):
            ok(f"Booster.{name} 方法存在")
        else:
            fail(f"Booster.{name} 方法不存在")


def check_exports():
    import funboost

    for name in ("boost", "BoosterParams", "BrokerEnum", "ConcurrentModeEnum", "TaskOptions", "fct", "enable_ctrl_c_quit_on_windows"):
        if hasattr(funboost, name):
            ok(f"funboost 导出 {name}")
        else:
            fail(f"funboost 未导出 {name}")


# ---------- SKILL 代码示例（改用 SQLITE_QUEUE 避免 Redis 依赖）----------

@boost(BoosterParams(
    queue_name="verify_basics_r1_main",
    broker_kind=BrokerEnum.SQLITE_QUEUE,
    concurrent_num=5,
    qps=10,
    max_retry_times=3,
    log_level=20,
))
def my_task(url: str, depth: int = 1):
    print(f"[OK] my_task url={url}, depth={depth}")
    return depth


@boost(BoosterParams(
    queue_name="verify_basics_r1_publish",
    broker_kind=BrokerEnum.SQLITE_QUEUE,
    concurrent_num=3,
))
def publish_task(url: str, depth: int = 1):
    print(f"[OK] publish_task url={url}, depth={depth}")
    return depth


@boost(BoosterParams(queue_name="verify_basics_r1_fct", broker_kind=BrokerEnum.SQLITE_QUEUE, concurrent_num=2))
def fct_task(x):
    print(f"[OK] fct.task_id={fct.task_id}")
    print(f"[OK] fct.queue_name={fct.queue_name}")
    print(f"[OK] fct.function_result_status.run_times={fct.function_result_status.run_times}")
    print(f"[OK] fct.full_msg type={type(fct.full_msg).__name__}")
    return x


@boost(BoosterParams(
    queue_name="verify_basics_r1_external",
    broker_kind=BrokerEnum.SQLITE_QUEUE,
    should_check_publish_func_params=False,
))
def handle_external(**kwargs):
    print(f"[OK] handle_external kwargs={kwargs}")


@boost(BoosterParams(queue_name="verify_basics_r1_async", broker_kind=BrokerEnum.SQLITE_QUEUE, concurrent_num=2))
def async_task(x: int):
    return x * 2


async def run_async_publish_checks():
    r1 = await async_task.aio_push(3)
    ok(f"aio_push 返回 AioAsyncResult task_id={r1.task_id[:8]}...")
    r2 = await async_task.aio_publish({"x": 7}, task_options=TaskOptions(countdown=0))
    ok(f"aio_publish 返回 AioAsyncResult task_id={r2.task_id[:8]}...")


def run_skill_code_examples():
    for i in range(3):
        my_task.push(f"https://example.com/page/{i}", depth=2)
    ok("my_task.push(url, depth=...) 运行成功")

    publish_task.publish(
        {"url": "https://example.com", "depth": 3},
        task_options=TaskOptions(countdown=0, task_id="custom-id-1"),
    )
    ok("publish + TaskOptions(countdown, task_id) 运行成功")

    publish_task.push("https://example.com", depth=3)
    ok("push 只传业务参数 运行成功")

    fct_task.push("ctx")
    ok("fct 上下文任务 push 成功")

    handle_external.push(name="from_java", value=99)
    ok("should_check_publish_func_params=False + **kwargs push 成功")

    asyncio.run(run_async_publish_checks())

    my_task.consume()
    publish_task.consume()
    fct_task.consume()
    handle_external.consume()
    async_task.consume()
    ok("多个 consume() 顺序启动成功")

    if callable(enable_ctrl_c_quit_on_windows):
        ok("enable_ctrl_c_quit_on_windows 可调用")
    else:
        fail("enable_ctrl_c_quit_on_windows 不可调用")


if __name__ == "__main__":
    print("=== 静态校验 ===")
    check_exports()
    check_booster_params_fields()
    check_task_options_fields()
    check_method_signatures(my_task)

    print("\n=== SKILL 代码示例运行 ===")
    run_skill_code_examples()

    time.sleep(12)
    print(f"\n=== 汇总: PASS={len(PASS)}, FAIL={len(FAIL)} ===")
    if FAIL:
        for item in FAIL:
            print(f"  FAIL: {item}")
        os._exit(1)
    print("[DONE] verify_basics_r1 全部通过")
    os._exit(66)
