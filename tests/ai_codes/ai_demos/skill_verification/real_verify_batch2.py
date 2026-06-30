"""验证 batch2 三个 Skill（RPC / Timing / Workflow）代码示例能否真实运行（MEMORY_QUEUE）"""
import os
import time
import sys
import inspect
from datetime import datetime, timedelta

os.environ["PYTHONPATH"] = r"D:\codes\funboost"
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = "real_verify_batch2_print.txt"
os.environ["SYS_STD_FILE_NAME"] = "real_verify_batch2_std.txt"

from funboost import boost, BoosterParams, BrokerEnum, ApsJobAdder
from funboost.core.msg_result_getter import AsyncResult
from funboost.core.function_result_status_saver import FunctionResultStatus
from funboost.workflow import chain, group, chord, WorkflowBoosterParams
from funboost.workflow import Chain, Group, Chord

PASS_COUNT = 0
FAIL_COUNT = 0
TIMING_EXEC = []
WF_EXEC = []


def ok(msg):
    global PASS_COUNT
    PASS_COUNT += 1
    print(f"[PASS] {msg}")


def fail(msg):
    global FAIL_COUNT
    FAIL_COUNT += 1
    print(f"[FAIL] {msg}")


# ========== Skill 1: funboost-rpc-mode ==========

@boost(
    BoosterParams(
        queue_name="real_verify_batch2_rpc_add",
        broker_kind=BrokerEnum.MEMORY_QUEUE,
        concurrent_num=5,
        is_using_rpc_mode=True,
        rpc_timeout=30,
    )
)
def rpc_add(x: int, y: int):
    result = x + y
    print(f"[EXEC] rpc_add({x}, {y}) = {result}")
    return result


def verify_rpc_mode():
    print("\n=== RPC 模式验证 ===")

    rpc_add.consume()
    time.sleep(2)

    async_result = rpc_add.push(3, 4)
    if isinstance(async_result, AsyncResult):
        ok("RPC: push 返回 AsyncResult")
    else:
        fail(f"RPC: push 应返回 AsyncResult，实际 {type(async_result).__name__}")

    if async_result.task_id:
        ok(f"RPC: AsyncResult.task_id 非空 ({async_result.task_id[:8]}...)")
    else:
        fail("RPC: AsyncResult.task_id 为空")

    try:
        result_val = async_result.result
        if result_val == 7:
            ok("RPC: async_result.result 返回 7")
        else:
            fail(f"RPC: async_result.result 期望 7，实际 {result_val!r}")
    except Exception as exc:
        fail(f"RPC: async_result.result 异常 {type(exc).__name__}: {exc}")

    status_dict = async_result.status_and_result
    if isinstance(status_dict, dict):
        ok("RPC: status_and_result 返回 dict")
        if status_dict.get("result") == 7:
            ok("RPC: status_and_result['result'] == 7")
        else:
            fail(f"RPC: status_and_result['result'] 错误: {status_dict.get('result')!r}")
        if status_dict.get("success") is True:
            ok("RPC: status_and_result['success'] is True")
        else:
            fail(f"RPC: status_and_result['success'] 错误: {status_dict.get('success')!r}")
    else:
        fail(f"RPC: status_and_result 应返回 dict，实际 {type(status_dict).__name__}")

    status_obj = async_result.status_and_result_obj
    if isinstance(status_obj, FunctionResultStatus):
        ok("RPC: status_and_result_obj 返回 FunctionResultStatus 对象")
        if status_obj.result == 7:
            ok("RPC: status_and_result_obj.result == 7")
        else:
            fail(f"RPC: status_and_result_obj.result 错误: {status_obj.result!r}")
        if status_obj.success is True:
            ok("RPC: status_and_result_obj.success is True")
        else:
            fail(f"RPC: status_and_result_obj.success 错误: {status_obj.success!r}")
    else:
        fail(f"RPC: status_and_result_obj 应返回 FunctionResultStatus，实际 {type(status_obj).__name__}")

    # SKILL: 根据 task_id 查询结果
    task_id = async_result.task_id
    result_obj = AsyncResult(task_id)
    queried = result_obj.status_and_result
    if isinstance(queried, dict) and queried.get("result") == 7:
        ok("RPC: AsyncResult(task_id).status_and_result 可查询历史结果")
    else:
        fail(f"RPC: AsyncResult(task_id) 查询失败: {queried!r}")


