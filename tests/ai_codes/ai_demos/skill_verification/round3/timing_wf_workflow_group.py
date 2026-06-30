"""验证 funboost-workflow SKILL — Group 并行执行"""
import os
import time

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
_ts = int(time.time())
os.environ["PRINT_WRTIE_FILE_NAME"] = f"timing_wf_workflow_group_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"timing_wf_workflow_group_std_{_ts}"

from funboost import boost, BrokerEnum
from funboost.workflow import group, WorkflowBoosterParams


class WfParams(WorkflowBoosterParams):
    broker_kind: str = BrokerEnum.MEMORY_QUEUE
    concurrent_num: int = 5
    max_retry_times: int = 0
    rpc_timeout: int = 30


@boost(WfParams(queue_name="r3_wf_group_process"))
def process(file_path: str, resolution: str = "720p"):
    print(f"处理 {file_path}，分辨率 {resolution}")
    return f"{file_path}.{resolution}.mp4"


if __name__ == "__main__":
    print("[START] timing_wf_workflow_group")
    process.consume()
    time.sleep(2)

    parallel_tasks = group(
        process.s("/tmp/video.mp4", resolution="360p"),
        process.s("/tmp/video.mp4", resolution="720p"),
        process.s("/tmp/video.mp4", resolution="1080p"),
    )
    result = parallel_tasks.apply()
    assert isinstance(result, list) and len(result) == 3, f"group 应返回 3 项列表，实际 {result!r}"
    print(f"[OK] group.apply() result={result}")

    time.sleep(20)
    print("[DONE] timing_wf_workflow_group")
    os._exit(66)
