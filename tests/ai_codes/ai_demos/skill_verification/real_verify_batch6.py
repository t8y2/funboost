"""验证 batch6 三个 Skill 的代码示例能否真实运行（remote-deploy / observability / troubleshooting）"""
import inspect
import os
import sys
import time

os.environ["PYTHONPATH"] = r"D:\codes\funboost"
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = "real_verify_batch6_print.txt"
os.environ["SYS_STD_FILE_NAME"] = "real_verify_batch6_std.txt"

PASS_COUNT = 0
FAIL_COUNT = 0
INFO_LINES = []


def ok(msg):
    global PASS_COUNT
    PASS_COUNT += 1
    print(f"[PASS] {msg}")


def fail(msg):
    global FAIL_COUNT
    FAIL_COUNT += 1
    print(f"[FAIL] {msg}")


def info(msg):
    INFO_LINES.append(msg)
    print(f"[INFO] {msg}")


# ========== Skill 1: funboost-remote-deploy ==========


def check_remote_deploy_imports():
    """SKILL: fabric_deploy 不在顶层；正确路径为 core.fabric_deploy_helper"""
    try:
        import funboost.contrib.fabric_deploy  # noqa: F401

        fail("funboost.contrib.fabric_deploy 存在（SKILL 未推荐此路径）")
    except ImportError:
        info("funboost.contrib.fabric_deploy 不存在，跳过（SKILL 使用 core.fabric_deploy_helper）")

    try:
        from funboost.core.fabric_deploy_helper import fabric_deploy, kill_all_remote_tasks

        ok("from funboost.core.fabric_deploy_helper import fabric_deploy, kill_all_remote_tasks 可导入")
    except ImportError as e:
        fail(f"funboost.core.fabric_deploy_helper 导入失败: {e}")
        return

    import funboost

    if hasattr(funboost, "fabric_deploy"):
        fail("funboost 顶层不应导出 fabric_deploy（SKILL §1 导入方式说明）")
    else:
        ok("funboost 顶层未导出 fabric_deploy（与 SKILL 一致）")

    from funboost import boost, BoosterParams, BrokerEnum

    @boost(
        BoosterParams(
            queue_name="real_verify_batch6_fabric",
            broker_kind=BrokerEnum.MEMORY_QUEUE,
            create_logger_file=False,
        )
    )
    def _fabric_probe(x):
        return x

    if hasattr(_fabric_probe, "fabric_deploy") and callable(_fabric_probe.fabric_deploy):
        ok("@boost 函数对象具备 .fabric_deploy() 方法（SKILL 推荐用法）")
    else:
        fail("@boost 函数对象缺少 .fabric_deploy() 方法")

    for param in ("host", "port", "user", "password", "process_num", "invoke_runner_kwargs"):
        if param in inspect.signature(fabric_deploy).parameters:
            ok(f"fabric_deploy 含参数 {param!r}")
        else:
            fail(f"fabric_deploy 缺参数 {param!r}")

    if hasattr(_fabric_probe, "multi_process_consume") and hasattr(_fabric_probe, "mp_consume"):
        ok("multi_process_consume / mp_consume 方法存在（SKILL §4）")
    else:
        fail("multi_process_consume / mp_consume 方法缺失")


# ========== Skill 2: funboost-observability ==========


