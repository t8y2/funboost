"""Round2 验证 funboost-workflow SKILL — import 路径与 .s()/.si() 需导入 workflow 模块"""
import os
import sys
import time

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
_ts = int(time.time())
os.environ["PRINT_WRTIE_FILE_NAME"] = f"r2_wf_07_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"r2_wf_07_std_{_ts}"

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

# SKILL: from funboost.workflow import chain, group, chord, WorkflowBoosterParams
try:
    from funboost.workflow import chain, group, chord, WorkflowBoosterParams
    report("from funboost.workflow import chain, group, chord, WorkflowBoosterParams", True)
except Exception as e:
    report("workflow imports", False, str(e))
    time.sleep(20)
    os._exit(66)


class WfParams(WorkflowBoosterParams):
    broker_kind: str = BrokerEnum.MEMORY_QUEUE
    concurrent_num: int = 5
    max_retry_times: int = 0
    rpc_timeout: int = 30


@boost(WfParams(queue_name=f"r2b_wf_sig_{_ts}"))
def wf_task(x: int):
    return x + 1


if __name__ == "__main__":
    report("chain 是可调用", callable(chain))
    report("group 是可调用", callable(group))
    report("chord 是可调用", callable(chord))

    report("wf_task 有 .s 方法", hasattr(wf_task, "s") and callable(wf_task.s))
    report("wf_task 有 .si 方法", hasattr(wf_task, "si") and callable(wf_task.si))

    sig = wf_task.s(10)
    report("func.s(*args) 创建签名对象", sig is not None, f"type={type(sig).__name__}")

    sig_i = wf_task.si(99)
    report("func.si(*args) 创建不可变签名", sig_i is not None, f"type={type(sig_i).__name__}")

    # WorkflowBoosterParams 默认 is_using_rpc_mode=True
    params = WfParams(queue_name="test_default")
    report(
        "SKILL: WorkflowBoosterParams 默认 is_using_rpc_mode=True",
        params.is_using_rpc_mode is True,
        f"is_using_rpc_mode={params.is_using_rpc_mode}",
    )

    print(f"\n=== 最终结果: {'PASS' if PASS else 'FAIL'} ===")
    sys.stdout.flush()
    time.sleep(20)
    os._exit(66)
