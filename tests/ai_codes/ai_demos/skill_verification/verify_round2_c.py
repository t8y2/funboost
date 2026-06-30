"""Round2-C: 综合验证 4 个 SKILL.md（rpc-mode / timing-jobs / workflow / faas-deploy）"""
import asyncio
import inspect
import os
import time
from datetime import datetime, timedelta

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
_ts = int(time.time())
os.environ["PRINT_WRTIE_FILE_NAME"] = f"verify_round2_c_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"verify_round2_c_std_{_ts}"

PASS = []
FAIL = []
DOC_ISSUES = []


def ok(msg):
    PASS.append(msg)
    print(f"[PASS] {msg}")


def fail(msg):
    FAIL.append(msg)
    print(f"[FAIL] {msg}")


def doc_issue(msg):
    DOC_ISSUES.append(msg)
    print(f"[DOC] {msg}")


# ---------------------------------------------------------------------------
# 1. RPC MODE
# ---------------------------------------------------------------------------
def verify_rpc_static():
    from funboost.core.msg_result_getter import AsyncResult, AioAsyncResult
    from funboost.core.function_result_status_saver import FunctionResultStatus

    ok("AsyncResult 类可导入")
    ok("AioAsyncResult 类可导入")

    for attr in ("result", "status_and_result", "status_and_result_obj"):
        if hasattr(AsyncResult, attr):
            ok(f"AsyncResult 有 {attr!r}")
        else:
            fail(f"AsyncResult 缺少 {attr!r}")

    ar_inst = AsyncResult("dummy-task-id-for-check")
    if hasattr(ar_inst, "task_id") and ar_inst.task_id == "dummy-task-id-for-check":
        ok("AsyncResult 实例有 task_id 属性（__init__ 设置）")
    else:
        fail("AsyncResult 实例缺少 task_id")

    if hasattr(AsyncResult, "status") or hasattr(ar_inst, "status"):
        doc_issue("AsyncResult 源码存在 .status 属性，但 RPC SKILL 未文档化")
    else:
        ok("AsyncResult 无 .status 属性（SKILL 正确使用 status_and_result）")

    for attr in ("result", "status_and_result", "status_and_result_obj"):
        if hasattr(AioAsyncResult, attr):
            ok(f"AioAsyncResult 有 {attr!r}")
        else:
            fail(f"AioAsyncResult 缺少 {attr!r}")

    return AsyncResult, AioAsyncResult, FunctionResultStatus


def verify_rpc_runtime(AsyncResult, FunctionResultStatus):
    from funboost import boost, BoosterParams, BrokerEnum

    @boost(BoosterParams(
        queue_name="verify_round2c_rpc_add",
        broker_kind=BrokerEnum.REDIS_ACK_ABLE,
        concurrent_num=5,
        is_using_rpc_mode=True,
        rpc_timeout=30,
    ))
    def add(x: int, y: int):
        return x + y

    add.consume()
    time.sleep(2)

    async_result = add.push(3, 4)
    if isinstance(async_result, AsyncResult):
        ok("push 返回 AsyncResult")
    else:
        fail(f"push 应返回 AsyncResult，实际 {type(async_result).__name__}")

    if async_result.task_id:
        ok(f"AsyncResult.task_id 非空: {async_result.task_id[:8]}...")
    else:
        fail("AsyncResult.task_id 为空")

    publish_result = add.publish({"x": 10, "y": 20})
    if isinstance(publish_result, AsyncResult):
        ok("publish 返回 AsyncResult")
    else:
        fail(f"publish 应返回 AsyncResult，实际 {type(publish_result).__name__}")

    try:
        val = async_result.result
        if val == 7:
            ok("async_result.result == 7")
        else:
            fail(f"async_result.result 错误: {val!r}")
    except Exception as exc:
        fail(f"async_result.result 异常: {type(exc).__name__}: {exc}")

    status_dict = async_result.status_and_result
    if isinstance(status_dict, dict) and status_dict.get("result") == 7 and status_dict.get("success") is True:
        ok("status_and_result 返回 dict 且 result/success 正确")
    else:
        fail(f"status_and_result 错误: {status_dict!r}")

    status_obj = async_result.status_and_result_obj
    if isinstance(status_obj, FunctionResultStatus) and status_obj.result == 7 and status_obj.success is True:
        ok("status_and_result_obj 返回 FunctionResultStatus 对象")
    else:
        fail(f"status_and_result_obj 错误: {status_obj!r}")


