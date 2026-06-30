"""Round2 验证 funboost-workflow SKILL — chain.apply() 返回 FunctionResultStatus"""
import os
import sys
import time

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
_ts = int(time.time())
os.environ["PRINT_WRTIE_FILE_NAME"] = f"r2_wf_08_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"r2_wf_08_std_{_ts}"

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
from funboost.workflow import chain, WorkflowBoosterParams
from funboost.core.function_result_status_saver import FunctionResultStatus


class WfParams(WorkflowBoosterParams):
    broker_kind: str = BrokerEnum.MEMORY_QUEUE
    concurrent_num: int = 5
    max_retry_times: int = 0
    rpc_timeout: int = 30


@boost(WfParams(queue_name=f"r2b_wf_chain_dl_{_ts}"))
def download(url: str):
    return f"/tmp/{url.split('/')[-1]}"


@boost(WfParams(queue_name=f"r2b_wf_chain_proc_{_ts}"))
def process(file_path: str, resolution: str = "720p"):
    return f"{file_path}.{resolution}.mp4"


if __name__ == "__main__":
    download.consume()
    process.consume()
    time.sleep(2)

    workflow = chain(
        download.s("https://example.com/video.mp4"),
        process.s(resolution="1080p"),
    )
    result = workflow.apply()

    report(
        "SKILL: chain.apply() 返回 FunctionResultStatus（非直接值）",
        isinstance(result, FunctionResultStatus),
        f"type={type(result).__name__}",
    )
    report(
        "通过 .result 属性取实际返回值",
        result.result == "/tmp/video.mp4.1080p.mp4",
        f"result.result={result.result!r}",
    )
    report(
        "FunctionResultStatus 有 success 属性",
        result.success is True,
        f"success={result.success}",
    )

    print(f"\n=== 最终结果: {'PASS' if PASS else 'FAIL'} ===")
    sys.stdout.flush()
    time.sleep(20)
    os._exit(66)
