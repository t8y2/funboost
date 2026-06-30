"""第2轮深度验证A：消息真的被消费了吗？函数真的执行了吗？（MEMORY_QUEUE）"""
import os
import time
import sys
import threading

os.environ["PYTHONPATH"] = r"D:\codes\funboost"
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = "real_verify_r2a_print.txt"
os.environ["SYS_STD_FILE_NAME"] = "real_verify_r2a_std.txt"
sys.path.insert(0, r"D:\codes\funboost")

from funboost import boost, BoosterParams, BrokerEnum
from funboost.consumers.base_consumer import AbstractConsumer
from funboost.core.function_result_status_saver import FunctionResultStatus
from funboost.workflow import chain, WorkflowBoosterParams

_TS = int(time.time())
PASS_COUNT = 0
FAIL_COUNT = 0


def _pass(msg):
    global PASS_COUNT
    PASS_COUNT += 1
    print(f"[PASS] {msg}")


def _fail(msg):
    global FAIL_COUNT
    FAIL_COUNT += 1
    print(f"[FAIL] {msg}")


# ========== 场景1：基础 push + consume ==========

results = []


@boost(
    BoosterParams(
        queue_name=f"real_verify_r2a_add_{_TS}",
        broker_kind=BrokerEnum.MEMORY_QUEUE,
        concurrent_num=1,
    )
)
def add_task(a, b):
    results.append(a + b)
    print(f"[EXEC] add_task({a}, {b}) -> {a + b}")


def scenario1_basic_consume():
    print("\n=== 场景1：基础 push + consume ===")
    add_task.push(1, 2)
    add_task.push(3, 4)
    add_task.push(5, 6)
    add_task.consume()
    time.sleep(12)
    if results == [3, 7, 11]:
        _pass(f"基础消费: results={results}")
    else:
        _fail(f"基础消费: 期望 [3, 7, 11]，实际 results={results}")


# ========== 场景2：RPC 模式 ==========


@boost(
    BoosterParams(
        queue_name=f"real_verify_r2a_rpc_{_TS}",
        broker_kind=BrokerEnum.MEMORY_QUEUE,
        concurrent_num=5,
        is_using_rpc_mode=True,
        rpc_timeout=30,
    )
)
def multiply(a, b):
    result = a * b
    print(f"[EXEC] multiply({a}, {b}) -> {result}")
    return result


def scenario2_rpc_mode():
    print("\n=== 场景2：RPC 模式 ===")
    multiply.consume()
    time.sleep(2)
    async_result = multiply.push(3, 7)
    time.sleep(10)
    try:
        rpc_val = async_result.result
        if rpc_val == 21:
            _pass(f"RPC 结果: {async_result.result}")
        else:
            _fail(f"RPC 结果: 期望 21，实际 {async_result.result!r}")
    except Exception as exc:
        _fail(f"RPC 结果: async_result.result 异常 {type(exc).__name__}: {exc}")


# ========== 场景3：高级重试 ==========

retry_count = [0]


@boost(
    BoosterParams(
        queue_name=f"real_verify_r2a_retry_{_TS}",
        broker_kind=BrokerEnum.MEMORY_QUEUE,
        max_retry_times=5,
        concurrent_num=1,
    )
)
def flaky_task(x):
    retry_count[0] += 1
    print(f"[EXEC] flaky_task x={x}, retry_count={retry_count[0]}")
    if retry_count[0] < 3:
        raise ValueError(f"模拟失败 retry_count={retry_count[0]}")
    return x


def scenario3_retry():
    print("\n=== 场景3：高级重试 ===")
    flaky_task.push(1)
    flaky_task.consume()
    time.sleep(12)
    if retry_count[0] >= 3:
        _pass(f"重试: retry_count={retry_count[0]}")
    else:
        _fail(f"重试: 期望 retry_count>=3，实际 retry_count={retry_count[0]}")


# ========== 场景4：workflow chain ==========


class WfParams(WorkflowBoosterParams):
    broker_kind: str = BrokerEnum.MEMORY_QUEUE
    concurrent_num: int = 5
    rpc_timeout: int = 30
    max_retry_times: int = 0


@boost(WfParams(queue_name=f"real_verify_r2a_step1_{_TS}"))
def step1(x):
    result = x + 10
    print(f"[EXEC] step1({x}) -> {result}")
    return result


@boost(WfParams(queue_name=f"real_verify_r2a_step2_{_TS}"))
def step2(x):
    result = x * 2
    print(f"[EXEC] step2({x}) -> {result}")
    return result


def scenario4_workflow_chain():
    print("\n=== 场景4：workflow chain ===")
    step1.consume()
    step2.consume()
    time.sleep(2)
    try:
        chain_status = chain(step1.s(5), step2.s()).apply()
        if isinstance(chain_status, FunctionResultStatus) and chain_status.result == 30:
            _pass(f"workflow chain 结果: {chain_status.result}")
        else:
            got = getattr(chain_status, "result", chain_status)
            _fail(f"workflow chain 结果: 期望 30，实际 {got!r}")
    except Exception as exc:
        _fail(f"workflow chain 异常: {type(exc).__name__}: {exc}")


# ========== 场景5：Mixin 钩子 ==========

hook_calls = []


class HookVerifyMixin(AbstractConsumer):
    def _both_sync_and_aio_frame_custom_record_process_info_func(
        self, current_function_result_status, kw
    ):
        super()._both_sync_and_aio_frame_custom_record_process_info_func(
            current_function_result_status, kw
        )
        hook_calls.append(
            {
                "success": current_function_result_status.success,
                "kw": kw,
            }
        )


@boost(
    BoosterParams(
        queue_name=f"real_verify_r2a_mixin_{_TS}",
        broker_kind=BrokerEnum.MEMORY_QUEUE,
        consumer_override_cls=HookVerifyMixin,
        concurrent_num=2,
    )
)
def mixin_hook_task(x):
    print(f"[EXEC] mixin_hook_task x={x}")
    return x * 2


def scenario5_mixin_hook():
    print("\n=== 场景5：Mixin 钩子 ===")
    mixin_hook_task.push(1)
    mixin_hook_task.push(2)
    mixin_hook_task.consume()
    time.sleep(12)
    if len(hook_calls) == 2:
        _pass(f"Mixin 钩子被调用 {len(hook_calls)} 次")
    else:
        _fail(f"Mixin 钩子: 期望 2 次，实际 {len(hook_calls)} 次, hook_calls={hook_calls}")


if __name__ == "__main__":
    print("=== real_verify_round2a: 第2轮深度验证A ===")

    scenario1_basic_consume()
    scenario2_rpc_mode()
    scenario3_retry()
    scenario4_workflow_chain()
    scenario5_mixin_hook()

    print(f"\n=== 第2轮A汇总: PASS={PASS_COUNT}, FAIL={FAIL_COUNT} ===")
    os._exit(66)