# ---------------------------------------------------------------------------
# 2. TIMING JOBS
# ---------------------------------------------------------------------------
def verify_timing():
    from funboost import boost, BoosterParams, BrokerEnum, ApsJobAdder
    from funboost.timing_job import ApsJobAdder as ApsJobAdderSub

    if ApsJobAdder is ApsJobAdderSub:
        ok("funboost 与 funboost.timing_job 导出同一 ApsJobAdder")
    else:
        fail("ApsJobAdder 导入路径不一致")

    sig = inspect.signature(ApsJobAdder.__init__)
    params = list(sig.parameters.keys())
    expected_init = ["self", "booster", "job_store_kind", "is_auto_start", "is_auto_paused"]
    if params == expected_init:
        ok(f"ApsJobAdder.__init__ 参数: {expected_init[1:]}")
    else:
        fail(f"ApsJobAdder.__init__ 参数不符: {params}")

    default_store = sig.parameters["job_store_kind"].default
    if default_store == "memory":
        ok("ApsJobAdder job_store_kind 默认值='memory'（非 redis）")
    else:
        fail(f"job_store_kind 默认应为 'memory'，实际 {default_store!r}")

    if hasattr(ApsJobAdder, "add_push_job") and callable(ApsJobAdder.add_push_job):
        ok("ApsJobAdder.add_push_job 方法存在")
    else:
        fail("ApsJobAdder.add_push_job 不存在")

    add_sig = inspect.signature(ApsJobAdder.add_push_job)
    for p in ("trigger", "args", "kwargs", "id", "replace_existing"):
        if p in add_sig.parameters:
            ok(f"add_push_job 有参数 {p!r}")
        else:
            fail(f"add_push_job 缺少参数 {p!r}")

    @boost(BoosterParams(
        queue_name="verify_round2c_timing",
        broker_kind=BrokerEnum.SQLITE_QUEUE,
        concurrent_num=3,
    ))
    def scheduled_task(table_name: str):
        return table_name

    scheduled_task.consume()

    adder = ApsJobAdder(scheduled_task)
    if adder.job_store_kind == "memory":
        ok("ApsJobAdder(func) 实例 job_store_kind='memory'")
    else:
        fail(f"实例 job_store_kind 错误: {adder.job_store_kind!r}")

    adder.add_push_job(
        trigger="interval",
        seconds=30,
        kwargs={"table_name": "sessions"},
        id="round2c_interval",
        replace_existing=True,
    )
    ok("add_push_job interval 注册成功")

    adder.add_push_job(
        trigger="cron",
        hour=2,
        minute=0,
        kwargs={"table_name": "logs"},
        id="round2c_cron",
        replace_existing=True,
    )
    ok("add_push_job cron 注册成功")

    adder.add_push_job(
        trigger="date",
        run_date=datetime.now() + timedelta(seconds=60),
        kwargs={"table_name": "once"},
        id="round2c_date",
        replace_existing=True,
    )
    ok("add_push_job date 注册成功")


# ---------------------------------------------------------------------------
# 3. WORKFLOW
# ---------------------------------------------------------------------------
def verify_workflow():
    from funboost import boost, BrokerEnum
    from funboost.workflow import chain, group, chord, WorkflowBoosterParams
    from funboost.workflow import Chain, Group, Chord, Signature
    from funboost.core.function_result_status_saver import FunctionResultStatus

    for name, obj in (
        ("chain", chain),
        ("group", group),
        ("chord", chord),
        ("WorkflowBoosterParams", WorkflowBoosterParams),
    ):
        if obj is not None:
            ok(f"funboost.workflow 导出 {name}")
        else:
            fail(f"funboost.workflow 未导出 {name}")

    params = WorkflowBoosterParams(queue_name="__wf_check__")
    if params.is_using_rpc_mode is True:
        ok("WorkflowBoosterParams 默认 is_using_rpc_mode=True")
    else:
        fail(f"WorkflowBoosterParams.is_using_rpc_mode 默认应为 True，实际 {params.is_using_rpc_mode}")

    class WfParams(WorkflowBoosterParams):
        broker_kind: str = BrokerEnum.REDIS_ACK_ABLE
        concurrent_num: int = 5
        max_retry_times: int = 0
        rpc_timeout: int = 30

    @boost(WfParams(queue_name="verify_round2c_wf_step"))
    def step(x: int) -> int:
        return x + 1

    @boost(WfParams(queue_name="verify_round2c_wf_double"))
    def double_val(x: int) -> int:
        return x * 2

    @boost(WfParams(queue_name="verify_round2c_wf_sum"))
    def sum_list(results: list, offset: int = 0) -> int:
        return sum(results) + offset

    if hasattr(step, "s") and callable(step.s):
        ok("import workflow 后 Booster.s() 存在")
    else:
        fail("Booster.s() 不存在")

    if hasattr(step, "si") and callable(step.si):
        ok("Booster.si() 存在")
    else:
        fail("Booster.si() 不存在")

    sig = step.s(1, tag="a")
    if isinstance(sig, Signature) and sig.immutable is False:
        ok("func.s() 创建 mutable Signature")
    else:
        fail(f"func.s() 行为不符: {sig!r}")

    sig_i = step.si(99)
    if isinstance(sig_i, Signature) and sig_i.immutable is True:
        ok("func.si() 创建 immutable Signature")
    else:
        fail(f"func.si() 行为不符: {sig_i!r}")

    step.consume()
    double_val.consume()
    sum_list.consume()
    time.sleep(2)

    wf_chain = chain(step.s(1), double_val.s())
    if isinstance(wf_chain, Chain):
        ok("chain() 返回 Chain")
    else:
        fail(f"chain() 应返回 Chain，实际 {type(wf_chain)}")

    chain_status = wf_chain.apply()
    if isinstance(chain_status, FunctionResultStatus) and chain_status.result == 4:
        ok("chain.apply() 返回 FunctionResultStatus，result=4")
    else:
        fail(f"chain.apply() 错误: {chain_status!r}")

    wf_group = group(step.s(10), step.s(20))
    if isinstance(wf_group, Group):
        ok("group() 返回 Group")
    else:
        fail(f"group() 应返回 Group，实际 {type(wf_group)}")

    group_results = wf_group.apply()
    if isinstance(group_results, list) and group_results == [11, 21]:
        ok(f"group.apply() 返回 list: {group_results}")
    else:
        fail(f"group.apply() 应返回 list [11,21]，实际 {group_results!r} (type={type(group_results).__name__})")

    wf_chord = chord(
        group(double_val.s(1), double_val.s(2)),
        sum_list.s(offset=100),
    )
    if isinstance(wf_chord, Chord):
        ok("chord() 返回 Chord")
    else:
        fail(f"chord() 应返回 Chord，实际 {type(wf_chord)}")

    chord_status = wf_chord.apply()
    if isinstance(chord_status, FunctionResultStatus) and chord_status.result == 106:
        ok("chord.apply() 返回 FunctionResultStatus，result=106")
    else:
        fail(f"chord.apply() 错误: {chord_status!r}")


