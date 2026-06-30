"""验证 4 个新 Agent Skill 的技术准确性（r1）

覆盖:
- funboost-spider-crawling
- funboost-remote-deploy
- funboost-observability
- funboost-troubleshooting
"""
import inspect
import os
import time

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
_ts = int(time.time())
os.environ["PRINT_WRTIE_FILE_NAME"] = f"verify_new4_r1_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"verify_new4_r1_std_{_ts}"

from funboost import (
    boost,
    BoosterParams,
    BrokerEnum,
    FunctionResultStatusPersistanceConfig,
    enable_ctrl_c_quit_on_windows,
)
from funboost.core.booster import Booster
from funboost.core.fabric_deploy_helper import fabric_deploy, kill_all_remote_tasks
from funboost.core.func_params_model import BoosterParams as BoosterParamsModel
from funboost.core.mongo_alert_monitor import MongoAlertMonitor
from funboost.utils import ctrl_c_end

PASS = []
FAIL = []


def ok(msg):
    PASS.append(msg)
    print(f"[PASS] {msg}")


def fail(msg):
    FAIL.append(msg)
    print(f"[FAIL] {msg}")


def check_callable_params(func, expected_params, label):
    sig = inspect.signature(func)
    params = list(sig.parameters.keys())
    if params == expected_params:
        ok(f"{label} 签名参数: {params}")
    else:
        fail(f"{label} 签名不符: 预期 {expected_params}, 实际 {params}")


def check_has_attrs(obj, attrs, label):
    for attr in attrs:
        if hasattr(obj, attr):
            ok(f"{label}.{attr} 存在")
        else:
            fail(f"{label}.{attr} 不存在")


# ── 1. funboost-spider-crawling ─────────────────────────────────────────────


def check_spider_imports():
    try:
        from funboost.contrib.funspider import (
            SimpleSpiderClient,
            AsyncSpiderClient,
            SpiderResponse,
            SpiderItem,
            Field,
            create_engine,
            create_async_engine,
        )
    except ImportError as e:
        fail(f"funspider 导入失败: {e}")
        return

    ok("funboost.contrib.funspider 核心符号可导入")
    for cls in (SimpleSpiderClient, AsyncSpiderClient, SpiderResponse, SpiderItem):
        ok(f"funspider.{cls.__name__} 类存在")

    check_callable_params(
        SimpleSpiderClient.__init__,
        ["self", "retry_times", "timeout", "proxy_getter_list", "user_agents"],
        "SimpleSpiderClient.__init__",
    )
    check_callable_params(
        AsyncSpiderClient.__init__,
        ["self", "retry_times", "timeout", "proxy_getter_list", "user_agents"],
        "AsyncSpiderClient.__init__",
    )
    for method in ("get", "post", "request", "close"):
        if hasattr(SimpleSpiderClient, method):
            ok(f"SimpleSpiderClient.{method} 存在")
        else:
            fail(f"SimpleSpiderClient.{method} 不存在")
    for method in ("get", "post", "request", "aclose"):
        if hasattr(AsyncSpiderClient, method):
            ok(f"AsyncSpiderClient.{method} 存在")
        else:
            fail(f"AsyncSpiderClient.{method} 不存在")

    spider_resp_methods = ("xpath", "css", "re", "re_first", "resp_dict", "text")
    check_has_attrs(SpiderResponse, spider_resp_methods, "SpiderResponse")

    item_methods = (
        "insert",
        "upsert",
        "bulk_upsert",
        "aio_insert",
        "aio_upsert",
        "mongo_upsert",
        "aio_mongo_upsert",
        "ensure_mongo_indexes",
        "create_table",
    )
    check_has_attrs(SpiderItem, item_methods, "SpiderItem")

    if "task_filtering_expire_seconds" in BoosterParamsModel.model_fields:
        ok("BoosterParams.task_filtering_expire_seconds 存在（爬虫去重 skill 引用）")
    else:
        fail("BoosterParams.task_filtering_expire_seconds 不存在")


# ── 2. funboost-remote-deploy ───────────────────────────────────────────────


