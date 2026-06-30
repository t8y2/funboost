"""验证 funboost-workflow SKILL.md 的技术准确性（r1）"""
import inspect
import os
import time

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
_ts = int(time.time())
os.environ["PRINT_WRTIE_FILE_NAME"] = f"verify_workflow_r1_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"verify_workflow_r1_std_{_ts}"

from funboost import boost, BrokerEnum
from funboost.workflow import chain, group, chord, WorkflowBoosterParams
from funboost.workflow import Chain, Group, Chord, Signature
from funboost.workflow.workflow_mixin import WorkflowConsumerMixin, WorkflowPublisherMixin
from funboost.core.function_result_status_saver import FunctionResultStatus

PASS = []
FAIL = []


def ok(msg):
    PASS.append(msg)
    print(f"[PASS] {msg}")


def fail(msg):
    FAIL.append(msg)
    print(f"[FAIL] {msg}")


def check_static_imports_and_api():
    """核对 SKILL 描述的导入与 API 是否存在"""
    for name in ("chain", "group", "chord", "WorkflowBoosterParams"):
        obj = globals().get(name)
        if obj is not None and callable(obj if name != "WorkflowBoosterParams" else obj):
            ok(f"from funboost.workflow import {name} 成功")
        else:
            fail(f"funboost.workflow 未导出 {name}")

    for cls_name, cls in (("Chain", Chain), ("Group", Group), ("Chord", Chord)):
        if hasattr(cls, "apply") and callable(cls.apply):
            ok(f"{cls_name}.apply() 方法存在")
        else:
            fail(f"{cls_name} 缺少 apply()")

    if callable(chain) and callable(group) and callable(chord):
        ok("chain/group/chord 便捷函数可调用")
    else:
        fail("chain/group/chord 便捷函数不可调用")


def check_workflow_booster_params():
    """核对 WorkflowBoosterParams 默认配置（SKILL 注意事项第 1 条）"""
    params = WorkflowBoosterParams(queue_name="__wf_defaults_check__")
    if params.is_using_rpc_mode is True:
        ok("WorkflowBoosterParams.is_using_rpc_mode 默认 True")
    else:
        fail(f"WorkflowBoosterParams.is_using_rpc_mode 默认应为 True，实际 {params.is_using_rpc_mode}")

    if params.consumer_override_cls is WorkflowConsumerMixin:
        ok("WorkflowBoosterParams 默认注入 WorkflowConsumerMixin")
    else:
        fail(f"consumer_override_cls 错误: {params.consumer_override_cls}")

    if params.publisher_override_cls is WorkflowPublisherMixin:
        ok("WorkflowBoosterParams 默认注入 WorkflowPublisherMixin")
    else:
        fail(f"publisher_override_cls 错误: {params.publisher_override_cls}")


def check_signature_methods(booster_obj):
    """核对 .s() / .si() 方法（导入 workflow 后自动挂载到 Booster）"""
    if hasattr(booster_obj, "s") and callable(booster_obj.s):
        ok("Booster.s() 方法存在（需 import funboost.workflow 后）")
    else:
        fail("Booster.s() 方法不存在")

    if hasattr(booster_obj, "si") and callable(booster_obj.si):
        ok("Booster.si() 方法存在")
    else:
        fail("Booster.si() 方法不存在")

    sig = booster_obj.s(1, tag="a")
    if isinstance(sig, Signature) and sig.args == (1,) and sig.kwargs == {"tag": "a"} and sig.immutable is False:
        ok("func.s(*args, **kwargs) 创建 Signature 且 immutable=False")
    else:
        fail(f"func.s() 行为不符: {sig!r}")

    sig_i = booster_obj.si(99)
    if isinstance(sig_i, Signature) and sig_i.args == (99,) and sig_i.immutable is True:
        ok("func.si(*args) 创建不可变 Signature（immutable=True）")
    else:
        fail(f"func.si() 行为不符: {sig_i!r}")


class WfParams(WorkflowBoosterParams):
    broker_kind: str = BrokerEnum.REDIS_ACK_ABLE
    concurrent_num: int = 5
    max_retry_times: int = 0
    rpc_timeout: int = 30


@boost(WfParams(queue_name="verify_wf_r1_step"))
def step(x: int) -> int:
    return x + 1


@boost(WfParams(queue_name="verify_wf_r1_double"))
def double_val(x: int) -> int:
    return x * 2


@boost(WfParams(queue_name="verify_wf_r1_add_fixed"))
def add_fixed(base: int) -> int:
    return base + 10


