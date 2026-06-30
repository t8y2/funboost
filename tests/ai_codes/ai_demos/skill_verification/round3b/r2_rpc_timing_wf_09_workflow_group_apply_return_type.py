"""Round2 验证 funboost-workflow SKILL — group.apply() 返回结果列表"""
import os
import sys
import time

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
_ts = int(time.time())
os.environ["PRINT_WRTIE_FILE_NAME"] = f"r2_wf_09_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"r2_wf_09_std_{_ts}"

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


from funboost import boost, BrokerEnum
from funboost.workflow import group, WorkflowBoosterParams
from funboost.core.function_result_status_saver import FunctionResultStatus


class WfParams(WorkflowBoosterParams):
    broker_kind: str = BrokerEnum.MEMORY_QUEUE
    concurrent_num: int = 5
    max_retry_times: int = 0
    rpc_timeout: int = 30


@boost(WfParams(queue_name=f"r2b_wf_group_{_ts}"))
def process(file_path: str, resolution: str = "720p"):
    return f"{file_path}.{resolution}.mp4"


if __name__ == "__main__":
    process.consume()
    time.sleep(2)

    parallel_tasks = group(
        process.s("/tmp/video.mp4", resolution="360p"),
        process.s("/tmp/video.mp4", resolution="720p"),
        process.s("/tmp/video.mp4", resolution="1080p"),
    )
    result = parallel_tasks.apply()

    report(
        "SKILL: group.apply() 返回 list",
        isinstance(result, list),
        f"type={type(result).__name__} len={len(result)}",
    )
    report(
        "列表长度为任务数 3",
        len(result) == 3,
        f"len={len(result)}",
    )
    report(
        "列表元素为函数返回值（str），非 FunctionResultStatus",
        all(isinstance(r, str) for r in result),
        f"element_types={[type(r).__name__ for r in result]}",
    )
    report(
        "列表元素不是 FunctionResultStatus",
        not any(isinstance(r, FunctionResultStatus) for r in result),
        f"values={result}",
    )
    expected = {
        "/tmp/video.mp4.360p.mp4",
        "/tmp/video.mp4.720p.mp4",
        "/tmp/video.mp4.1080p.mp4",
    }
    report(
        "返回值内容正确",
        set(result) == expected,
        f"result={result}",
    )

    print(f"\n=== 最终结果: {'PASS' if PASS else 'FAIL'} ===")
    sys.stdout.flush()
    time.sleep(20)
    os._exit(66)
