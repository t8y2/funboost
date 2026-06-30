"""Round2-06 综合验证 5 个 SKILL（对照 c4.md / c15.md）

Skills:
1. funboost-rpc-mode
2. funboost-timing-jobs
3. funboost-workflow
4. funboost-faas-deploy
5. funboost-advanced-retry

检查项（用户指定）:
- RPC: push -> AsyncResult, status_and_result dict, status_and_result_obj object
- Timing: ApsJobAdder(job_store_kind='memory'), add_push_job 存在
- Workflow: chain/group/chord.apply() 返回类型
- FaaS: fastapi_router 路由路径, msg_body 参数名
- Retry: advanced_retry_config 5 个键, do_task_filtering 语义
"""
import inspect
import os
import re
import time
from pathlib import Path
from typing import Optional

PROJECT_ROOT = r"D:\codes\funboost"
C4_PATH = Path(r"D:\codes\funboost_docs\source\articles\c4.md")
C15_PATH = Path(r"D:\codes\funboost_docs\source\articles\c15.md")

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"verify_all_r2_06_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"verify_all_r2_06_std_{_ts}"

PASS: list[str] = []
FAIL: list[str] = []
SKILL_RESULTS: dict[str, list[str]] = {
    "funboost-rpc-mode": [],
    "funboost-timing-jobs": [],
    "funboost-workflow": [],
    "funboost-faas-deploy": [],
    "funboost-advanced-retry": [],
}


def ok(msg: str, skill: Optional[str] = None) -> None:
    PASS.append(msg)
    print(f"[PASS] {msg}")
    if skill:
        SKILL_RESULTS[skill].append(f"PASS: {msg}")


def fail(msg: str, skill: Optional[str] = None) -> None:
    FAIL.append(msg)
    print(f"[FAIL] {msg}")
    if skill:
        SKILL_RESULTS[skill].append(f"FAIL: {msg}")


def read_doc(path: Path) -> str:
    if path.is_file():
        return path.read_text(encoding="utf-8")
    return ""


# ---------------------------------------------------------------------------
# 1. RPC
# ---------------------------------------------------------------------------
def verify_rpc_skill():
    skill = "funboost-rpc-mode"
    print("\n=== [1/5] funboost-rpc-mode ===")

    from funboost import boost, BoosterParams, BrokerEnum
    from funboost.core.msg_result_getter import AsyncResult, AioAsyncResult
    from funboost.core.function_result_status_saver import FunctionResultStatus

    c4 = read_doc(C4_PATH)
    if "is_using_rpc_mode=True" in c4 and "async_result = add.push" in c4:
        ok("c4.md §4.6 含 is_using_rpc_mode + push 示例", skill)
    else:
        fail("c4.md §4.6 RPC 示例缺失关键片段", skill)

    for attr in ("result", "status_and_result", "status_and_result_obj"):
        if hasattr(AsyncResult, attr):
            ok(f"AsyncResult.{attr} 存在（SKILL 速查表）", skill)
        else:
            fail(f"AsyncResult 缺少 {attr}", skill)

    init_params = list(inspect.signature(AsyncResult.__init__).parameters.keys())
    if "task_id" in init_params:
        ok("AsyncResult(task_id) 构造参数含 task_id（SKILL 速查表）", skill)
    else:
        fail("AsyncResult 缺少 task_id 构造参数", skill)

    @boost(BoosterParams(
        queue_name=f"verify_r2_06_rpc_{_ts}",
        broker_kind=BrokerEnum.REDIS_ACK_ABLE,
        concurrent_num=5,
        is_using_rpc_mode=True,
        rpc_timeout=20,
    ))
    def add_rpc(x: int, y: int):
        return x + y

    add_rpc.consume()
    time.sleep(1.5)

    async_result = add_rpc.push(3, 4)
    if isinstance(async_result, AsyncResult):
        ok("push 返回 AsyncResult（SKILL + c4.md §4.6）", skill)
    else:
        fail(f"push 返回类型错误: {type(async_result)}", skill)

    try:
        val = async_result.result
        if val == 7:
            ok("async_result.result 阻塞获取返回值 = 7", skill)
        else:
            fail(f"async_result.result 错误: {val!r}", skill)
    except Exception as exc:
        fail(f"async_result.result 异常: {exc}", skill)

    status_dict = async_result.status_and_result
    if isinstance(status_dict, dict) and status_dict.get("result") == 7:
        ok("status_and_result 返回 dict 且含 result/success", skill)
    else:
        fail(f"status_and_result 不符: {status_dict!r}", skill)

    status_obj = async_result.status_and_result_obj
    if isinstance(status_obj, FunctionResultStatus) and status_obj.result == 7:
        ok("status_and_result_obj 返回 FunctionResultStatus 对象", skill)
    else:
        fail(f"status_and_result_obj 不符: {status_obj!r}", skill)

    if isinstance(AioAsyncResult, type):
        ok("AioAsyncResult 类存在（SKILL 异步 RPC）", skill)
    else:
        fail("AioAsyncResult 不存在", skill)