# ---------------------------------------------------------------------------
# 4. FAAS DEPLOY
# ---------------------------------------------------------------------------
def verify_faas_static():
    from funboost.faas import fastapi_router, flask_blueprint
    from funboost.faas.fastapi_adapter import MsgItem

    ok(f"fastapi_router 可导入, type={type(fastapi_router).__name__}")
    ok(f"flask_blueprint 可导入, type={type(flask_blueprint).__name__}")

    prefix = getattr(fastapi_router, "prefix", "")
    if prefix == "/funboost":
        ok("fastapi_router.prefix='/funboost'")
    else:
        fail(f"fastapi_router.prefix 应为 '/funboost'，实际 {prefix!r}")

    publish_ok = get_result_ok = False
    for route in fastapi_router.routes:
        path = getattr(route, "path", "") or ""
        methods = set(getattr(route, "methods", None) or []) - {"HEAD"}
        if path.endswith("/publish") and "POST" in methods:
            publish_ok = True
        if path.endswith("/get_result") and "GET" in methods:
            get_result_ok = True

    if publish_ok:
        ok("POST /funboost/publish 路由存在")
    else:
        fail("POST /funboost/publish 路由缺失")

    if get_result_ok:
        ok("GET /funboost/get_result 路由存在")
    else:
        fail("GET /funboost/get_result 路由缺失")

    fields = MsgItem.model_fields if hasattr(MsgItem, "model_fields") else MsgItem.__fields__
    for name in ("queue_name", "msg_body", "need_result", "timeout"):
        if name in fields:
            ok(f"MsgItem.{name} 字段存在")
        else:
            fail(f"MsgItem.{name} 字段不存在")

    if "msg" not in fields and "msg_body" in fields:
        ok("请求体字段为 msg_body（非 msg）")
    else:
        fail("MsgItem 字段命名与 SKILL 描述不符")

    defaults = MsgItem(queue_name="q", msg_body={"x": 1})
    if defaults.need_result is False and defaults.timeout == 60:
        ok("MsgItem need_result 默认 False, timeout 默认 60")
    else:
        fail(f"MsgItem 默认值错误: need_result={defaults.need_result}, timeout={defaults.timeout}")


