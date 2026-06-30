"""验证 funboost-workflow SKILL — 复杂嵌套 chain + chord 流水线"""
import os
import time

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
_ts = int(time.time())
os.environ["PRINT_WRTIE_FILE_NAME"] = f"timing_wf_workflow_nested_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"timing_wf_workflow_nested_std_{_ts}"

from funboost import boost, BrokerEnum
from funboost.workflow import chain, group, chord, WorkflowBoosterParams
from funboost.core.function_result_status_saver import FunctionResultStatus


class WfParams(WorkflowBoosterParams):
    broker_kind: str = BrokerEnum.MEMORY_QUEUE
    concurrent_num: int = 5
    max_retry_times: int = 0
    rpc_timeout: int = 30


@boost(WfParams(queue_name="r3_wf_nested_download"))
def download(url: str):
    print(f"下载 {url}")
    return f"/tmp/{url.split('/')[-1]}"


@boost(WfParams(queue_name="r3_wf_nested_process"))
def process(file_path: str, resolution: str = "720p"):
    print(f"处理 {file_path}，分辨率 {resolution}")
    return f"{file_path}.{resolution}.mp4"


@boost(WfParams(queue_name="r3_wf_nested_notify"))
def notify(results: list, user_id: int):
    print(f"通知用户 {user_id}：{len(results)} 个文件已就绪")
    return "done"


if __name__ == "__main__":
    print("[START] timing_wf_workflow_nested")
    download.consume()
    process.consume()
    notify.consume()
    time.sleep(2)

    workflow = chain(
        download.s("https://example.com/video.mp4"),
        chord(
            group(
                process.s(resolution=r)
                for r in ["360p", "720p", "1080p"]
            ),
            notify.s(user_id=1001),
        ),
    )
    result = workflow.apply()
    assert isinstance(result, FunctionResultStatus) and result.result == "done", f"嵌套 workflow 结果错误: {result!r}"
    print(f"[OK] nested chain+chord.apply() result={result.result}")

    time.sleep(20)
    print("[DONE] timing_wf_workflow_nested")
    os._exit(66)