def check_observability_mixin_imports():
    """SKILL 导入路径速查：Mixin 从 contrib 子模块导入"""
    expected_prom = "funboost.contrib.override_publisher_consumer_cls.funboost_promethus_mixin"
    expected_otel = "funboost.contrib.override_publisher_consumer_cls.funboost_otel_mixin"
    expected_alert = "funboost.contrib.override_publisher_consumer_cls.alert_notifier_mixin"

    try:
        from funboost.contrib.override_publisher_consumer_cls.funboost_promethus_mixin import (
            PrometheusConsumerMixin,
            PrometheusPublisherMixin,
            PrometheusBoosterParams,
            PrometheusPushGatewayBoosterParams,
            start_prometheus_http_server,
        )
        from funboost.contrib.override_publisher_consumer_cls.funboost_otel_mixin import (
            AutoOtelConsumerMixin,
            AutoOtelPublisherMixin,
            OtelBoosterParams,
        )
        from funboost.contrib.override_publisher_consumer_cls.alert_notifier_mixin import (
            AlertNotifierConsumerMixin,
            AlertNotifierBoosterParams,
        )
        from funboost.contrib.override_publisher_consumer_cls.periodic_quota_mixin import (
            PeriodicQuotaConsumerMixin,
            PeriodicQuotaBoosterParams,
        )
        from funboost.core.mongo_alert_monitor import MongoAlertMonitor
    except ImportError as e:
        fail(f"observability mixin 导入失败: {e}")
        return

    ok("observability SKILL 列出的全部 mixin / MongoAlertMonitor 可导入")

    checks = [
        (PrometheusConsumerMixin, expected_prom),
        (AutoOtelConsumerMixin, expected_otel),
        (AlertNotifierConsumerMixin, expected_alert),
    ]
    for cls, expected_mod in checks:
        if cls.__module__ == expected_mod:
            ok(f"{cls.__name__} 导入路径正确: {expected_mod}")
        else:
            fail(f"{cls.__name__} 路径不符: 预期 {expected_mod}, 实际 {cls.__module__}")

    import funboost

    for name in (
        "PrometheusConsumerMixin",
        "AutoOtelConsumerMixin",
        "AlertNotifierConsumerMixin",
        "FunctionResultStatusPersistanceConfig",
    ):
        if name == "FunctionResultStatusPersistanceConfig":
            if hasattr(funboost, name):
                ok("FunctionResultStatusPersistanceConfig 可从 funboost 顶层导入（SKILL 速查表）")
            else:
                fail("FunctionResultStatusPersistanceConfig 未在 funboost 顶层导出")
            continue
        if hasattr(funboost, name):
            fail(f"funboost 顶层不应导出 {name}（SKILL 说明 mixin 不在顶层）")
        else:
            ok(f"funboost 顶层未导出 {name}（符合 SKILL）")

    if callable(start_prometheus_http_server):
        ok("start_prometheus_http_server 可调用")
    else:
        fail("start_prometheus_http_server 不可调用")

    for params_cls in (
        PrometheusBoosterParams,
        PrometheusPushGatewayBoosterParams,
        OtelBoosterParams,
        AlertNotifierBoosterParams,
        PeriodicQuotaBoosterParams,
    ):
        ok(f"{params_cls.__name__} 预配置 Params 类存在")

    if MongoAlertMonitor.__module__ == "funboost.core.mongo_alert_monitor":
        ok("MongoAlertMonitor 路径正确: funboost.core.mongo_alert_monitor")
    else:
        fail(f"MongoAlertMonitor 路径不符: {MongoAlertMonitor.__module__}")