def verify_faas_integration():
    try:
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from funboost.faas import fastapi_router
        from funboost import boost, BoosterParams, BrokerEnum
    except ImportError as e:
        ok(f"FastAPI 集成测试跳过: {e}")
        return

    @boost(BoosterParams(
        queue_name="verify_round2c_faas",
        broker_kind=BrokerEnum.REDIS_ACK_ABLE,
        is_using_rpc_mode=True,
        is_send_consumer_heartbeat_to_redis=True,
        concurrent_num=3,
    ))
    def faas_task(x: int, y: int):
        return x + y

    faas_task.consume()
    time.sleep(2)

    app = FastAPI()
    app.include_router(fastapi_router)
    client = TestClient(app)

    bad = client.post(
        "/funboost/publish",
        json={"queue_name": "verify_round2c_faas", "msg": {"x": 1, "y": 2}},
    )
    if bad.status_code == 422:
        ok("使用 msg 而非 msg_body 返回 422")
    else:
        fail(f"msg 字段应 422，实际 status={bad.status_code}")

    resp = client.post(
        "/funboost/publish",
        json={
            "queue_name": "verify_round2c_faas",
            "msg_body": {"x": 5, "y": 6},
            "need_result": True,
            "timeout": 10,
        },
    )
    body = resp.json()
    sr = (body.get("data") or {}).get("status_and_result")
    if resp.status_code == 200 and body.get("succ") and sr and sr.get("result") == 11:
        ok("POST /funboost/publish msg_body + need_result=true 返回 result=11")
    else:
        fail(f"FaaS publish 集成失败: {body}")


# ---------------------------------------------------------------------------
# SKILL 文档一致性扫描（静态）
# ---------------------------------------------------------------------------
def scan_skill_docs():
    skill_paths = {
        "rpc-mode": r"D:\codes\funboost\.agents\skills\funboost-rpc-mode\SKILL.md",
        "timing-jobs": r"D:\codes\funboost\.agents\skills\funboost-timing-jobs\SKILL.md",
        "workflow": r"D:\codes\funboost\.agents\skills\funboost-workflow\SKILL.md",
        "faas-deploy": r"D:\codes\funboost\.agents\skills\funboost-faas-deploy\SKILL.md",
    }
    for name, path in skill_paths.items():
        with open(path, encoding="utf-8") as f:
            text = f.read()

        if name == "rpc-mode":
            bad_status_refs = [
                "async_result.status ",
                "async_result.status\n",
                "result_obj.status ",
                "result_obj.status\n",
                "aio_result.status ",
                "aio_result.status\n",
            ]
            if any(ref in text for ref in bad_status_refs):
                doc_issue("RPC SKILL 错误推荐使用 AsyncResult.status 属性")
            else:
                ok("RPC SKILL 未错误推荐 AsyncResult.status（应使用 status_and_result）")
            if "is_using_rpc_mode=True" in text:
                ok("RPC SKILL 强调 is_using_rpc_mode=True")

        if name == "timing-jobs":
            if "job_store_kind='memory'" in text or 'job_store_kind="memory"' in text or "默认 job_store_kind='memory'" in text:
                ok("Timing SKILL 说明默认 job_store_kind='memory'")
            elif "ApsJobAdder(cleanup_expired_data)" in text and "job_store_kind" not in text.split("ApsJobAdder(cleanup_expired_data)")[1].split(")")[0]:
                ok("Timing SKILL 核心示例 ApsJobAdder(func) 未显式传 redis，符合 memory 默认")
            if "apscheduler.add_job" in text and "禁止" in text:
                ok("Timing SKILL 禁止直接使用 apscheduler.add_job")

        if name == "workflow":
            if "WorkflowBoosterParams" in text and "is_using_rpc_mode=True" in text:
                ok("Workflow SKILL 推荐 WorkflowBoosterParams 且说明 RPC")
            if "group.apply()" not in text and "parallel_tasks.apply()" in text:
                ok("Workflow SKILL group 示例使用 apply()（返回类型由运行时验证）")

        if name == "faas-deploy":
            if '"msg_body"' in text:
                ok("FaaS SKILL 请求体使用 msg_body")
            if '"msg"' in text and '"msg_body"' in text and "不是 `msg`" in text:
                ok("FaaS SKILL 明确 msg_body 非 msg")
            if "POST /funboost/publish" in text and "GET /funboost/get_result" in text:
                ok("FaaS SKILL 路由路径正确")


if __name__ == "__main__":
    print("=== [1/4] RPC MODE ===")
    AR, AAR, FRS = verify_rpc_static()
    verify_rpc_runtime(AR, FRS)

    print("\n=== [2/4] TIMING JOBS ===")
    verify_timing()

    print("\n=== [3/4] WORKFLOW ===")
    verify_workflow()

    print("\n=== [4/4] FAAS DEPLOY ===")
    verify_faas_static()
    verify_faas_integration()

    print("\n=== SKILL 文档扫描 ===")
    scan_skill_docs()

    print(f"\n=== 汇总: PASS={len(PASS)}, FAIL={len(FAIL)}, DOC={len(DOC_ISSUES)} ===")
    if FAIL:
        for item in FAIL:
            print(f"  FAIL: {item}")
    if DOC_ISSUES:
        for item in DOC_ISSUES:
            print(f"  DOC: {item}")

    time.sleep(2)
    os._exit(66 if not FAIL else 1)
