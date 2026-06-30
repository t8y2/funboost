"""验证 funboost-rpc-mode SKILL.md — 示例2：异步 RPC 模式"""
import asyncio
import os
import sys
import time

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
_ts = int(time.time())
os.environ["PRINT_WRTIE_FILE_NAME"] = f"broker_rpc_rpc_async_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"broker_rpc_rpc_async_std_{_ts}"

PASS = True


def report(name: str, ok: bool, detail: str = ""):
    global PASS
    if not ok:
        PASS = False
    status = "PASS" if ok else "FAIL"
    msg = f"[{status}] {name}"
    if detail:
        msg += f" — {detail}"
    print(msg)


try:
    from funboost import boost, BoosterParams, BrokerEnum, ConcurrentModeEnum
    from funboost.core.msg_result_getter import AioAsyncResult
    report("import boost, BoosterParams, BrokerEnum, ConcurrentModeEnum, AioAsyncResult", True)
except Exception as e:
    report("import 依赖", False, str(e))
    time.sleep(12)
    os._exit(66)


@boost(BoosterParams(
    queue_name="round3_async_add_queue",
    broker_kind=BrokerEnum.MEMORY_QUEUE,  # SKILL 示例为 REDIS_ACK_ABLE
    concurrent_mode=ConcurrentModeEnum.ASYNC,
    is_using_rpc_mode=True,
    concurrent_num=5,
))
async def async_add(x: int, y: int):
    return x + y


async def main():
    async_add.consume()

    aio_result = await async_add.aio_push(10, 20)
    report(
        "aio_push 返回 AioAsyncResult",
        isinstance(aio_result, AioAsyncResult),
        f"type={type(aio_result).__name__}",
    )

    await asyncio.sleep(3)
    try:
        result = await aio_result.result
        report("await aio_result.result 获取返回值", result == 30, f"result={result}")
        print(f"结果: {result}")
    except Exception as e:
        report(
            "await aio_result.result 获取返回值",
            False,
            f"{type(e).__name__}: {e}（RPC 结果存 Redis，无 Redis 时会失败）",
        )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        report("异步 RPC 示例运行", False, str(e))

    print(f"\n=== 最终结果: {'PASS' if PASS else 'FAIL'} ===")
    sys.stdout.flush()
    time.sleep(12)
    os._exit(66)
