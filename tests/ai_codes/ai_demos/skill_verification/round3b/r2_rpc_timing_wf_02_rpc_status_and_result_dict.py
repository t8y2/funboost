"""Round2 验证 funboost-rpc-mode SKILL — status_and_result 返回字典，status_and_result_obj 返回对象"""
import asyncio
import os
import sys
import time

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
_ts = int(time.time())
os.environ["PRINT_WRTIE_FILE_NAME"] = f"r2_rpc_02_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"r2_rpc_02_std_{_ts}"

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


from funboost import boost, BoosterParams, BrokerEnum, AsyncResult, AioAsyncResult
from funboost.core.function_result_status_saver import FunctionResultStatus


@boost(BoosterParams(
    queue_name=f"r2b_rpc_dict_{_ts}",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    is_using_rpc_mode=True,
    concurrent_num=5,
))
def mul(x: int, y: int):
    return x * y


async def async_query(task_id: str):
    aio_obj = AioAsyncResult(task_id, timeout=15)
    return await aio_obj.status_and_result


if __name__ == "__main__":
    mul.consume()
    time.sleep(1)

    async_result = mul.push(6, 7)
    time.sleep(2)

    status_dict = async_result.status_and_result
    report(
        "SKILL: status_and_result 返回字典",
        isinstance(status_dict, dict),
        f"type={type(status_dict).__name__}",
    )
    if isinstance(status_dict, dict):
        report(
            "字典含 result 键",
            "result" in status_dict,
            f"result={status_dict.get('result')}",
        )
        report(
            "字典含 success 键",
            "success" in status_dict,
            f"success={status_dict.get('success')}",
        )
        report(
            "status_dict['result'] 为函数返回值",
            status_dict.get("result") == 42,
            f"expected=42 actual={status_dict.get('result')}",
        )
        report(
            "status_dict['success'] 为 True",
            status_dict.get("success") is True,
            f"success={status_dict.get('success')}",
        )

    status_obj = async_result.status_and_result_obj
    report(
        "SKILL: status_and_result_obj 返回 FunctionResultStatus",
        isinstance(status_obj, FunctionResultStatus),
        f"type={type(status_obj).__name__ if status_obj else None}",
    )
    if status_obj:
        report(
            "status_obj.result 与 status_dict['result'] 一致",
            status_obj.result == 42,
            f"result={status_obj.result}",
        )
        report(
            "status_obj.success 为 True",
            status_obj.success is True,
            f"success={status_obj.success}",
        )

    # 异步查询
    async_status = asyncio.run(async_query(async_result.task_id))
    report(
        "SKILL: await aio_result.status_and_result 返回字典",
        isinstance(async_status, dict),
        f"type={type(async_status).__name__ if async_status else None}",
    )

    print(f"\n=== 最终结果: {'PASS' if PASS else 'FAIL'} ===")
    sys.stdout.flush()
    time.sleep(20)
    os._exit(66)
