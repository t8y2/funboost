"""验证 funboost-workflow SKILL — 核心任务定义（WorkflowBoosterParams + 三任务声明）"""
import os
import time

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
_ts = int(time.time())
os.environ["PRINT_WRTIE_FILE_NAME"] = f"timing_wf_workflow_task_definitions_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"timing_wf_workflow_task_definitions_std_{_ts}"

from funboost import boost, BrokerEnum
from funboost.workflow import chain, group, chord, WorkflowBoosterParams


class WfParams(WorkflowBoosterParams):
    broker_kind: str = BrokerEnum.MEMORY_QUEUE
    concurrent_num: int = 5
    max_retry_times: int = 0
    rpc_timeout: int = 30


@boost(WfParams(queue_name="r3_download_queue"))
def download(url: str):
    print(f"下载 {url}")
    return f"/tmp/{url.split('/')[-1]}"


@boost(WfParams(queue_name="r3_process_queue"))
def process(file_path: str, resolution: str = "720p"):
    print(f"处理 {file_path}，分辨率 {resolution}")
    return f"{file_path}.{resolution}.mp4"


@boost(WfParams(queue_name="r3_notify_queue"))
def notify(results: list, user_id: int):
    print(f"通知用户 {user_id}：{len(results)} 个文件已就绪")
    return "done"


if __name__ == "__main__":
    print("[START] timing_wf_workflow_task_definitions")
    for fn in (download, process, notify):
        assert hasattr(fn, "s") and callable(fn.s), f"{fn.queue_name} 缺少 .s()"
        assert hasattr(fn, "si") and callable(fn.si), f"{fn.queue_name} 缺少 .si()"
    print("[OK] 三任务定义 + .s()/.si() 可用")
    print(f"[OK] WorkflowBoosterParams is_using_rpc_mode={WfParams(queue_name='x').is_using_rpc_mode}")

    time.sleep(20)
    print("[DONE] timing_wf_workflow_task_definitions")
    os._exit(66)
