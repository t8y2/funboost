"""验证 funboost-funweb-ops SKILL.md 的技术准确性（r1）"""
import inspect
import os
import time

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
_ts = int(time.time())
os.environ["PRINT_WRTIE_FILE_NAME"] = f"verify_funweb_r1_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"verify_funweb_r1_std_{_ts}"

from funboost import BoosterParams, FunctionResultStatusPersistanceConfig
from funboost.core.func_params_model import BoosterParams as BoosterParamsModel

PASS = []
FAIL = []


def ok(msg):
    PASS.append(msg)
    print(f"[PASS] {msg}")


def fail(msg):
    FAIL.append(msg)
    print(f"[FAIL] {msg}")


def check_start_funboost_web_manager_import():
    """SKILL: from funboost.funweb.app import start_funboost_web_manager"""
    from funboost.funweb.app import start_funboost_web_manager as fn1

    ok("from funboost.funweb.app import start_funboost_web_manager 可导入")

    try:
        from funboost.funboost_web_manager.app import start_funboost_web_manager as fn2

        if fn1 is fn2:
            ok("等价路径 funboost.funboost_web_manager.app 指向同一函数")
        else:
            fail("funboost_web_manager.app 与 funweb.app 的 start_funboost_web_manager 不是同一对象")
    except ImportError as e:
        fail(f"等价导入路径 funboost.funboost_web_manager.app 失败: {e}")


def check_start_funboost_web_manager_signature():
    """SKILL: host, port, block, debug, care_project_name 参数及默认值"""
    from funboost.funweb.app import start_funboost_web_manager

    sig = inspect.signature(start_funboost_web_manager)
    param_names = list(sig.parameters.keys())
    expected_params = ["host", "port", "block", "debug", "care_project_name"]
    if param_names == expected_params:
        ok(f"start_funboost_web_manager 参数名: {param_names}")
    else:
        fail(f"参数名不符: 预期 {expected_params}, 实际 {param_names}")

    defaults = {
        "host": "0.0.0.0",
        "port": 27018,
        "block": False,
        "debug": False,
        "care_project_name": None,
    }
    for name, expected in defaults.items():
        actual = sig.parameters[name].default
        if actual == expected:
            ok(f"start_funboost_web_manager.{name} 默认值={expected!r}")
        else:
            fail(f"start_funboost_web_manager.{name} 默认值错误: 预期 {expected!r}, 实际 {actual!r}")


def check_booster_params_heartbeat_field():
    """SKILL: is_send_consumer_heartbeat_to_redis 字段"""
    if "is_send_consumer_heartbeat_to_redis" in BoosterParamsModel.model_fields:
        ok("BoosterParams.is_send_consumer_heartbeat_to_redis 字段存在")
    else:
        fail("BoosterParams.is_send_consumer_heartbeat_to_redis 字段不存在")

    defaults = BoosterParamsModel(queue_name="__funweb_verify__")
    if defaults.is_send_consumer_heartbeat_to_redis is False:
        ok("BoosterParams.is_send_consumer_heartbeat_to_redis 默认 False（SKILL 要求显式设 True）")
    else:
        fail(f"默认应为 False, 实际 {defaults.is_send_consumer_heartbeat_to_redis!r}")

    bp = BoosterParams(
        queue_name="__funweb_verify__",
        is_send_consumer_heartbeat_to_redis=True,
    )
    if bp.is_send_consumer_heartbeat_to_redis is True:
        ok("BoosterParams(is_send_consumer_heartbeat_to_redis=True) 可设置")
    else:
        fail("无法将 is_send_consumer_heartbeat_to_redis 设为 True")


