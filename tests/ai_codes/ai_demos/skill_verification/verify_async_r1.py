"""验证 funboost-async-programming SKILL.md 的技术准确性（r1）"""
import asyncio
import inspect
import os
import sys
import time

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
_ts = int(time.time())
os.environ["PRINT_WRTIE_FILE_NAME"] = f"verify_async_r1_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"verify_async_r1_std_{_ts}"

from funboost import (
    boost,
    BoosterParams,
    BrokerEnum,
    ConcurrentModeEnum,
    TaskOptions,
    AioAsyncResult,
)
from funboost.core.func_params_model import BoosterParams as BoosterParamsModel

PASS = []
FAIL = []


def ok(msg):
    PASS.append(msg)
    print(f"[PASS] {msg}")


def fail(msg):
    FAIL.append(msg)
    print(f"[FAIL] {msg}")


def check_concurrent_mode_enum():
    if hasattr(ConcurrentModeEnum, "ASYNC"):
        ok(f"ConcurrentModeEnum.ASYNC = {ConcurrentModeEnum.ASYNC!r}")
    else:
        fail("ConcurrentModeEnum.ASYNC 不存在")

    if ConcurrentModeEnum.ASYNC == "async":
        ok("ConcurrentModeEnum.ASYNC 值为 'async'")
    else:
        fail(f"ConcurrentModeEnum.ASYNC 值错误: {ConcurrentModeEnum.ASYNC!r}")


def check_booster_params_async_fields():
    model_fields = set(BoosterParamsModel.model_fields.keys())
    for field in (
        "concurrent_mode",
        "concurrent_num",
        "specify_async_loop",
        "is_auto_start_specify_async_loop_in_child_thread",
        "is_using_rpc_mode",
    ):
        if field in model_fields:
            ok(f"BoosterParams.{field} 存在")
        else:
            fail(f"BoosterParams.{field} 不存在")

    defaults = BoosterParamsModel(queue_name="__async_defaults__")
    if defaults.concurrent_mode == ConcurrentModeEnum.THREADING:
        ok("BoosterParams.concurrent_mode 默认 THREADING")
    else:
        fail(f"concurrent_mode 默认值错误: {defaults.concurrent_mode!r}")

    if defaults.specify_async_loop is None:
        ok("BoosterParams.specify_async_loop 默认 None")
    else:
        fail(f"specify_async_loop 默认值错误: {defaults.specify_async_loop!r}")

    if defaults.is_auto_start_specify_async_loop_in_child_thread is True:
        ok("BoosterParams.is_auto_start_specify_async_loop_in_child_thread 默认 True")
    else:
        fail("is_auto_start_specify_async_loop_in_child_thread 默认值错误")


def check_exports():
    import funboost

    for name in ("ConcurrentModeEnum", "AioAsyncResult", "boost", "BoosterParams", "TaskOptions"):
        if hasattr(funboost, name):
            ok(f"funboost 导出 {name}")
        else:
            fail(f"funboost 未导出 {name}")


def check_aio_async_result_api():
    props = ["result", "status_and_result"]
    for prop in props:
        if hasattr(AioAsyncResult, prop):
            ok(f"AioAsyncResult.{prop} 存在")
        else:
            fail(f"AioAsyncResult.{prop} 不存在")

    if inspect.iscoroutinefunction(AioAsyncResult.get):
        ok("AioAsyncResult.get 是 async 方法")
    else:
        fail("AioAsyncResult.get 不是 async 方法")


@boost(BoosterParams(
    queue_name="verify_async_r1_async_task",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    concurrent_mode=ConcurrentModeEnum.ASYNC,
    concurrent_num=10,
    log_level=20,
))
async def async_task(n: int):
    await asyncio.sleep(0.05)
    return n * n


@boost(BoosterParams(
    queue_name="verify_async_r1_sync_task",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    log_level=20,
))
def sync_task(n: int):
    time.sleep(0.05)
    return n + 1