# ========== Skill 2: funboost-timing-jobs ==========

@boost(
    BoosterParams(
        queue_name="real_verify_batch2_timing",
        broker_kind=BrokerEnum.MEMORY_QUEUE,
        concurrent_num=3,
        qps=10,
    )
)
def cleanup_expired_data(table_name: str):
    TIMING_EXEC.append(table_name)
    print(f"[EXEC] cleanup_expired_data table_name={table_name}")
    return table_name


def verify_timing_jobs():
    print("\n=== Timing 定时任务验证 ===")

    if hasattr(sys.modules.get("funboost"), "ApsJobAdder") or ApsJobAdder:
        ok("Timing: ApsJobAdder 可 import")
    else:
        fail("Timing: ApsJobAdder import 失败")

    sig = inspect.signature(ApsJobAdder.__init__)
    default_store = sig.parameters["job_store_kind"].default
    if default_store == "memory":
        ok("Timing: ApsJobAdder 默认 job_store_kind='memory'")
    else:
        fail(f"Timing: job_store_kind 默认应为 'memory'，实际 {default_store!r}")

    cleanup_expired_data.consume()

    adder = ApsJobAdder(cleanup_expired_data)
    if adder.job_store_kind == "memory":
        ok("Timing: ApsJobAdder(func) 实例 job_store_kind='memory'")
    else:
        fail(f"Timing: 实例 job_store_kind 错误: {adder.job_store_kind!r}")

    try:
        adder.add_push_job(
            trigger="interval",
            seconds=30,
            kwargs={"table_name": "sessions"},
            id="batch2_cleanup_sessions",
            replace_existing=True,
        )
        ok("Timing: interval trigger 注册成功")
    except Exception as exc:
        fail(f"Timing: interval trigger 注册失败: {type(exc).__name__}: {exc}")

    try:
        adder.add_push_job(
            trigger="cron",
            hour=2,
            minute=0,
            kwargs={"table_name": "logs"},
            id="batch2_cleanup_logs_daily",
            replace_existing=True,
        )
        ok("Timing: cron trigger 注册成功")
    except Exception as exc:
        fail(f"Timing: cron trigger 注册失败: {type(exc).__name__}: {exc}")

    try:
        adder.add_push_job(
            trigger="date",
            run_date=datetime.now() + timedelta(hours=1),
            kwargs={"table_name": "once"},
            id="batch2_cleanup_once",
            replace_existing=True,
        )
        ok("Timing: date trigger 注册成功")
    except Exception as exc:
        fail(f"Timing: date trigger 注册失败: {type(exc).__name__}: {exc}")

    cleanup_expired_data.push("manual_verify")
    ok("Timing: 手动 push 发布成功")


# ========== Skill 3: funboost-workflow ==========

class WfParams(WorkflowBoosterParams):
    broker_kind: str = BrokerEnum.MEMORY_QUEUE
    concurrent_num: int = 5
    rpc_timeout: int = 30
    max_retry_times: int = 0


@boost(WfParams(queue_name="real_verify_batch2_wf_step"))
def wf_step(x: int) -> int:
    result = x + 1
    WF_EXEC.append(("wf_step", result))
    print(f"[EXEC] wf_step({x}) = {result}")
    return result


@boost(WfParams(queue_name="real_verify_batch2_wf_double"))
def wf_double(x: int) -> int:
    result = x * 2
    WF_EXEC.append(("wf_double", result))
    print(f"[EXEC] wf_double({x}) = {result}")
    return result


