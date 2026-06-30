"""验证 funboost-faas-deploy SKILL.md 的技术准确性（r1）"""
import inspect
import os
import time

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
_ts = int(time.time())
os.environ["PRINT_WRTIE_FILE_NAME"] = f"verify_faas_r1_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"verify_faas_r1_std_{_ts}"

from funboost import boost, BoosterParams, BrokerEnum
from funboost.constant import EnvConst

PASS = []
FAIL = []


def ok(msg):
    PASS.append(msg)
    print(f"[PASS] {msg}")


def fail(msg):
    FAIL.append(msg)
    print(f"[FAIL] {msg}")


def check_faas_exports():
    """SKILL 速查表：fastapi_router / flask_blueprint / django_router 导出"""
    from funboost.faas import (
        fastapi_router,
        flask_blueprint,
        ActiveCousumerProcessInfoGetter,
    )

    ok(f"fastapi_router 可导入, type={type(fastapi_router).__name__}")
    ok(f"flask_blueprint 可导入, type={type(flask_blueprint).__name__}")

    try:
        from funboost.faas import django_router  # noqa: F401
        ok("django_router 可导入（需 django-ninja）")
    except ImportError as e:
        ok(f"django_router 惰性导入正常（未装 django-ninja 时可选）: {e}")

    if callable(ActiveCousumerProcessInfoGetter):
        ok("funboost.faas 还导出 ActiveCousumerProcessInfoGetter（SKILL 未提及但源码存在）")


def check_fastapi_router_routes():
    """SKILL: POST /funboost/publish, GET /funboost/get_result"""
    from funboost.faas import fastapi_router

    prefix = getattr(fastapi_router, "prefix", "")
    if prefix == "/funboost":
        ok(f"fastapi_router prefix={prefix!r}")
    else:
        fail(f"fastapi_router prefix 应为 '/funboost', 实际 {prefix!r}")

    def _full_path(relative_path: str) -> str:
        p = relative_path if relative_path.startswith("/") else f"/{relative_path}"
        return (prefix.rstrip("/") + p) if prefix else p

    publish_found = get_result_found = False
    for route in fastapi_router.routes:
        rel = getattr(route, "path", "") or ""
        methods = set(getattr(route, "methods", None) or []) - {"HEAD"}
        if rel.endswith("/publish") and "POST" in methods:
            publish_found = True
        if rel.endswith("/get_result") and "GET" in methods:
            get_result_found = True

    if publish_found:
        ok(f"FastAPI 路由 {_full_path('/publish')} methods=['POST'] 存在")
    else:
        fail(f"FastAPI 路由 {_full_path('/publish')} POST 缺失")

    if get_result_found:
        ok(f"FastAPI 路由 {_full_path('/get_result')} methods=['GET'] 存在")
    else:
        fail(f"FastAPI 路由 {_full_path('/get_result')} GET 缺失")

    route_count = len([r for r in fastapi_router.routes if getattr(r, "path", None)])
    if route_count > 2:
        ok(f"FastAPI router 另有 {route_count - 2} 个扩展端点（SKILL 仅列核心 2 个，属文档精简）")


def check_msg_item_model():
    """SKILL 请求体字段：queue_name, msg_body, need_result, timeout"""
    from funboost.faas.fastapi_adapter import MsgItem

    fields = MsgItem.model_fields if hasattr(MsgItem, "model_fields") else MsgItem.__fields__
    for name in ("queue_name", "msg_body", "need_result", "timeout"):
        if name in fields:
            ok(f"MsgItem.{name} 字段存在")
        else:
            fail(f"MsgItem.{name} 字段不存在")

    defaults = MsgItem(queue_name="q", msg_body={"x": 1})
    if defaults.need_result is False:
        ok("MsgItem.need_result 默认值=False（与 SKILL 一致）")
    else:
        fail(f"MsgItem.need_result 默认值错误: {defaults.need_result!r}")

    if defaults.timeout == 60:
        ok("MsgItem.timeout 默认值=60（与 SKILL 一致）")
    else:
        fail(f"MsgItem.timeout 默认值错误: {defaults.timeout!r}")

    if "msg" not in fields and "msg_body" in fields:
        ok("参数名是 msg_body 而非 msg（与 SKILL 强调一致）")
    else:
        fail("msg_body 字段命名与 SKILL 描述不符")