def check_async_def_decorated():
    if inspect.iscoroutinefunction(async_task.consuming_function):
        ok("async def 函数可被 @boost 装饰（consuming_function 是协程）")
    else:
        fail("async def 函数装饰后 consuming_function 不是协程")

    params = async_task.consumer.consumer_params
    if params.concurrent_mode == ConcurrentModeEnum.ASYNC:
        ok("async_task concurrent_mode=ASYNC 配置生效")
    else:
        fail(f"async_task concurrent_mode 错误: {params.concurrent_mode!r}")


def check_method_signatures():
    pub = async_task.publisher
    for name in ("aio_push", "aio_publish", "push", "publish", "consume"):
        if hasattr(async_task, name) and callable(getattr(async_task, name)):
            ok(f"Booster.{name} 方法存在")
        else:
            fail(f"Booster.{name} 方法不存在")

    aio_push_sig = inspect.signature(pub.aio_push)
    aio_publish_sig = inspect.signature(pub.aio_publish)
    if list(aio_push_sig.parameters.keys()) == ["func_args", "func_kwargs"]:
        ok("aio_push(*func_args, **func_kwargs) 签名正确")
    else:
        fail(f"aio_push 签名不符: {aio_push_sig}")

    aio_pub_params = list(aio_publish_sig.parameters.keys())
    if aio_pub_params == ["msg", "task_id", "task_options"]:
        ok("aio_publish(msg, task_id=None, task_options=None) 签名正确")
    else:
        fail(f"aio_publish 签名不符: {aio_publish_sig}")

    if inspect.iscoroutinefunction(pub.aio_push):
        ok("aio_push 是 async 方法")
    else:
        fail("aio_push 不是 async 方法")

    if inspect.iscoroutinefunction(pub.aio_publish):
        ok("aio_publish 是 async 方法")
    else:
        fail("aio_publish 不是 async 方法")

    if hasattr(pub, "get_aio_future") and callable(pub.get_aio_future):
        ok("MEMORY_QUEUE publisher.get_aio_future 存在")
    else:
        fail("MEMORY_QUEUE publisher.get_aio_future 不存在")


async def run_memory_queue_async_demo():
    """SKILL 8.1 精简版：MEMORY_QUEUE + ASYNC + aio_push + get_aio_future"""
    for i in range(3):
        r = await async_task.aio_push(i)
        if isinstance(r, AioAsyncResult):
            ok(f"aio_push 返回 AioAsyncResult task_id={r.task_id[:8]}...")
        else:
            fail(f"aio_push 返回类型错误: {type(r)}")

    r2 = await async_task.aio_publish({"n": 5}, task_options=TaskOptions(countdown=0))
    if isinstance(r2, AioAsyncResult):
        ok("aio_publish 返回 AioAsyncResult")
    else:
        fail(f"aio_publish 返回类型错误: {type(r2)}")

    sync_task.push(100)

    status = await async_task.publisher.get_aio_future(7)
    if hasattr(status, "result") and status.result == 49:
        ok(f"get_aio_future(7) 返回 result={status.result}")
    else:
        fail(f"get_aio_future(7) 结果错误: {getattr(status, 'result', status)!r}")

    status2 = await sync_task.publisher.get_aio_future(10)
    if hasattr(status2, "result") and status2.result == 11:
        ok(f"sync get_aio_future(10) 返回 result={status2.result}")
    else:
        fail(f"sync get_aio_future(10) 结果错误: {getattr(status2, 'result', status2)!r}")


def run_runtime_checks():
    async_task.consume()
    sync_task.consume()
    ok("MEMORY_QUEUE + ASYNC consume() 启动成功")

    asyncio.run(run_memory_queue_async_demo())


if __name__ == "__main__":
    print("=== 静态校验 ===")
    check_exports()
    check_concurrent_mode_enum()
    check_booster_params_async_fields()
    check_aio_async_result_api()
    check_async_def_decorated()
    check_method_signatures()

    print("\n=== 运行时校验（MEMORY_QUEUE + ASYNC）===")
    run_runtime_checks()

    time.sleep(3)
    print(f"\n=== 汇总: PASS={len(PASS)}, FAIL={len(FAIL)} ===")
    if FAIL:
        for item in FAIL:
            print(f"  FAIL: {item}")
        os._exit(1)
    print("[DONE] verify_async_r1 全部通过")
    os._exit(66)
