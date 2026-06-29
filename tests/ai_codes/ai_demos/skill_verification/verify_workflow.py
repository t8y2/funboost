"""验证 funboost-workflow skill 中的代码示例"""
import os
import time

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"verify_workflow_{int(time.time())}"
os.environ["SYS_STD_FILE_NAME"] = f"verify_workflow_std_{int(time.time())}"

from funboost import boost, BoosterParams, BrokerEnum
from funboost.workflow import chain, group, chord, WorkflowBoosterParams


@boost(BoosterParams(
    queue_name="wf_step_a",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    is_using_rpc_mode=True,
    concurrent_num=5,
))
def step_a(url: str):
    print(f"[OK] step_a 下载 url={url}")
    return f"data_from_{url}"


@boost(BoosterParams(
    queue_name="wf_step_b",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    is_using_rpc_mode=True,
    concurrent_num=5,
))
def step_b(data: str, resolution: str = "720p"):
    print(f"[OK] step_b 处理 data={data}, resolution={resolution}")
    return f"processed_{data}_{resolution}"


@boost(BoosterParams(
    queue_name="wf_step_c",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    is_using_rpc_mode=True,
    concurrent_num=5,
))
def step_c(results: list):
    print(f"[OK] step_c 汇总 results={results}")
    return f"final_report_{len(results)}_items"


if __name__ == "__main__":
    # 启动所有消费者
    step_a.consume()
    step_b.consume()
    step_c.consume()

    time.sleep(2)

    # 验证1: chain (顺序执行)
    print("--- 测试 chain ---")
    wf_chain = chain(
        step_a.s("http://example.com/video.mp4"),
        step_b.s(resolution="1080p"),
    )
    chain_result = wf_chain.apply()
    print(f"[OK] chain 结果: {chain_result}")

    # 验证2: group (并行执行)
    print("--- 测试 group ---")
    wf_group = group(
        step_b.s("raw_data_1", resolution="360p"),
        step_b.s("raw_data_2", resolution="720p"),
        step_b.s("raw_data_3", resolution="1080p"),
    )
    group_result = wf_group.apply()
    print(f"[OK] group 结果: {group_result}")

    # 验证3: chord (并行 + 回调汇总)
    print("--- 测试 chord ---")
    wf_chord = chord(
        group(
            step_b.s("video_a", resolution="480p"),
            step_b.s("video_b", resolution="720p"),
        ),
        step_c.s(),
    )
    chord_result = wf_chord.apply()
    print(f"[OK] chord 结果: {chord_result}")

    time.sleep(8)
    print("[DONE] verify_workflow 完成")
    os._exit(66)