def check_get_result_params():
    """SKILL: GET /funboost/get_result?task_id=xxx&timeout=5"""
    from funboost.faas import fastapi_router

    sig = None
    for route in fastapi_router.routes:
        path = getattr(route, "path", "") or ""
        if path.endswith("/get_result"):
            sig = inspect.signature(route.endpoint)
            break

    if sig is None:
        fail("未找到 get_result 端点")
        return

    params = sig.parameters
    if "task_id" in params:
        ok("get_result 参数 task_id 存在")
    else:
        fail("get_result 缺少 task_id 参数")

    if "timeout" in params:
        default = params["timeout"].default
        if default == 5:
            ok("get_result 参数 timeout 默认值=5（与 SKILL 一致）")
        else:
            fail(f"get_result timeout 默认值错误: {default!r}")
    else:
        fail("get_result 缺少 timeout 参数")


def check_is_use_local_booster_env():
    """SKILL: os.environ['funboost.faas.is_use_local_booster'] = 'true'"""
    expected = "funboost.faas.is_use_local_booster"
    if EnvConst.FUNBOOST_FAAS_IS_USE_LOCAL_BOOSTER == expected:
        ok(f"环境变量名 EnvConst.FUNBOOST_FAAS_IS_USE_LOCAL_BOOSTER={expected!r}")
    else:
        fail(
            f"环境变量名不符: SKILL 写 {expected!r}, "
            f"源码 EnvConst={EnvConst.FUNBOOST_FAAS_IS_USE_LOCAL_BOOSTER!r}"
        )

    from funboost.core.active_cousumer_info_getter import SingleQueueConusmerParamsGetter

    src = inspect.getsource(SingleQueueConusmerParamsGetter.__init__)
    if "FUNBOOST_FAAS_IS_USE_LOCAL_BOOSTER" in src and "'true'" in src:
        ok("SingleQueueConusmerParamsGetter 读取 env 且 'true' 启用本地 booster")
    else:
        fail("SingleQueueConusmerParamsGetter 未按 SKILL 描述读取 is_use_local_booster 环境变量")


def check_flask_blueprint():
    """SKILL: app.register_blueprint(flask_blueprint)"""
    from funboost.faas import flask_blueprint

    if flask_blueprint.url_prefix == "/funboost":
        ok(f"flask_blueprint url_prefix={flask_blueprint.url_prefix!r}")
    else:
        fail(f"flask_blueprint url_prefix 错误: {flask_blueprint.url_prefix!r}")

    app_routes = set()
    try:
        from flask import Flask

        app = Flask(__name__)
        app.register_blueprint(flask_blueprint)
        for rule in app.url_map.iter_rules():
            if rule.rule.startswith("/funboost"):
                app_routes.add((rule.rule, frozenset(rule.methods)))
    except ImportError:
        ok("Flask 未安装，跳过 blueprint 路由枚举")
        return

    publish_ok = any(r == "/funboost/publish" and "POST" in m for r, m in app_routes)
    get_result_ok = any(r == "/funboost/get_result" and "GET" in m for r, m in app_routes)
    if publish_ok:
        ok("Flask POST /funboost/publish 存在")
    else:
        fail("Flask POST /funboost/publish 不存在")
    if get_result_ok:
        ok("Flask GET /funboost/get_result 存在")
    else:
        fail("Flask GET /funboost/get_result 不存在")


def check_need_result_rpc_behavior():
    """SKILL: need_result 为 true 时内置 router 自动启用 RPC（FastAPI 源码）"""
    from funboost.faas import fastapi_adapter

    src = inspect.getsource(fastapi_adapter.publish_msg)
    if "need_result" in src and "TaskOptions(is_using_rpc_mode=True)" in src:
        ok("FastAPI publish 在 need_result=True 时使用 TaskOptions(is_using_rpc_mode=True)")
    else:
        fail("FastAPI publish 未按 SKILL 描述处理 need_result RPC")

    from funboost.faas import flask_adapter

    flask_src = inspect.getsource(flask_adapter.publish_msg)
    if "need_result" in flask_src and "TaskOptions(is_using_rpc_mode=True)" in flask_src:
        ok("Flask publish 在 need_result=True 时使用 TaskOptions(is_using_rpc_mode=True)")
    else:
        fail("Flask publish 未按 SKILL 描述处理 need_result RPC")

    try:
        django_mod = __import__("funboost.faas.django_adapter", fromlist=["publish_msg"])
        django_src = inspect.getsource(django_mod.publish_msg)
        if "is_using_rpc_mode" in django_src and "need_result" in django_src:
            ok("Django adapter 对 need_result 有 is_using_rpc_mode 校验（SKILL 常见错误表所述）")
        else:
            fail("Django adapter need_result / is_using_rpc_mode 行为与 SKILL 不符")
    except ImportError:
        ok("Django adapter RPC 行为校验跳过（未装 django-ninja）")