@boost(WfParams(queue_name="verify_wf_r1_mul_by"))
def mul_by(x: int, factor: int) -> int:
    return x * factor


@boost(WfParams(queue_name="verify_wf_r1_sum_list"))
def sum_list(results: list, offset: int = 0) -> int:
    return sum(results) + offset


def run_workflow_runtime_checks():
    """运行 chain / group / chord / apply() 端到端验证"""
    step.consume()
    double_val.consume()
    add_fixed.consume()
    mul_by.consume()
    sum_list.consume()
    ok("各工作流任务 consume() 启动成功")
    time.sleep(2)

    # chain: 上游结果传给下游第一个参数
    wf_chain = chain(step.s(1), double_val.s())
    if not isinstance(wf_chain, Chain):
        fail(f"chain() 应返回 Chain，实际 {type(wf_chain)}")
    else:
        ok("chain() 返回 Chain 实例")

    chain_status = wf_chain.apply()
    if isinstance(chain_status, FunctionResultStatus) and chain_status.result == 4:
        ok("chain.apply() 串行传递结果: step(1)->2, double(2)->4")
    else:
        fail(f"chain.apply() 结果错误: {chain_status!r}")

    # group: 并行执行，返回 list
    wf_group = group(step.s(10), step.s(20), step.s(30))
    if not isinstance(wf_group, Group):
        fail(f"group() 应返回 Group，实际 {type(wf_group)}")
    else:
        ok("group() 返回 Group 实例")

    group_results = wf_group.apply()
    if group_results == [11, 21, 31]:
        ok(f"group.apply() 返回结果列表: {group_results}")
    else:
        fail(f"group.apply() 结果错误: {group_results}")

    # group 生成器语法（SKILL chord 示例）
    wf_group_gen = group(step.s(i) for i in (1, 2, 3))
    gen_results = wf_group_gen.apply()
    if gen_results == [2, 3, 4]:
        ok("group(task.s(i) for i in ...) 生成器语法可用")
    else:
        fail(f"group 生成器语法结果错误: {gen_results}")

    # .si() 忽略上游结果
    wf_si = chain(step.s(5), add_fixed.si(base=100))
    si_status = wf_si.apply()
    if isinstance(si_status, FunctionResultStatus) and si_status.result == 110:
        ok("chain 中 .si() 忽略上游结果，仅用签名参数")
    else:
        fail(f".si() chain 结果错误: {si_status!r}")

    # chord: group 结果列表传给 callback 第一个参数
    wf_chord = chord(
        group(double_val.s(1), double_val.s(2), double_val.s(3)),
        sum_list.s(offset=100),
    )
    if not isinstance(wf_chord, Chord):
        fail(f"chord() 应返回 Chord，实际 {type(wf_chord)}")
    else:
        ok("chord() 返回 Chord 实例")

    chord_status = wf_chord.apply()
    # double: [2,4,6] -> sum=12 + offset 100 = 112
    if isinstance(chord_status, FunctionResultStatus) and chord_status.result == 112:
        ok("chord.apply() 聚合 group 结果并传给 callback")
    else:
        fail(f"chord.apply() 结果错误: {chord_status!r}")

    # 嵌套 chain + chord（SKILL 复杂嵌套流水线模式）
    wf_nested = chain(
        step.s(0),
        chord(
            group(mul_by.s(factor=2), mul_by.s(factor=3)),
            sum_list.s(offset=0),
        ),
    )
    nested_status = wf_nested.apply()
    # step(0)->1; chord header: mul_by(1,f=2)->2, mul_by(1,f=3)->3; sum=5
    if isinstance(nested_status, FunctionResultStatus) and nested_status.result == 5:
        ok("chain 嵌套 chord 流水线 apply() 成功")
    else:
        fail(f"嵌套 chain+chord 结果错误: {nested_status!r}")


if __name__ == "__main__":
    print("=== 静态校验 ===")
    check_static_imports_and_api()
    check_workflow_booster_params()
    check_signature_methods(step)

    print("\n=== 运行时工作流验证 ===")
    try:
        run_workflow_runtime_checks()
    except Exception as exc:
        fail(f"运行时验证异常: {type(exc).__name__}: {exc}")

    time.sleep(2)
    print(f"\n=== 汇总: PASS={len(PASS)}, FAIL={len(FAIL)} ===")
    if FAIL:
        for item in FAIL:
            print(f"  FAIL: {item}")
        os._exit(1)
    print("[DONE] verify_workflow_r1 全部通过")
    os._exit(66)