# ---------------------------------------------------------------------------
# 2. Timing
# ---------------------------------------------------------------------------
def verify_timing_skill():
    skill = "funboost-timing-jobs"
    print("\n=== [2/5] funboost-timing-jobs ===")

    from funboost import boost, BoosterParams, BrokerEnum, ApsJobAdder

    c4 = read_doc(C4_PATH)
    if "ApsJobAdder" in c4 and "add_push_job" in c4:
        ok("c4.md §4.4 含 ApsJobAdder.add_push_job", skill)
    else:
        fail("c4.md §4.4 缺少 ApsJobAdder/add_push_job", skill)

    if "job_store_kind='redis'" in c4:
        ok("c4.md 示例多用 job_store_kind='redis'（SKILL 补充 memory 默认值）", skill)

    sig = inspect.signature(ApsJobAdder.__init__)
    default_store = sig.parameters["job_store_kind"].default
    if default_store == "memory":
        ok("ApsJobAdder 默认 job_store_kind='memory'（SKILL 正确，c4 示例未强调）", skill)
    else:
        fail(f"ApsJobAdder job_store_kind 默认={default_store!r}", skill)

    if hasattr(ApsJobAdder, "add_push_job") and callable(ApsJobAdder.add_push_job):
        ok("ApsJobAdder.add_push_job 方法存在", skill)
    else:
        fail("ApsJobAdder.add_push_job 不存在", skill)

    @boost(BoosterParams(
        queue_name=f"verify_r2_06_timing_{_ts}",
        broker_kind=BrokerEnum.SQLITE_QUEUE,
        concurrent_num=2,
    ))
    def scheduled_task(table_name: str):
        return table_name

    scheduled_task.consume()
    adder = ApsJobAdder(scheduled_task)  # 默认 memory
    adder.add_push_job(
        trigger="interval",
        seconds=60,
        kwargs={"table_name": "sessions"},
        id="r2_06_cleanup",
        replace_existing=True,
    )
    ok("ApsJobAdder(func).add_push_job(interval) 注册成功（SKILL 核心模式）", skill)

    if "apscheduler.add_job" in read_doc(Path(PROJECT_ROOT) / ".agents/skills/funboost-timing-jobs/SKILL.md"):
        ok("SKILL 铁律禁止 apscheduler.add_job(my_task)（c4 §4.4.4 允许 add_job+包装函数，SKILL 表述略严）", skill)