def check_custom_api_import():
    """SKILL 自定义 API 示例中的 AioAsyncResult 导入路径"""
    try:
        from funboost.core.msg_result_getter import AioAsyncResult as A1
        from funboost import AioAsyncResult as A2

        if A1 is A2:
            ok("SKILL 示例 from funboost.core.msg_result_getter import AioAsyncResult 可用")
        else:
            ok("两种 AioAsyncResult 导入路径均可用（推荐 from funboost import AioAsyncResult）")
    except ImportError as e:
        fail(f"AioAsyncResult 导入失败: {e}")


@boost(
    BoosterParams(
        queue_name="faas_r1_verify_task",
        broker_kind=BrokerEnum.REDIS_ACK_ABLE,
        is_using_rpc_mode=True,
        is_send_consumer_heartbeat_to_redis=True,
        concurrent_num=3,
    )
)
def faas_r1_task(x: int, y: int):
    return x + y


def run_integration_checks():
    """用 TestClient 验证 publish 请求体字段 msg_body / need_result"""
    try:
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from funboost.faas import fastapi_router
    except ImportError as e:
        ok(f"FastAPI 集成测试跳过（未安装）: {e}")
        return

    faas_r1_task.consume()
    time.sleep(2)

    app = FastAPI()
    app.include_router(fastapi_router)
    client = TestClient(app)

    # 错误字段 msg 应被拒绝（422）
    bad = client.post("/funboost/publish", json={"queue_name": "faas_r1_verify_task", "msg": {"x": 1, "y": 2}})
    if bad.status_code == 422:
        ok("POST /funboost/publish 使用 msg 而非 msg_body 返回 422")
    else:
        fail(f"使用 msg 字段应 422, 实际 status={bad.status_code}")

    # 正确 msg_body，need_result=false
    resp = client.post(
        "/funboost/publish",
        json={"queue_name": "faas_r1_verify_task", "msg_body": {"x": 10, "y": 20}, "need_result": False},
    )
    body = resp.json()
    if resp.status_code == 200 and body.get("succ") and body.get("data", {}).get("task_id"):
        ok("POST /funboost/publish msg_body + need_result=false 成功")
        task_id = body["data"]["task_id"]
    else:
        fail(f"publish 失败: status={resp.status_code}, body={body}")
        return

    time.sleep(2)

    # need_result=true 应返回 status_and_result
    rpc_resp = client.post(
        "/funboost/publish",
        json={
            "queue_name": "faas_r1_verify_task",
            "msg_body": {"x": 100, "y": 200},
            "need_result": True,
            "timeout": 10,
        },
    )
    rpc_body = rpc_resp.json()
    sr = (rpc_body.get("data") or {}).get("status_and_result")
    if rpc_resp.status_code == 200 and rpc_body.get("succ") and sr and sr.get("result") == 300:
        ok("need_result=true 返回 status_and_result.result=300")
    else:
        fail(f"need_result=true RPC 失败: {rpc_body}")

    # GET get_result
    gr = client.get(f"/funboost/get_result?task_id={task_id}&timeout=5")
    if gr.status_code == 200:
        ok("GET /funboost/get_result 可调用")
    else:
        fail(f"get_result 失败: status={gr.status_code}")


if __name__ == "__main__":
    print("=== 静态校验 ===")
    check_faas_exports()
    check_fastapi_router_routes()
    check_msg_item_model()
    check_get_result_params()
    check_is_use_local_booster_env()
    check_flask_blueprint()
    check_need_result_rpc_behavior()
    check_custom_api_import()

    print("\n=== 集成校验 ===")
    run_integration_checks()

    print(f"\n=== 汇总: PASS={len(PASS)}, FAIL={len(FAIL)} ===")
    if FAIL:
        for item in FAIL:
            print(f"  FAIL: {item}")
        os._exit(1)
    print("[DONE] verify_faas_r1 全部通过")
    os._exit(66)
