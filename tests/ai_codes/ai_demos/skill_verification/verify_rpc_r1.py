"""验证 funboost-rpc-mode SKILL.md 中描述的 RPC API 与源码行为一致。"""
import inspect
import os
import time

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"verify_rpc_r1_{int(time.time())}"
os.environ["SYS_STD_FILE_NAME"] = f"verify_rpc_r1_std_{int(time.time())}"

from funboost import boost, BoosterParams, BrokerEnum, ConcurrentModeEnum
from funboost.core.msg_result_getter import AsyncResult, AioAsyncResult
from funboost.core.function_result_status_saver import FunctionResultStatus


def check(label: str, ok: bool, detail: str = ""):
    status = "PASS" if ok else "FAIL"
    msg = f"[{status}] {label}"
    if detail:
        msg += f" — {detail}"
    print(msg)
    return ok


def verify_class_api():
    all_ok = True

    all_ok &= check(
        "AsyncResult 类存在",
        inspect.isclass(AsyncResult),
        AsyncResult.__module__,
    )

    for attr in ("result", "task_id", "status_and_result", "status_and_result_obj"):
        all_ok &= check(
            f"AsyncResult 有 {attr!r}",
            hasattr(AsyncResult, attr),
        )

    has_status = hasattr(AsyncResult, "status")
    all_ok &= check(
        "AsyncResult 有 'status' 属性（SKILL 验证项）",
        has_status,
        "不存在；应使用 status_and_result / is_success()" if not has_status else "",
    )

    all_ok &= check(
        "AioAsyncResult 类存在",
        inspect.isclass(AioAsyncResult),
        AioAsyncResult.__module__,
    )

    for attr in ("status_and_result", "status_and_result_obj", "result"):
        all_ok &= check(
            f"AioAsyncResult 有 {attr!r}",
            hasattr(AioAsyncResult, attr),
        )

    return all_ok


@boost(BoosterParams(
    queue_name="verify_rpc_r1_add",
    broker_kind=BrokerEnum.REDIS_ACK_ABLE,
    concurrent_num=5,
    is_using_rpc_mode=True,
    rpc_timeout=30,
))
def add(x: int, y: int):
    return x + y


def verify_runtime_rpc():
    all_ok = True
    add.consume()
    time.sleep(2)

    async_result = add.push(3, 4)
    all_ok &= check(
        "is_using_rpc_mode=True 时 push 返回 AsyncResult",
        isinstance(async_result, AsyncResult),
        type(async_result).__name__,
    )
    all_ok &= check(
        "AsyncResult.task_id 非空",
        bool(async_result.task_id),
        async_result.task_id,
    )

    publish_result = add.publish({"x": 10, "y": 20})
    all_ok &= check(
        "publish 返回 AsyncResult",
        isinstance(publish_result, AsyncResult),
        type(publish_result).__name__,
    )

    try:
        result_val = async_result.result
        all_ok &= check(
            "async_result.result 返回函数返回值",
            result_val == 7,
            f"got {result_val!r}",
        )
    except Exception as exc:
        all_ok &= check("async_result.result 获取成功", False, f"{type(exc).__name__}: {exc}")

    status_dict = async_result.status_and_result
    all_ok &= check(
        "status_and_result 返回 dict",
        isinstance(status_dict, dict),
        type(status_dict).__name__ if status_dict is not None else "None",
    )
    if isinstance(status_dict, dict):
        all_ok &= check(
            "status_and_result['result'] 正确",
            status_dict.get("result") == 7,
            str(status_dict.get("result")),
        )
        all_ok &= check(
            "status_and_result['success'] 为 True",
            status_dict.get("success") is True,
            str(status_dict.get("success")),
        )

    status_obj = async_result.status_and_result_obj
    all_ok &= check(
        "status_and_result_obj 返回 FunctionResultStatus",
        isinstance(status_obj, FunctionResultStatus),
        type(status_obj).__name__ if status_obj is not None else "None",
    )
    if isinstance(status_obj, FunctionResultStatus):
        all_ok &= check(
            "status_and_result_obj.result 正确",
            status_obj.result == 7,
            str(status_obj.result),
        )
        all_ok &= check(
            "status_and_result_obj.success 为 True",
            status_obj.success is True,
            str(status_obj.success),
        )

    return all_ok


async def verify_aio_async_result():
    import asyncio

    @boost(BoosterParams(
        queue_name="verify_rpc_r1_async_add",
        broker_kind=BrokerEnum.REDIS_ACK_ABLE,
        concurrent_mode=ConcurrentModeEnum.ASYNC,
        concurrent_num=5,
        is_using_rpc_mode=True,
        rpc_timeout=30,
    ))
    async def async_add(x: int, y: int):
        return x + y

    async_add.consume()
    await asyncio.sleep(2)

    all_ok = True
    aio_result = await async_add.aio_push(10, 20)
    all_ok &= check(
        "aio_push 返回 AioAsyncResult",
        isinstance(aio_result, AioAsyncResult),
        type(aio_result).__name__,
    )

    aio_publish_result = await async_add.aio_publish({"x": 1, "y": 2})
    all_ok &= check(
        "aio_publish 返回 AioAsyncResult",
        isinstance(aio_publish_result, AioAsyncResult),
        type(aio_publish_result).__name__,
    )

    try:
        val = await aio_result.result
        all_ok &= check("await aio_result.result 正确", val == 30, str(val))
    except Exception as exc:
        all_ok &= check("await aio_result.result 成功", False, f"{type(exc).__name__}: {exc}")

    sr_dict = await aio_result.status_and_result
    all_ok &= check(
        "await aio_result.status_and_result 返回 dict",
        isinstance(sr_dict, dict),
        type(sr_dict).__name__ if sr_dict is not None else "None",
    )

    sr_obj = await aio_result.status_and_result_obj
    all_ok &= check(
        "await aio_result.status_and_result_obj 返回 FunctionResultStatus",
        isinstance(sr_obj, FunctionResultStatus),
        type(sr_obj).__name__ if sr_obj is not None else "None",
    )

    return all_ok


if __name__ == "__main__":
    import asyncio

    print("=== 静态 API 验证 ===")
    static_ok = verify_class_api()

    print("\n=== 同步 RPC 运行时验证 ===")
    runtime_ok = verify_runtime_rpc()

    print("\n=== 异步 RPC 运行时验证 ===")
    aio_ok = asyncio.run(verify_aio_async_result())

    overall = static_ok and runtime_ok and aio_ok
    print(f"\n[{'ALL PASS' if overall else 'SOME FAILED'}] verify_rpc_r1 完成")
    time.sleep(3)
    os._exit(66 if overall else 1)