def check_related_booster_params_fields():
    """SKILL WebOpsBoosterParams 示例中的其他字段"""
    for field in (
        "project_name",
        "is_using_rpc_mode",
        "function_result_status_persistance_conf",
    ):
        if field in BoosterParamsModel.model_fields:
            ok(f"BoosterParams.{field} 存在")
        else:
            fail(f"BoosterParams.{field} 不存在")

    conf = FunctionResultStatusPersistanceConfig(
        is_save_result=True,
        is_save_status=True,
        expire_seconds=7 * 24 * 3600,
    )
    if conf.is_save_result and conf.is_save_status:
        ok("FunctionResultStatusPersistanceConfig 示例参数可构造")
    else:
        fail("FunctionResultStatusPersistanceConfig 构造异常")


def check_funweb_directory_structure():
    """SKILL §1 funweb 目录结构"""
    root = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "funboost", "funweb")
    root = os.path.normpath(root)
    expected = [
        "app.py",
        "functions.py",
        "flask_bps/dashboard.py",
        "flask_bps/queue_alerts.py",
        "flask_bps/script_deploy.py",
        "flask_bps/system_monitor.py",
        "flask_bps/log_viewer.py",
        "templates/fun_result_table.html",
        "templates/queue_op.html",
        "templates/timing_jobs_management.html",
    ]
    for rel in expected:
        path = os.path.join(root, rel)
        if os.path.isfile(path):
            ok(f"funweb/{rel} 存在")
        else:
            fail(f"funweb/{rel} 不存在")


def check_flask_app_basics():
    """SKILL: 默认登录、蓝图、定时任务 FaaS 路由"""
    from funboost.funweb import app as funweb_app_module

    app = funweb_app_module.app
    users = {u["user_name"]: u["password"] for u in funweb_app_module.users}
    if users.get("admin") == "123456":
        ok("默认登录 admin/123456 与源码 users 一致")
    else:
        fail(f"默认登录不符: {users!r}")

    bp_names = {bp.name for bp in app.blueprints.values()}
    for name in ("funboost", "deploy", "monitor", "log_viewer", "dashboard", "queue_alerts"):
        if name in bp_names:
            ok(f"Flask 蓝图 {name!r} 已注册")
        else:
            fail(f"Flask 蓝图 {name!r} 未注册")

    timing_route_found = False
    for rule in app.url_map.iter_rules():
        if rule.rule == "/funboost/get_timing_jobs" and "GET" in rule.methods:
            timing_route_found = True
            break
    if timing_route_found:
        ok("GET /funboost/get_timing_jobs 路由存在（flask_blueprint）")
    else:
        fail("GET /funboost/get_timing_jobs 路由缺失")


def check_not_exported_from_funboost_init():
    """SKILL 未声称顶层导出；记录事实"""
    import funboost

    if hasattr(funboost, "start_funboost_web_manager"):
        fail("funboost 顶层不应导出 start_funboost_web_manager，但已导出")
    else:
        ok("start_funboost_web_manager 不在 funboost 顶层 __init__（需从 funboost.funweb.app 导入）")


def check_heartbeat_interval_constant():
    """SKILL: 消费者每 10 秒向 Redis 上报心跳"""
    from funboost.consumers.base_consumer import DistributedConsumerStatistics

    interval = getattr(DistributedConsumerStatistics, "SEND_HEARTBEAT_INTERVAL", None)
    if interval == 10:
        ok("DistributedConsumerStatistics.SEND_HEARTBEAT_INTERVAL=10")
    else:
        fail(f"心跳间隔应为 10 秒, 实际 {interval!r}")


if __name__ == "__main__":
    print("=== funboost-funweb-ops SKILL 静态校验 ===")
    check_start_funboost_web_manager_import()
    check_start_funboost_web_manager_signature()
    check_booster_params_heartbeat_field()
    check_related_booster_params_fields()
    check_funweb_directory_structure()
    check_flask_app_basics()
    check_not_exported_from_funboost_init()
    check_heartbeat_interval_constant()

    print(f"\n=== 汇总: PASS={len(PASS)}, FAIL={len(FAIL)} ===")
    if FAIL:
        for item in FAIL:
            print(f"  FAIL: {item}")
        os._exit(1)
    print("[DONE] verify_funweb_r1 全部通过")
    os._exit(66)
