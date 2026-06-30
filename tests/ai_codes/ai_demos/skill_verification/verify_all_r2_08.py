"""Round2 验证：funboost-observability / funboost-troubleshooting SKILL vs 教程 c4b / c6 / c10

Observability:
  - PrometheusConsumerMixin 导入路径
  - user_options 键名（Prometheus / alert_options / periodic quota）

Troubleshooting:
  - enable_ctrl_c_quit_on_windows 可从 funboost 导入
  - enable_ctrl_c_quit_on_windows 最终 os._exit(44) 行为
"""
import inspect
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"verify_all_r2_08_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"verify_all_r2_08_std_{_ts}"

from funboost import BoosterParams, enable_ctrl_c_quit_on_windows
from funboost.utils import ctrl_c_end

PASS = []
FAIL = []


def ok(msg):
    PASS.append(msg)
    print(f"[PASS] {msg}")


def fail(msg):
    FAIL.append(msg)
    print(f"[FAIL] {msg}")


# ── 1. funboost-observability ───────────────────────────────────────────────


def check_observability_import_paths():
    """SKILL / c4b.md 4b.9：Mixin 从 contrib 子模块导入，不在 funboost 顶层"""
    expected_path = (
        "funboost.contrib.override_publisher_consumer_cls.funboost_promethus_mixin"
    )
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

    ok("observability 全部 mixin / MongoAlertMonitor 模块可导入")

    if PrometheusConsumerMixin.__module__ == expected_path:
        ok(f"PrometheusConsumerMixin 路径正确: {expected_path}")
    else:
        fail(
            f"PrometheusConsumerMixin 路径不符: 预期 {expected_path}, "
            f"实际 {PrometheusConsumerMixin.__module__}"
        )

    for cls in (
        PrometheusConsumerMixin,
        PrometheusPublisherMixin,
        AutoOtelConsumerMixin,
        AutoOtelPublisherMixin,
        AlertNotifierConsumerMixin,
        PeriodicQuotaConsumerMixin,
    ):
        if not cls.__module__.startswith(
            "funboost.contrib.override_publisher_consumer_cls."
        ):
            fail(f"{cls.__name__} 不在 contrib.override_publisher_consumer_cls 下")
        else:
            ok(f"{cls.__name__} 位于 contrib 子模块（与 SKILL / c4b 一致）")

    import funboost

    for name in (
        "PrometheusConsumerMixin",
        "AutoOtelConsumerMixin",
        "AlertNotifierConsumerMixin",
        "PeriodicQuotaConsumerMixin",
    ):
        if hasattr(funboost, name):
            fail(f"funboost 顶层不应导出 {name}（SKILL 说明 mixin 不在顶层）")
        else:
            ok(f"funboost 顶层未导出 {name}（符合 SKILL 说明）")

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


def check_observability_user_options_keys():
    """SKILL / c4b.md 4b.9.2 / c6.md 6.30.1 / c4b.md 4b.12：user_options 键名"""
    root = os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "..",
        "..",
        "funboost",
        "contrib",
        "override_publisher_consumer_cls",
    )
    checks = {
        "funboost_promethus_mixin.py": [
            "prometheus_pushgateway_url",
            "prometheus_push_interval",
            "prometheus_job_name",
        ],
        "alert_notifier_mixin.py": [
            "alert_options",
            "strategy",
            "failure_threshold",
            "errors_rate",
            "period",
            "min_calls",
            "alert_app",
            "webhook_url",
            "alert_interval",
            "exceptions",
        ],
        "periodic_quota_mixin.py": [
            "quota_limit",
            "quota_period",
            "sliding_window",
        ],
    }
    for filename, keys in checks.items():
        path = os.path.join(root, filename)
        with open(path, encoding="utf-8") as f:
            content = f.read()
        for key in keys:
            if f"'{key}'" in content or f'"{key}"' in content:
                ok(f"{filename} 含 user_options 键 {key!r}（SKILL / 教程一致）")
            else:
                fail(f"{filename} 未找到 user_options 键 {key!r}")


def check_observability_pushgateway_defaults():
    """SKILL 表格：prometheus_job_name 默认 'funboost'（源码 default）"""
    src = inspect.getsource(
        __import__(
            "funboost.contrib.override_publisher_consumer_cls.funboost_promethus_mixin",
            fromlist=["PrometheusPushGatewayBoosterParams"],
        ).PrometheusPushGatewayBoosterParams
    )
    if "'prometheus_job_name'" in src and "'funboost'" in src:
        ok("PrometheusPushGatewayBoosterParams 默认 prometheus_job_name='funboost'")
    else:
        fail("未在 PrometheusPushGatewayBoosterParams 中找到默认 job_name='funboost'")