@boost(WfParams(queue_name="real_verify_batch2_wf_sum"))
def wf_sum_list(results: list, offset: int = 0) -> int:
    result = sum(results) + offset
    WF_EXEC.append(("wf_sum_list", result))
    print(f"[EXEC] wf_sum_list({results}, offset={offset}) = {result}")
    return result


def verify_workflow():
    print("\n=== Workflow 工作流验证 ===")

    for name in ("chain", "group", "chord", "WorkflowBoosterParams"):
        if name in globals():
            ok(f"Workflow: import {name} 成功")
        else:
            fail(f"Workflow: import {name} 失败")

    wf_step.consume()
    wf_double.consume()
    wf_sum_list.consume()
    ok("Workflow: 各任务 consume() 启动成功")
    time.sleep(2)

    wf_chain = chain(wf_step.s(1), wf_double.s())
    if isinstance(wf_chain, Chain):
        ok("Workflow: chain() 返回 Chain 实例")
    else:
        fail(f"Workflow: chain() 应返回 Chain，实际 {type(wf_chain).__name__}")

    try:
        chain_status = wf_chain.apply()
        if isinstance(chain_status, FunctionResultStatus) and chain_status.result == 4:
            ok("Workflow: chain.apply() 串行结果正确 (step(1)->2, double(2)->4)")
        else:
            fail(f"Workflow: chain.apply() 结果错误: {chain_status!r}")
    except Exception as exc:
        fail(f"Workflow: chain.apply() 异常: {type(exc).__name__}: {exc}")

    wf_group = group(wf_step.s(10), wf_step.s(20), wf_step.s(30))
    if isinstance(wf_group, Group):
        ok("Workflow: group() 返回 Group 实例")
    else:
        fail(f"Workflow: group() 应返回 Group，实际 {type(wf_group).__name__}")

    try:
        group_results = wf_group.apply()
        if group_results == [11, 21, 31]:
            ok(f"Workflow: group.apply() 结果正确: {group_results}")
        else:
            fail(f"Workflow: group.apply() 结果错误: {group_results!r}")
    except Exception as exc:
        fail(f"Workflow: group.apply() 异常: {type(exc).__name__}: {exc}")

    wf_chord = chord(
        group(wf_double.s(1), wf_double.s(2), wf_double.s(3)),
        wf_sum_list.s(offset=100),
    )
    if isinstance(wf_chord, Chord):
        ok("Workflow: chord() 返回 Chord 实例")
    else:
        fail(f"Workflow: chord() 应返回 Chord，实际 {type(wf_chord).__name__}")

    try:
        chord_status = wf_chord.apply()
        if isinstance(chord_status, FunctionResultStatus) and chord_status.result == 112:
            ok("Workflow: chord.apply() 聚合结果正确 (sum([2,4,6])+100=112)")
        else:
            fail(f"Workflow: chord.apply() 结果错误: {chord_status!r}")
    except Exception as exc:
        fail(f"Workflow: chord.apply() 异常: {type(exc).__name__}: {exc}")


def verify_post_consume():
    """等待消费完成后检查 timing 手动 push 是否被执行"""
    time.sleep(6)

    if "manual_verify" in TIMING_EXEC:
        ok("Timing: cleanup_expired_data 消费了手动 push 消息")
    else:
        fail(f"Timing: 手动 push 未被消费，TIMING_EXEC={TIMING_EXEC}")


if __name__ == "__main__":
    print("=== real_verify_batch2: Skill 代码示例运行时验证 ===")

    verify_rpc_mode()
    verify_timing_jobs()
    verify_workflow()
    verify_post_consume()

    print(f"\n=== 汇总: PASS={PASS_COUNT}, FAIL={FAIL_COUNT} ===")
    time.sleep(15)
    os._exit(66)
