"""Round2-04 验证 funboost-async-programming SKILL.md（对照 c4b.md 4b.3 / 4b.13）"""
import asyncio
import inspect
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"verify_all_r2_04_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"verify_all_r2_04_std_{_ts}"

from funboost import (
    AioAsyncResult,
    BoosterParams,
    BrokerEnum,
    ConcurrentModeEnum,
    TaskOptions,
    boost,
)

PASS = []
FAIL = []


def ok(msg):
    PASS.append(msg)
    print(f"[PASS] {msg}")


def fail(msg):
    FAIL.append(msg)
    print(f"[FAIL] {msg}")


@boost(BoosterParams(
    queue_name="verify_all_r2_04_async_q",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    concurrent_mode=ConcurrentModeEnum.ASYNC,
    concurrent_num=20,
    qps=10,
    log_level=20,
))
async def async_task(x: int, y: int = 0):
    await asyncio.sleep(0.1)
    return x + y


def check_skill_static_claims():
    """对照 SKILL 速查表 / 铁律：API 与 BoosterParams 字段存在性"""
    import funboost
    from funboost.core.func_params_model import BoosterParams as BP

    for name in ("AioAsyncResult", "ConcurrentModeEnum", "TaskOptions"):
        if hasattr(funboost, name):
            ok(f"funboost 导出 {name}")
        else:
            fail(f"funboost 未导出 {name}")

    for field in (
        "concurrent_mode",
        "specify_async_loop",
        "is_auto_start_specify_async_loop_in_child_thread",
        "is_using_rpc_mode",
    ):
        if field in BP.model_fields:
            ok(f"BoosterParams.{field} 存在（SKILL 相关 BoosterParams 字段表）")
        else:
            fail(f"BoosterParams.{field} 不存在")

    if not hasattr(async_task, "aio_consume") and not hasattr(async_task, "async_consume"):
        ok("不存在臆造 API aio_consume / async_consume（SKILL 铁律 4）")
    else:
        fail("存在 SKILL 禁止的臆造 API")

    if inspect.iscoroutinefunction(async_task.publisher.aio_push):
        ok("aio_push 是 async 方法（SKILL §2）")
    else:
        fail("aio_push 不是 async 方法")

    params = async_task.consumer.consumer_params
    if params.concurrent_mode == ConcurrentModeEnum.ASYNC:
        ok("concurrent_mode=ConcurrentModeEnum.ASYNC 配置生效（SKILL §1.1）")
    else:
        fail(f"concurrent_mode 配置错误: {params.concurrent_mode!r}")

    if hasattr(async_task.publisher, "get_aio_future"):
        ok("MEMORY_QUEUE publisher.get_aio_future 存在（SKILL §3 / c4b 4b.13）")
    else:
        fail("publisher.get_aio_future 不存在")


async def run_async_runtime_checks():
    """SKILL §2 + §8.1 + c4b 4b.3.1 / 4b.13 运行时验证"""
    # aio_push 返回 AioAsyncResult
    aio_result = await async_task.aio_push(10, 20)
    if isinstance(aio_result, AioAsyncResult):
        ok(f"aio_push 返回 AioAsyncResult task_id={aio_result.task_id[:8]}...")
    else:
        fail(f"aio_push 返回类型错误: {type(aio_result)}")

    # aio_publish 同样返回 AioAsyncResult
    pub_result = await async_task.aio_publish(
        {"x": 3, "y": 4},
        task_options=TaskOptions(countdown=0),
    )
    if isinstance(pub_result, AioAsyncResult):
        ok("aio_publish 返回 AioAsyncResult")
    else:
        fail(f"aio_publish 返回类型错误: {type(pub_result)}")

    # get_aio_future：c4b 4b.13 示例 async_task(x, y) -> x+y
    future = async_task.publisher.get_aio_future(7, 5)
    if asyncio.isfuture(future) or inspect.isawaitable(future):
        ok("get_aio_future 返回 asyncio.Future（可 await）")
    else:
        fail(f"get_aio_future 返回类型错误: {type(future)}")

    status = await future
    if getattr(status, "success", False) and status.result == 12:
        ok(f"get_aio_future(7,5) result={status.result} success={status.success}")
    else:
        fail(f"get_aio_future(7,5) 结果错误: result={getattr(status, 'result', None)!r} success={getattr(status, 'success', None)!r}")

    # 批量 get_aio_future（c4b 4b.13 async_rpc_demo 模式）
    futures = [async_task.publisher.get_aio_future(i, i * 2) for i in range(3, 6)]
    for i, fut in enumerate(futures, start=3):
        st = await fut
        expected = i + i * 2
        if st.result == expected and st.success:
            ok(f"get_aio_future({i},{i*2}) result={st.result}")
        else:
            fail(f"get_aio_future({i},{i*2}) 期望 {expected} 实际 {st.result!r}")


def run_runtime_checks():
    async_task.consume()
    ok("MEMORY_QUEUE + ASYNC consume() 启动成功")
    asyncio.run(run_async_runtime_checks())


if __name__ == "__main__":
    print("=== verify_all_r2_04: funboost-async-programming ===\n")
    print("--- 静态校验 ---")
    check_skill_static_claims()

    print("\n--- 运行时校验（MEMORY_QUEUE + ASYNC + aio_push + get_aio_future）---")
    run_runtime_checks()

    time.sleep(2)
    print(f"\n=== 汇总: PASS={len(PASS)}, FAIL={len(FAIL)} ===")
    if FAIL:
        for item in FAIL:
            print(f"  FAIL: {item}")
        os._exit(1)
    print("[DONE] verify_all_r2_04 全部通过")
    os._exit(66)