def check_function_result_status_persistance_conf():
    """SKILL §5: function_result_status_persistance_conf 配置字段"""
    from funboost import FunctionResultStatusPersistanceConfig
    from funboost.core.func_params_model import BoosterParams as BoosterParamsModel
    from pydantic import ValidationError

    skill_fields = [
        "is_save_status",
        "is_save_result",
        "expire_seconds",
        "is_use_bulk_insert",
        "table_name",
    ]
    model_fields = set(FunctionResultStatusPersistanceConfig.model_fields.keys())
    for field in skill_fields:
        if field in model_fields:
            ok(f"FunctionResultStatusPersistanceConfig.{field} 存在")
        else:
            fail(f"FunctionResultStatusPersistanceConfig.{field} 不存在")

    if "function_result_status_persistance_conf" in BoosterParamsModel.model_fields:
        ok("BoosterParams.function_result_status_persistance_conf 字段存在")
    else:
        fail("BoosterParams.function_result_status_persistance_conf 字段不存在")

    try:
        FunctionResultStatusPersistanceConfig(is_save_status=False, is_save_result=True)
        fail("is_save_result=True 且 is_save_status=False 应被拒绝（SKILL 常见陷阱 §3）")
    except ValueError:
        ok("is_save_result=True 时 is_save_status 必须为 True（ValueError 校验生效）")

    conf = FunctionResultStatusPersistanceConfig(
        is_save_status=True,
        is_save_result=True,
        expire_seconds=7 * 24 * 3600,
        table_name="my_project_all_tasks",
        is_use_bulk_insert=True,
    )
    if conf.expire_seconds == 604800 and conf.table_name == "my_project_all_tasks":
        ok("FunctionResultStatusPersistanceConfig 示例实例化成功")
    else:
        fail("FunctionResultStatusPersistanceConfig 示例实例化字段值不符")

    try:
        BoosterParamsModel(
            queue_name="real_verify_batch6_persist",
            function_result_status_persistance_conf=FunctionResultStatusPersistanceConfig(
                is_save_status=True,
                is_save_result=True,
            ),
        )
        ok("BoosterParams 可接受 function_result_status_persistance_conf 配置")
    except ValidationError as e:
        fail(f"BoosterParams 接受 persistance_conf 失败: {e}")


# ========== Skill 3: funboost-troubleshooting ==========


def check_troubleshooting_ctrl_c_and_run_forever():
    """SKILL §1: enable_ctrl_c_quit_on_windows；关键词 run_forever"""
    from funboost import enable_ctrl_c_quit_on_windows
    from funboost.utils import ctrl_c_end
    import funboost

    if hasattr(funboost, "enable_ctrl_c_quit_on_windows"):
        ok("from funboost import enable_ctrl_c_quit_on_windows 可导入")
    else:
        fail("funboost 未导出 enable_ctrl_c_quit_on_windows")

    if enable_ctrl_c_quit_on_windows is ctrl_c_end.enable_ctrl_c_quit_on_windows:
        ok("enable_ctrl_c_quit_on_windows 指向 funboost.utils.ctrl_c_end 实现")
    else:
        fail("enable_ctrl_c_quit_on_windows 导入对象与 ctrl_c_end 不一致")

    src = inspect.getsource(ctrl_c_end.enable_ctrl_c_quit_on_windows)
    if "time.sleep(2)" in src and "os._exit(44)" in src:
        ok("enable_ctrl_c_quit_on_windows 含 time.sleep(2) 与 os._exit(44)（SKILL §1.2）")
    else:
        fail("enable_ctrl_c_quit_on_windows 源码与 SKILL 描述不符")

    ctrl_c_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "..", "funboost", "utils", "ctrl_c_end.py"
    )
    if os.path.isfile(os.path.normpath(ctrl_c_path)):
        ok("ctrl_c_end 源码路径存在: funboost/utils/ctrl_c_end.py")
    else:
        fail(f"ctrl_c_end 源码路径不存在: {ctrl_c_path}")

    if hasattr(funboost, "run_forever"):
        ok("from funboost import run_forever 可导入")
    else:
        fail("from funboost import run_forever 不可导入（__init__ 已注释导出）")

    try:
        from funboost.core.helper_funs import run_forever  # noqa: F401

        ok("from funboost.core.helper_funs import run_forever 可导入")
    except ImportError:
        fail("from funboost.core.helper_funs import run_forever 不可导入（helper_funs 中已注释）")


