"""验证 funboost-workflow SKILL — Chain 串行流水线"""
import os
import time

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
_ts = int(time.time())
os.environ["PRINT_WRTIE_FILE_NAME"] = f"timing_wf_workflow_chain_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"timing_wf_workflow_chain_std_{_ts}"

from funboost import boost, BrokerEnum
from funboost.workflow import chain, WorkflowBoosterParams
from funboost.core.function_result_status_saver import FunctionResultStatus


class WfParams(WorkflowBoosterParams):
    broker_kind: str = BrokerEnum.MEMORY_QUEUE
    concurrent_num: int = 5
    max_retry_times: int = 0
    rpc_timeout: int = 30


@boost(WfParams(queue_name="r3_wf_chain_download"))
def download(url: str):
    print(f"下载 {url}")
    return f"/tmp/{url.split('/')[-1]}"


@boost(WfParams(queue_name="r3_wf_chain_process"))
def process(file_path: str, resolution: str = "720p"):
    print(f"处理 {file_path}，分辨率 {resolution}")
    return f"{file_path}.{resolution}.mp4"


if __name__ == "__main__":
    print("[START] timing_wf_workflow_chain")
    download.consume()
    process.consume()
    time.sleep(2)

    workflow = chain(
        download.s("https://example.com/video.mp4"),
        process.s(resolution="1080p"),
    )
    result = workflow.apply()
    assert isinstance(result, FunctionResultStatus), f"apply() 应返回 FunctionResultStatus，实际 {type(result)}"
    print(f"[OK] chain.apply() result={result.result}")

    time.sleep(20)
    print("[DONE] timing_wf_workflow_chain")
    os._exit(66)
