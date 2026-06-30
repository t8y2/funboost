"""验证 funboost-rpc-mode SKILL.md — 示例1：同步 RPC 模式"""
import os
import sys
import time

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
_ts = int(time.time())
os.environ["PRINT_WRTIE_FILE_NAME"] = f"broker_rpc_rpc_sync_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"broker_rpc_rpc_sync_std_{_ts}"

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
    from funboost import boost, BoosterParams, BrokerEnum
    from funboost.core.msg_result_getter import AsyncResult
    report("import boost, BoosterParams, BrokerEnum, AsyncResult", True)
except Exception as e:
    report("import boost, BoosterParams, BrokerEnum, AsyncResult", False, str(e))
    time.sleep(12)
    os._exit(66)


@boost(BoosterParams(
    queue_name="round3_add_queue",
    broker_kind=BrokerEnum.MEMORY_QUEUE,  # SKILL 示例为 REDIS_ACK_ABLE
    is_using_rpc_mode=True,
    concurrent_num=5,
    qps=10,
))
def add(x: int, y: int):
    return x + y


if __name__ == "__main__":
    try:
        add.consume()
        async_result = add.push(3, 4)
        report(
            "push 返回 AsyncResult",
            isinstance(async_result, AsyncResult),
            f"type={type(async_result).__name__}",
        )
        print(f"Task ID: {async_result.task_id}")

        time.sleep(3)
        try:
            result = async_result.result
            report("async_result.result 获取返回值", result == 7, f"result={result}")
            print(f"结果: {result}")
        except Exception as e:
            report(
                "async_result.result 获取返回值",
                False,
                f"{type(e).__name__}: {e}（RPC 结果存 Redis，无 Redis 时会失败）",
            )
    except Exception as e:
        report("同步 RPC 示例运行", False, str(e))

    print(f"\n=== 最终结果: {'PASS' if PASS else 'FAIL'} ===")
    sys.stdout.flush()
    time.sleep(12)
    os._exit(66)