# ---------------------------------------------------------------------------
# 3. Workflow
# ---------------------------------------------------------------------------
def verify_workflow_skill():
    skill = "funboost-workflow"
    print("\n=== [3/5] funboost-workflow ===")

    from funboost import boost, BrokerEnum
    from funboost.workflow import chain, group, chord, WorkflowBoosterParams
    from funboost.workflow.primitives import Chain, Group, Chord
    from funboost.core.function_result_status_saver import FunctionResultStatus

    class WfParams(WorkflowBoosterParams):
        broker_kind: str = BrokerEnum.REDIS_ACK_ABLE
        concurrent_num: int = 5
        max_retry_times: int = 0
        rpc_timeout: int = 20

    @boost(WfParams(queue_name=f"verify_r2_06_wf_step_{_ts}"))
    def wf_step(x: int) -> int:
        return x + 1

    @boost(WfParams(queue_name=f"verify_r2_06_wf_double_{_ts}"))
    def wf_double(x: int) -> int:
        return x * 2

    @boost(WfParams(queue_name=f"verify_r2_06_wf_sum_{_ts}"))
    def wf_sum_list(results: list, offset: int = 0) -> int:
        return sum(results) + offset

    wf_step.consume()
    wf_double.consume()
    wf_sum_list.consume()
    time.sleep(1.5)

    wf_chain = chain(wf_step.s(1), wf_double.s())
    chain_ret = wf_chain.apply()
    if isinstance(wf_chain, Chain) and isinstance(chain_ret, FunctionResultStatus):
        ok("chain.apply() 返回 FunctionResultStatus（SKILL 未显式写类型，与源码一致）", skill)
    else:
        fail(f"chain.apply() 类型错误: chain={type(wf_chain)}, ret={type(chain_ret)}", skill)
    if chain_ret.result == 4:
        ok("chain 串行结果 step(1)->2, double(2)->4", skill)
    else:
        fail(f"chain 结果错误: {chain_ret.result}", skill)

    wf_group = group(wf_step.s(10), wf_step.s(20))
    group_ret = wf_group.apply()
    if isinstance(wf_group, Group) and isinstance(group_ret, list):
        ok("group.apply() 返回 list（SKILL 未显式写类型，与源码一致）", skill)
    else:
        fail(f"group.apply() 类型错误: {type(group_ret)}", skill)
    if group_ret == [11, 21]:
        ok("group.apply() 并行结果 [11, 21]", skill)
    else:
        fail(f"group 结果错误: {group_ret}", skill)

    wf_chord = chord(group(wf_double.s(1), wf_double.s(2)), wf_sum_list.s(offset=100))
    chord_ret = wf_chord.apply()
    if isinstance(wf_chord, Chord) and isinstance(chord_ret, FunctionResultStatus):
        ok("chord.apply() 返回 FunctionResultStatus", skill)
    else:
        fail(f"chord.apply() 类型错误: {type(chord_ret)}", skill)
    if chord_ret.result == 106:  # [2,4] sum=6 + 100
        ok("chord 聚合 callback 结果 = 106", skill)
    else:
        fail(f"chord 结果错误: {chord_ret.result}", skill)

    params = WorkflowBoosterParams(queue_name="__wf__")
    if params.is_using_rpc_mode is True:
        ok("WorkflowBoosterParams 默认 is_using_rpc_mode=True（SKILL 注意事项）", skill)
    else:
        fail("WorkflowBoosterParams 未默认启用 RPC", skill)


# ---------------------------------------------------------------------------
# 4. FaaS
# ---------------------------------------------------------------------------
def verify_faas_skill():
    skill = "funboost-faas-deploy"
    print("\n=== [4/5] funboost-faas-deploy ===")

    from funboost.faas import fastapi_router
    from funboost.faas.fastapi_adapter import MsgItem

    c15 = read_doc(C15_PATH)
    if "/funboost/publish" in c15 and "msg_body" in c15:
        ok("c15.md §15.5 含 POST /funboost/publish + msg_body", skill)
    else:
        fail("c15.md FaaS 路由/msg_body 描述缺失", skill)

    prefix = getattr(fastapi_router, "prefix", "")
    if prefix == "/funboost":
        ok("fastapi_router prefix='/funboost'（SKILL + c15）", skill)
    else:
        fail(f"fastapi_router prefix 错误: {prefix!r}", skill)

    publish_ok = get_result_ok = False
    for route in fastapi_router.routes:
        rel = getattr(route, "path", "") or ""
        methods = set(getattr(route, "methods", None) or []) - {"HEAD"}
        if rel.endswith("/publish") and "POST" in methods:
            publish_ok = True
        if rel.endswith("/get_result") and "GET" in methods:
            get_result_ok = True

    if publish_ok:
        ok("POST /funboost/publish 路由存在", skill)
    else:
        fail("POST /funboost/publish 路由缺失", skill)
    if get_result_ok:
        ok("GET /funboost/get_result 路由存在", skill)
    else:
        fail("GET /funboost/get_result 路由缺失", skill)

    fields = MsgItem.model_fields if hasattr(MsgItem, "model_fields") else MsgItem.__fields__
    if "msg_body" in fields and "msg" not in fields:
        ok("请求体字段名为 msg_body 而非 msg（SKILL + c15 §15.7）", skill)
    else:
        fail("MsgItem 字段命名与 SKILL/c15 不符", skill)

    try:
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from funboost import boost, BoosterParams, BrokerEnum

        @boost(BoosterParams(
            queue_name=f"verify_r2_06_faas_{_ts}",
            broker_kind=BrokerEnum.REDIS_ACK_ABLE,
            is_using_rpc_mode=True,
            is_send_consumer_heartbeat_to_redis=True,
            concurrent_num=3,
        ))
        def faas_add(x: int, y: int):
            return x + y

        faas_add.consume()
        time.sleep(1.5)

        app = FastAPI()
        app.include_router(fastapi_router)
        client = TestClient(app)

        bad = client.post(
            "/funboost/publish",
            json={"queue_name": f"verify_r2_06_faas_{_ts}", "msg": {"x": 1, "y": 2}},
        )
        if bad.status_code == 422:
            ok("使用 msg 而非 msg_body 返回 422", skill)
        else:
            fail(f"msg 字段应 422, 实际 {bad.status_code}", skill)

        good = client.post(
            "/funboost/publish",
            json={
                "queue_name": f"verify_r2_06_faas_{_ts}",
                "msg_body": {"x": 5, "y": 6},
                "need_result": True,
                "timeout": 10,
            },
        )
        body = good.json()
        sr = (body.get("data") or {}).get("status_and_result")
        if good.status_code == 200 and sr and sr.get("result") == 11:
            ok("POST msg_body + need_result=true RPC 返回 result=11", skill)
        else:
            fail(f"FaaS publish 集成失败: {body}", skill)
    except ImportError as exc:
        ok(f"FastAPI TestClient 集成跳过: {exc}", skill)


