"""Round2 验证 funboost-workflow SKILL — chord.apply() 返回 FunctionResultStatus"""
import os
import sys
import time

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
_ts = int(time.time())
os.environ["PRINT_WRTIE_FILE_NAME"] = f"r2_wf_10_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"r2_wf_10_std_{_ts}"

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
from funboost.workflow import group, chord, WorkflowBoosterParams
from funboost.core.function_result_status_saver import FunctionResultStatus


class WfParams(WorkflowBoosterParams):
    broker_kind: str = BrokerEnum.MEMORY_QUEUE
    concurrent_num: int = 5
    max_retry_times: int = 0
    rpc_timeout: int = 30


@boost(WfParams(queue_name=f"r2b_wf_chord_proc_{_ts}"))
def process(file_path: str, resolution: str = "720p"):
    return f"{file_path}.{resolution}.mp4"


@boost(WfParams(queue_name=f"r2b_wf_chord_notify_{_ts}"))
def notify(results: list, user_id: int):
    return f"done:{user_id}:{len(results)}"


if __name__ == "__main__":
    process.consume()
    notify.consume()
    time.sleep(2)

    workflow = chord(
        group(
            process.s("/tmp/v.mp4", resolution=r)
            for r in ["360p", "720p", "1080p"]
        ),
        notify.s(user_id=1001),
    )
    result = workflow.apply()

    report(
        "SKILL: chord.apply() 返回 FunctionResultStatus",
        isinstance(result, FunctionResultStatus),
        f"type={type(result).__name__}",
    )
    report(
        "callback 收到 group 结果列表并聚合",
        result.result == "done:1001:3",
        f"result.result={result.result!r}",
    )
    report(
        "FunctionResultStatus.success 为 True",
        result.success is True,
        f"success={result.success}",
    )

    print(f"\n=== 最终结果: {'PASS' if PASS else 'FAIL'} ===")
    sys.stdout.flush()
    time.sleep(20)
    os._exit(66)