# ── 2. funboost-troubleshooting ───────────────────────────────────────────


def check_troubleshooting_ctrl_c():
    """SKILL / c6.md 6.25b：enable_ctrl_c_quit_on_windows 导入与 os._exit(44)"""
    import funboost

    if hasattr(funboost, "enable_ctrl_c_quit_on_windows"):
        ok("funboost 顶层导出 enable_ctrl_c_quit_on_windows")
    else:
        fail("funboost 未导出 enable_ctrl_c_quit_on_windows")

    if enable_ctrl_c_quit_on_windows is ctrl_c_end.enable_ctrl_c_quit_on_windows:
        ok("from funboost import enable_ctrl_c_quit_on_windows 指向 ctrl_c_end 实现")
    else:
        fail("enable_ctrl_c_quit_on_windows 导入对象与 ctrl_c_end 不一致")

    if callable(enable_ctrl_c_quit_on_windows):
        ok("enable_ctrl_c_quit_on_windows 可调用")
    else:
        fail("enable_ctrl_c_quit_on_windows 不可调用")

    src = inspect.getsource(ctrl_c_end.enable_ctrl_c_quit_on_windows)
    if "time.sleep(2)" in src:
        ok("enable_ctrl_c_quit_on_windows 内含 time.sleep(2)（与 c6.md 6.25b.3 一致）")
    else:
        fail("enable_ctrl_c_quit_on_windows 未找到 time.sleep(2)")

    if "os._exit(44)" in src:
        ok("enable_ctrl_c_quit_on_windows 最终调用 os._exit(44)（与 SKILL / c6.md 一致）")
    else:
        fail("enable_ctrl_c_quit_on_windows 未找到 os._exit(44)")

    if "KeyboardInterrupt" in src:
        ok("enable_ctrl_c_quit_on_windows 捕获 KeyboardInterrupt（Ctrl+C）")
    else:
        fail("enable_ctrl_c_quit_on_windows 未捕获 KeyboardInterrupt")


def check_troubleshooting_tutorial_fields():
    """SKILL 引用的 BoosterParams / publisher API 与 c6.md 一致"""
    from funboost import boost, BrokerEnum
    from funboost.core.func_params_model import BoosterParams as BoosterParamsModel

    async_fields = (
        "specify_async_loop",
        "is_auto_start_specify_async_loop_in_child_thread",
    )
    model_fields = set(BoosterParamsModel.model_fields.keys())
    for field in async_fields:
        if field in model_fields:
            ok(f"BoosterParams.{field} 存在（c6.md 6.26 / SKILL §4）")
        else:
            fail(f"BoosterParams.{field} 不存在")

    @boost(BoosterParams(queue_name=f"verify_r2_08_pub_{_ts}", broker_kind=BrokerEnum.MEMORY_QUEUE))
    def _dummy(x):
        return x

    pub = _dummy.publisher
    for method in ("generate_msg_context_for_push", "generate_msg_context_for_publish"):
        if hasattr(pub, method):
            ok(f"publisher.{method} 存在（c6.md 6.31 / SKILL §3 步骤5）")
        else:
            fail(f"publisher.{method} 不存在")

    if hasattr(_dummy, "wait_for_possible_has_finish_all_tasks"):
        ok("wait_for_possible_has_finish_all_tasks 存在（c6.md 6.15 / SKILL §3 步骤7）")
    else:
        fail("wait_for_possible_has_finish_all_tasks 不存在")


def check_troubleshooting_config_path():
    """SKILL §2 / c6.md 6.18：配置通过 import funboost_config 加载"""
    import funboost.set_frame_config as sfc

    src = inspect.getsource(sfc)
    if "import_module('funboost_config')" in src or 'import_module("funboost_config")' in src:
        ok("set_frame_config 通过 import_module('funboost_config') 加载（SKILL / c6.md 6.18）")
    else:
        fail("set_frame_config 未找到 import_module('funboost_config')")


if __name__ == "__main__":
    print("=== funboost-observability SKILL 验证 ===")
    check_observability_import_paths()
    check_observability_user_options_keys()
    check_observability_pushgateway_defaults()

    print("\n=== funboost-troubleshooting SKILL 验证 ===")
    check_troubleshooting_ctrl_c()
    check_troubleshooting_tutorial_fields()
    check_troubleshooting_config_path()

    print(f"\n=== 汇总: PASS={len(PASS)}, FAIL={len(FAIL)} ===")
    if FAIL:
        for item in FAIL:
            print(f"  FAIL: {item}")
        os._exit(1)
    print("[DONE] verify_all_r2_08 全部通过")
    os._exit(66)