def check_troubleshooting_log_and_config_paths():
    """SKILL §5 日志配置；§2 PYTHONPATH / funboost_config 加载"""
    from funboost.core.func_params_model import BoosterParams as BoosterParamsModel
    from funboost.funboost_config_deafult import FunboostCommonConfig
    import funboost.set_frame_config as sfc

    log_path = os.environ.get("LOG_PATH")
    if log_path == r"D:\pythonlogs\ai_console_outs":
        ok(f"LOG_PATH 环境变量已设置: {log_path}")
    else:
        fail(f"LOG_PATH 环境变量不符: {log_path!r}")

    for env_key in ("PRINT_WRTIE_FILE_NAME", "SYS_STD_FILE_NAME"):
        if os.environ.get(env_key):
            ok(f"{env_key} 环境变量已设置: {os.environ[env_key]!r}")
        else:
            fail(f"{env_key} 环境变量未设置")

    for field in ("log_level", "create_logger_file", "log_filename"):
        if field in BoosterParamsModel.model_fields:
            ok(f"BoosterParams.{field} 存在（SKILL §5.2 日志字段）")
        else:
            fail(f"BoosterParams.{field} 不存在")

    for field in ("SHOW_HOW_FUNBOOST_CONFIG_SETTINGS", "FUNBOOST_PROMPT_LOG_LEVEL", "KEEPALIVETIMETHREAD_LOG_LEVEL"):
        if hasattr(FunboostCommonConfig, field):
            ok(f"FunboostCommonConfig.{field} 存在（SKILL §5.3 减少刷屏）")
        else:
            fail(f"FunboostCommonConfig.{field} 不存在")

    sfc_src = inspect.getsource(sfc)
    if "import_module('funboost_config')" in sfc_src or 'import_module("funboost_config")' in sfc_src:
        ok("set_frame_config 通过 import_module('funboost_config') 加载（SKILL §2.3）")
    else:
        fail("set_frame_config 未找到 import_module('funboost_config')")

    set_frame_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "..", "funboost", "set_frame_config.py"
    )
    if os.path.isfile(os.path.normpath(set_frame_path)):
        ok("配置加载源码路径存在: funboost/set_frame_config.py")
    else:
        fail(f"set_frame_config.py 路径不存在: {set_frame_path}")


def check_troubleshooting_runtime_helpers():
    """SKILL §3 / §7: publisher 预览消息、wait_for_possible_has_finish_all_tasks"""
    from funboost import boost, BoosterParams, BrokerEnum

    @boost(
        BoosterParams(
            queue_name="real_verify_batch6_trouble",
            broker_kind=BrokerEnum.MEMORY_QUEUE,
            create_logger_file=False,
        )
    )
    def _dummy(x, y=1):
        return x + y

    pub = _dummy.publisher
    for method in ("generate_msg_context_for_push", "generate_msg_context_for_publish"):
        if hasattr(pub, method) and callable(getattr(pub, method)):
            ok(f"publisher.{method} 存在且可调用（SKILL §3 步骤5）")
        else:
            fail(f"publisher.{method} 不存在或不可调用")

    try:
        push_ctx = pub.generate_msg_context_for_push(1, 2)
        publish_ctx = pub.generate_msg_context_for_publish({"x": 1, "y": 2})
        if isinstance(push_ctx, dict) and isinstance(publish_ctx, dict):
            ok("generate_msg_context_for_push/publish 返回 dict（SKILL 示例可运行）")
        else:
            fail(f"generate_msg_context 返回类型异常: {type(push_ctx)}, {type(publish_ctx)}")
    except Exception as e:
        fail(f"generate_msg_context 调用失败: {e}")

    if hasattr(_dummy, "wait_for_possible_has_finish_all_tasks"):
        ok("wait_for_possible_has_finish_all_tasks 存在（SKILL §3 步骤7）")
    else:
        fail("wait_for_possible_has_finish_all_tasks 不存在")


if __name__ == "__main__":
    print("=== real_verify_batch6: funboost-remote-deploy ===")
    check_remote_deploy_imports()

    print("\n=== real_verify_batch6: funboost-observability ===")
    check_observability_mixin_imports()
    check_function_result_status_persistance_conf()

    print("\n=== real_verify_batch6: funboost-troubleshooting ===")
    check_troubleshooting_ctrl_c_and_run_forever()
    check_troubleshooting_log_and_config_paths()
    check_troubleshooting_runtime_helpers()

    print(f"\n=== 汇总: PASS={PASS_COUNT}, FAIL={FAIL_COUNT}, INFO={len(INFO_LINES)} ===")
    time.sleep(10)
    os._exit(66)