def check_fabric_deploy():
    check_callable_params(
        fabric_deploy,
        [
            "booster",
            "host",
            "port",
            "user",
            "password",
            "path_pattern_exluded_tuple",
            "file_suffix_tuple_exluded",
            "only_upload_within_the_last_modify_time",
            "file_volume_limit",
            "sftp_log_level",
            "extra_shell_str",
            "invoke_runner_kwargs",
            "python_interpreter",
            "process_num",
            "pkey_file_path",
        ],
        "fabric_deploy",
    )
    check_callable_params(
        kill_all_remote_tasks,
        ["host", "port", "user", "password"],
        "kill_all_remote_tasks",
    )

    defaults = inspect.signature(fabric_deploy).parameters
    expected_defaults = {
        "path_pattern_exluded_tuple": ('/.git/', '/.idea/', '/dist/', '/build/'),
        "file_suffix_tuple_exluded": ('.pyc', '.log', '.gz'),
        "only_upload_within_the_last_modify_time": 3650 * 24 * 60 * 60,
        "file_volume_limit": 1000 * 1000,
        "sftp_log_level": 20,
        "python_interpreter": "python3",
        "process_num": 1,
        "invoke_runner_kwargs": {"hide": None, "pty": True, "warn": False},
    }
    for key, val in expected_defaults.items():
        actual = defaults[key].default
        if actual == val:
            ok(f"fabric_deploy.{key} 默认值正确")
        else:
            fail(f"fabric_deploy.{key} 默认值不符: 预期 {val!r}, 实际 {actual!r}")

    if hasattr(Booster, "fabric_deploy"):
        ok("Booster.fabric_deploy 方法存在")
    else:
        fail("Booster.fabric_deploy 方法不存在")

    import funboost

    if hasattr(funboost, "fabric_deploy"):
        fail("funboost 顶层仍导出 fabric_deploy（skill 说应未导出）")
    else:
        ok("funboost 顶层未导出 fabric_deploy（与 skill 一致）")

    @boost(BoosterParams(queue_name=f"verify_fabric_{_ts}", broker_kind=BrokerEnum.MEMORY_QUEUE))
    def _fabric_dummy(x):
        return x

    if hasattr(_fabric_dummy, "fabric_deploy"):
        ok("@boost 函数对象带 .fabric_deploy 方法")
    else:
        fail("@boost 函数对象缺少 .fabric_deploy 方法")


# ── 3. funboost-observability ───────────────────────────────────────────────


def check_observability_imports():
    try:
        from funboost.contrib.override_publisher_consumer_cls.funboost_promethus_mixin import (
            PrometheusConsumerMixin,
            PrometheusPublisherMixin,
            PrometheusBoosterParams,
            PrometheusPushGatewayBoosterParams,
            start_prometheus_http_server,
            TASK_TOTAL,
            TASK_LATENCY,
            TASK_RETRIES,
            QUEUE_MSG_COUNT,
            PUBLISH_TOTAL,
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
    except ImportError as e:
        fail(f"observability mixin 导入失败: {e}")
        return

    ok("observability 全部 mixin 模块可导入")
    def exported_metric_name(metric):
        """prometheus_client Counter 的 _name 不含 _total，但 /metrics 导出时会加后缀"""
        if getattr(metric, "_type", None) == "counter":
            return metric._name + "_total"
        return metric._name

    metric_names = {
        TASK_TOTAL: "funboost_task_total",
        TASK_LATENCY: "funboost_task_latency_seconds",
        TASK_RETRIES: "funboost_task_retries_total",
        QUEUE_MSG_COUNT: "funboost_queue_msg_count",
        PUBLISH_TOTAL: "funboost_publish_total",
    }
    for metric, name in metric_names.items():
        exported = exported_metric_name(metric)
        if exported == name:
            ok(f"Prometheus 指标 {name} 存在（导出名）")
        else:
            fail(f"Prometheus 指标名不符: 预期 {name}, 实际 {exported}")

    sig = inspect.signature(start_prometheus_http_server)
    if "port" in sig.parameters and sig.parameters["port"].default == 8000:
        ok("start_prometheus_http_server(port=8000) 默认端口正确")
    else:
        fail(f"start_prometheus_http_server 签名不符: {sig}")

    for cls in (
        PrometheusBoosterParams,
        PrometheusPushGatewayBoosterParams,
        OtelBoosterParams,
        AlertNotifierBoosterParams,
        PeriodicQuotaBoosterParams,
    ):
        ok(f"{cls.__name__} 预配置 Params 类存在")

    persist_fields = (
        "is_save_status",
        "is_save_result",
        "expire_seconds",
        "is_use_bulk_insert",
        "table_name",
    )
    model_fields = set(FunctionResultStatusPersistanceConfig.model_fields.keys())
    for field in persist_fields:
        if field in model_fields:
            ok(f"FunctionResultStatusPersistanceConfig.{field} 存在")
        else:
            fail(f"FunctionResultStatusPersistanceConfig.{field} 不存在")

    default_expire = FunctionResultStatusPersistanceConfig().expire_seconds
    if default_expire == 7 * 24 * 3600:
        ok("FunctionResultStatusPersistanceConfig.expire_seconds 默认 7 天")
    else:
        fail(f"expire_seconds 默认值不符: {default_expire}")

    try:
        FunctionResultStatusPersistanceConfig(is_save_status=False, is_save_result=True)
        fail("is_save_result=True 且 is_save_status=False 应抛 ValueError")
    except ValueError:
        ok("is_save_result 依赖 is_save_status 校验与 skill 一致")

    mongo_sig = inspect.signature(MongoAlertMonitor.__init__)
    mongo_params = list(mongo_sig.parameters.keys())
    expected_mongo = [
        "self",
        "boosters",
        "alert_app",
        "webhook_url",
        "window_seconds",
        "failure_count",
        "errors_rate",
        "min_calls",
        "poll_interval",
        "alert_interval",
    ]
    if mongo_params == expected_mongo:
        ok(f"MongoAlertMonitor.__init__ 参数与 skill 一致")
    else:
        fail(f"MongoAlertMonitor.__init__ 参数不符: {mongo_params}")

    if hasattr(MongoAlertMonitor, "start"):
        ok("MongoAlertMonitor.start 方法存在")
    else:
        fail("MongoAlertMonitor.start 方法不存在")


def check_user_options_keys_in_source():
    """读取 mixin 源码，确认 skill 文档中的 user_options 键名存在"""
    root = os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "..", "funboost", "contrib", "override_publisher_consumer_cls"
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
        "periodic_quota_mixin.py": ["quota_limit", "quota_period", "sliding_window"],
    }
    for filename, keys in checks.items():
        path = os.path.join(root, filename)
        with open(path, encoding="utf-8") as f:
            content = f.read()
        for key in keys:
            if f"'{key}'" in content or f'"{key}"' in content:
                ok(f"{filename} 含 user_options 键 {key!r}")
            else:
                fail(f"{filename} 未找到 user_options 键 {key!r}")


