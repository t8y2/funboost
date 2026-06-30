"""Round2 验证 funboost-workflow SKILL — 嵌套 chain+chord.apply() 返回 FunctionResultStatus"""
import os
import sys
import time

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
_ts = int(time.time())
os.environ["PRINT_WRTIE_FILE_NAME"] = f"r2_wf_11_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"r2_wf_11_std_{_ts}"

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
from funboost.workflow import chain, group, chord, WorkflowBoosterParams
from funboost.core.function_result_status_saver import FunctionResultStatus


class WfParams(WorkflowBoosterParams):
    broker_kind: str = BrokerEnum.MEMORY_QUEUE
    concurrent_num: int = 5
    max_retry_times: int = 0
    rpc_timeout: int = 30


@boost(WfParams(queue_name=f"r2b_wf_nested_dl_{_ts}"))
def download(url: str):
    return f"/tmp/{url.split('/')[-1]}"


@boost(WfParams(queue_name=f"r2b_wf_nested_proc_{_ts}"))
def process(file_path: str, resolution: str = "720p"):
    return f"{file_path}.{resolution}.mp4"


@boost(WfParams(queue_name=f"r2b_wf_nested_notify_{_ts}"))
def notify(results: list, user_id: int):
    return f"nested:{user_id}:{len(results)}"


if __name__ == "__main__":
    download.consume()
    process.consume()
    notify.consume()
    time.sleep(2)

    workflow = chain(
        download.s("https://example.com/video.mp4"),
        chord(
            group(process.s(resolution=r) for r in ["360p", "720p", "1080p"]),
            notify.s(user_id=1001),
        ),
    )
    result = workflow.apply()

    report(
        "嵌套 chain+chord apply() 返回 FunctionResultStatus",
        isinstance(result, FunctionResultStatus),
        f"type={type(result).__name__}",
    )
    report(
        "最终 .result 为 notify 返回值",
        result.result == "nested:1001:3",
        f"result.result={result.result!r}",
    )

    print(f"\n=== 最终结果: {'PASS' if PASS else 'FAIL'} ===")
    sys.stdout.flush()
    time.sleep(20)
    os._exit(66)
