"""验证 funboost-rpc-mode SKILL.md — 示例3：根据 task_id 查询结果"""
import asyncio
import os
import sys
import time

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
_ts = int(time.time())
os.environ["PRINT_WRTIE_FILE_NAME"] = f"broker_rpc_rpc_query_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"broker_rpc_rpc_query_std_{_ts}"

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
    from funboost.core.msg_result_getter import AsyncResult, AioAsyncResult
    report("import AsyncResult, AioAsyncResult", True)
except Exception as e:
    report("import AsyncResult, AioAsyncResult", False, str(e))
    time.sleep(12)
    os._exit(66)


@boost(BoosterParams(
    queue_name="round3_rpc_query_queue",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    is_using_rpc_mode=True,
    concurrent_num=5,
    qps=10,
))
def compute(x: int, y: int):
    return x * y


async def query_result(task_id: str):
    aio_obj = AioAsyncResult(task_id, timeout=10)
    status_dict = await aio_obj.status_and_result
    if status_dict:
        print(status_dict["result"])
        return status_dict
    print("超时未获取到结果")
    return None


if __name__ == "__main__":
    task_id = "some-task-id-string"

    try:
        compute.consume()
        async_result = compute.push(6, 7)
        task_id = async_result.task_id
        report("先 push 获得真实 task_id", bool(task_id), f"task_id={task_id}")
        time.sleep(3)

        result_obj = AsyncResult(task_id, timeout=10)
        status_dict = result_obj.status_and_result
        if status_dict:
            report(
                "AsyncResult.status_and_result 返回字典",
                True,
                f"result={status_dict.get('result')}, success={status_dict.get('success')}",
            )
            print(status_dict["result"])
            print(status_dict["success"])
        else:
            report(
                "AsyncResult.status_and_result 返回字典",
                False,
                "返回 None（超时，可能 Redis 未配置）",
            )

        status_obj = result_obj.status_and_result_obj
        if status_obj:
            report(
                "status_and_result_obj 返回 FunctionResultStatus",
                True,
                f"result={status_obj.result}, success={status_obj.success}",
            )
            print(status_obj.result)
            print(status_obj.success)
        else:
            report(
                "status_and_result_obj 返回 FunctionResultStatus",
                False,
                "返回 None（超时，可能 Redis 未配置）",
            )

        async_status = asyncio.run(query_result(task_id))
        if async_status:
            report("AioAsyncResult.status_and_result 异步查询", True)
        else:
            report(
                "AioAsyncResult.status_and_result 异步查询",
                False,
                "超时未获取到结果（可能 Redis 未配置）",
            )

    except Exception as e:
        report("task_id 查询示例运行", False, f"{type(e).__name__}: {e}")

    print(f"\n=== 最终结果: {'PASS' if PASS else 'FAIL'} ===")
    sys.stdout.flush()
    time.sleep(12)
    os._exit(66)