# ── 4. funboost-troubleshooting ─────────────────────────────────────────────


def check_troubleshooting():
    if enable_ctrl_c_quit_on_windows is ctrl_c_end.enable_ctrl_c_quit_on_windows:
        ok("from funboost import enable_ctrl_c_quit_on_windows 路径正确")
    else:
        fail("enable_ctrl_c_quit_on_windows 导入对象不一致")

    src = inspect.getsource(ctrl_c_end.enable_ctrl_c_quit_on_windows)
    if "time.sleep(2)" in src:
        ok("enable_ctrl_c_quit_on_windows 内含 time.sleep(2)")
    else:
        fail("enable_ctrl_c_quit_on_windows 未找到 time.sleep(2)")
    if "os._exit(44)" in src:
        ok("enable_ctrl_c_quit_on_windows 最终 os._exit(44)")
    else:
        fail("enable_ctrl_c_quit_on_windows 未找到 os._exit(44)")

    async_fields = (
        "specify_async_loop",
        "is_auto_start_specify_async_loop_in_child_thread",
    )
    model_fields = set(BoosterParamsModel.model_fields.keys())
    for field in async_fields:
        if field in model_fields:
            ok(f"BoosterParams.{field} 存在（event loop 排查 skill 引用）")
        else:
            fail(f"BoosterParams.{field} 不存在")

    @boost(BoosterParams(queue_name=f"verify_pub_{_ts}", broker_kind=BrokerEnum.MEMORY_QUEUE))
    def _pub_dummy(x):
        return x

    pub = _pub_dummy.publisher
    for method in ("generate_msg_context_for_push", "generate_msg_context_for_publish"):
        if hasattr(pub, method):
            ok(f"publisher.{method} 存在")
        else:
            fail(f"publisher.{method} 不存在")

    if hasattr(_pub_dummy, "wait_for_possible_has_finish_all_tasks"):
        ok("booster.wait_for_possible_has_finish_all_tasks 存在")
    else:
        fail("booster.wait_for_possible_has_finish_all_tasks 不存在")


def main():
    print("=" * 60)
    print("verify_new4_r1: 4 个 Skill 技术准确性验证")
    print("=" * 60)

    check_spider_imports()
    check_fabric_deploy()
    check_observability_imports()
    check_user_options_keys_in_source()
    check_troubleshooting()

    print("=" * 60)
    print(f"PASS: {len(PASS)}  FAIL: {len(FAIL)}")
    if FAIL:
        print("\n失败项:")
        for item in FAIL:
            print(f"  - {item}")
    print("=" * 60)
    time.sleep(1)
    os._exit(0 if not FAIL else 1)


if __name__ == "__main__":
    main()