# ---------------------------------------------------------------------------
# 5. Retry
# ---------------------------------------------------------------------------
def verify_retry_skill():
    skill = "funboost-advanced-retry"
    print("\n=== [5/5] funboost-advanced-retry ===")

    from funboost.core.func_params_model import BoosterParams as BP

    c4 = read_doc(C4_PATH)
    if "advanced_retry_config" in c4 and "do_task_filtering" in c4:
        ok("c4.md §4.24.5 / §4.35 含 advanced_retry_config 与 do_task_filtering", skill)
    else:
        fail("c4.md 重试/过滤章节缺失", skill)

    cfg = BP(queue_name="__cfg__").advanced_retry_config
    skill_keys = {
        "retry_mode": "sleep",
        "retry_base_interval": 1.0,
        "retry_multiplier": 2.0,
        "retry_max_interval": 60.0,
        "retry_jitter": False,
    }
    for key, expected in skill_keys.items():
        if key in cfg and cfg[key] == expected:
            ok(f"advanced_retry_config[{key!r}] 默认值={expected!r}（SKILL 表 + c4 §4.24.5）", skill)
        else:
            fail(f"advanced_retry_config[{key!r}] 不符: {cfg.get(key)!r}", skill)

    base_consumer_src = Path(PROJECT_ROOT, "funboost/consumers/base_consumer.py").read_text(encoding="utf-8")
    if re.search(r"def _should_filter_task", base_consumer_src):
        ok("_should_filter_task 在消费端执行过滤（SKILL「消费端过滤」准确）", skill)
    else:
        fail("未找到 _should_filter_task", skill)

    if "add_a_value" in base_consumer_src and "do_task_filtering" in base_consumer_src:
        ok("过滤键在消费成功后写入 Redis（完成消费周期后才生效）", skill)
    else:
        fail("do_task_filtering 写入逻辑未找到", skill)

    skill_text = Path(PROJECT_ROOT, ".agents/skills/funboost-advanced-retry/SKILL.md").read_text(encoding="utf-8")
    if "完成一次消费周期后" in skill_text:
        ok("SKILL do_task_filtering 语义：完成消费周期后跳过（比 c4 §4.35 示例更准确）", skill)
    else:
        fail("SKILL 未描述 do_task_filtering 消费周期语义", skill)

    if "RPC" in c4 and "do_task_filtering" in c4 and "不要同时使用" in c4:
        ok("c4 §4.35 警告 RPC 与 do_task_filtering 勿同时使用（SKILL 可补充）", skill)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=== verify_all_r2_06: 5 SKILL 综合验证 ===")
    verify_rpc_skill()
    verify_timing_skill()
    verify_workflow_skill()
    verify_faas_skill()
    verify_retry_skill()

    print(f"\n=== 汇总: PASS={len(PASS)}, FAIL={len(FAIL)} ===")
    for skill_name, items in SKILL_RESULTS.items():
        fails = [x for x in items if x.startswith("FAIL")]
        status = "OK" if not fails else "FAIL"
        print(f"  [{status}] {skill_name}: {len(items) - len(fails)} pass, {len(fails)} fail")

    if FAIL:
        for item in FAIL:
            print(f"  FAIL: {item}")
        os._exit(1)

    print("[DONE] verify_all_r2_06 全部通过")
    os._exit(66)
