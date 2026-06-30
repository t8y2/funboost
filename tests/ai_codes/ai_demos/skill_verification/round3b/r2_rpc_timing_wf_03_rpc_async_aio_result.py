"""Round2 验证 funboost-rpc-mode SKILL — 异步 aio_push/aio_publish 返回 AioAsyncResult"""
import asyncio
import os
import sys
import time

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
_ts = int(time.time())
os.environ["PRINT_WRTIE_FILE_NAME"] = f"r2_rpc_03_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"r2_rpc_03_std_{_ts}"

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


from funboost import boost, BoosterParams, BrokerEnum, ConcurrentModeEnum, AioAsyncResult


@boost(BoosterParams(
    queue_name=f"r2b_rpc_async_{_ts}",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    concurrent_mode=ConcurrentModeEnum.ASYNC,
    is_using_rpc_mode=True,
    concurrent_num=5,
))
async def async_add(x: int, y: int):
    return x + y


async def main():
    async_add.consume()
    await asyncio.sleep(1)

    aio_result = await async_add.aio_push(10, 20)
    report(
        "SKILL: aio_push 返回 AioAsyncResult",
        isinstance(aio_result, AioAsyncResult),
        f"type={type(aio_result).__name__}",
    )

    aio_pub = await async_add.aio_publish({"x": 1, "y": 2})
    report(
        "SKILL: aio_publish 返回 AioAsyncResult",
        isinstance(aio_pub, AioAsyncResult),
        f"type={type(aio_pub).__name__}",
    )

    await asyncio.sleep(2)
    result = await aio_result.result
    report(
        "SKILL: await aio_result.result 返回函数值",
        result == 30,
        f"result={result}",
    )

    pub_status = await aio_pub.status_and_result
    report(
        "await aio_result.status_and_result 返回字典",
        isinstance(pub_status, dict) and pub_status.get("result") == 3,
        f"status={pub_status}",
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        report("异步 RPC 运行", False, f"{type(e).__name__}: {e}")

    print(f"\n=== 最终结果: {'PASS' if PASS else 'FAIL'} ===")
    sys.stdout.flush()
    time.sleep(20)
    os._exit(66)
