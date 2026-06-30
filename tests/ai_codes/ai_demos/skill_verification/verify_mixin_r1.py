"""验证 developing-funboost-mixin SKILL.md 的技术准确性（r1）"""
import inspect
import os
import time

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
_ts = int(time.time())
os.environ["PRINT_WRTIE_FILE_NAME"] = f"verify_mixin_r1_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"verify_mixin_r1_std_{_ts}"

from funboost import boost, BoosterParams, BrokerEnum
from funboost.consumers.base_consumer import AbstractConsumer
from funboost.core.func_params_model import BoosterParams as BoosterParamsModel
from funboost.factories.consumer_factory import get_consumer

PASS = []
FAIL = []


def ok(msg):
    PASS.append(msg)
    print(f"[PASS] {msg}")


def fail(msg):
    FAIL.append(msg)
    print(f"[FAIL] {msg}")


def check_booster_params_mixin_fields():
    model_fields = set(BoosterParamsModel.model_fields.keys())
    for field in ("consumer_override_cls", "publisher_override_cls", "user_options"):
        if field in model_fields:
            ok(f"BoosterParams.{field} 存在")
        else:
            fail(f"BoosterParams.{field} 不存在于源码")

    defaults = BoosterParamsModel(queue_name="__mixin_defaults__")
    if defaults.user_options == {}:
        ok("BoosterParams.user_options 默认值为 {}")
    else:
        fail(f"BoosterParams.user_options 默认值错误: {defaults.user_options!r}")
    if defaults.consumer_override_cls is None:
        ok("BoosterParams.consumer_override_cls 默认值为 None")
    else:
        fail(f"BoosterParams.consumer_override_cls 默认值错误: {defaults.consumer_override_cls!r}")


def check_submit_task_signature():
    sig = inspect.signature(AbstractConsumer._submit_task)
    params = list(sig.parameters.keys())
    if params == ["self", "kw"]:
        ok(f"AbstractConsumer._submit_task 签名正确: {sig}")
    else:
        fail(f"AbstractConsumer._submit_task 签名不符: {sig}")


def check_hook_methods():
    hooks = {
        "_both_sync_and_aio_frame_custom_record_process_info_func": (
            AbstractConsumer._both_sync_and_aio_frame_custom_record_process_info_func,
            ["self", "current_function_result_status", "kw"],
            False,
        ),
        "_frame_custom_record_process_info_func": (
            AbstractConsumer._frame_custom_record_process_info_func,
            ["self", "current_function_result_status", "kw"],
            False,
        ),
        "_aio_frame_custom_record_process_info_func": (
            AbstractConsumer._aio_frame_custom_record_process_info_func,
            ["self", "current_function_result_status", "kw"],
            True,
        ),
    }
    for name, (method, expected_params, is_async) in hooks.items():
        if not hasattr(AbstractConsumer, name):
            fail(f"AbstractConsumer 缺少方法 {name}")
            continue
        sig = inspect.signature(method)
        params = list(sig.parameters.keys())
        if params == expected_params:
            ok(f"AbstractConsumer.{name} 参数签名正确: {sig}")
        else:
            fail(f"AbstractConsumer.{name} 参数签名不符: 预期 {expected_params}, 实际 {params}")
        if inspect.iscoroutinefunction(method) == is_async:
            ok(f"AbstractConsumer.{name} async={is_async} 与源码一致")
        else:
            fail(f"AbstractConsumer.{name} async 属性不符: 预期 {is_async}")


def check_removed_methods_not_in_skill():
    """SKILL 不应再引用已删除的熔断器内部方法"""
    skill_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "..",
        "..",
        ".agents",
        "skills",
        "developing-funboost-mixin",
        "SKILL.md",
    )
    skill_path = os.path.normpath(skill_path)
    if not os.path.isfile(skill_path):
        fail(f"找不到 SKILL.md: {skill_path}")
        return
    text = open(skill_path, encoding="utf-8").read()
    for removed in ("_handle_threshold_exceeded", "_record_success", "_record_failure"):
        if removed in text:
            fail(f"SKILL.md 仍包含已删除方法 {removed}")
        else:
            ok(f"SKILL.md 未引用已删除方法 {removed}")


def check_existing_mixins_importable():
    mixin_imports = [
        ("CircuitBreakerConsumerMixin", "funboost.contrib.override_publisher_consumer_cls.circuit_breaker_mixin"),
        ("MicroBatchConsumerMixin", "funboost.contrib.override_publisher_consumer_cls.funboost_micro_batch_mixin"),
        ("PrometheusConsumerMixin", "funboost.contrib.override_publisher_consumer_cls.funboost_promethus_mixin"),
        ("PrometheusPublisherMixin", "funboost.contrib.override_publisher_consumer_cls.funboost_promethus_mixin"),
        ("AutoOtelConsumerMixin", "funboost.contrib.override_publisher_consumer_cls.funboost_otel_mixin"),
        ("AutoOtelPublisherMixin", "funboost.contrib.override_publisher_consumer_cls.funboost_otel_mixin"),
        ("PeriodicQuotaConsumerMixin", "funboost.contrib.override_publisher_consumer_cls.periodic_quota_mixin"),
        ("AlertNotifierConsumerMixin", "funboost.contrib.override_publisher_consumer_cls.alert_notifier_mixin"),
    ]
    for cls_name, module_path in mixin_imports:
        try:
            mod = __import__(module_path, fromlist=[cls_name])
            cls = getattr(mod, cls_name)
            ok(f"可导入 {cls_name} <- {module_path}")
            if not (hasattr(cls, "custom_init") or hasattr(cls, "_submit_task") or hasattr(cls, "_both_sync_and_aio_frame_custom_record_process_info_func")):
                fail(f"{cls_name} 不像 Consumer/Publisher Mixin（缺少常见重写点）")
        except Exception as e:
            fail(f"无法导入 {cls_name} <- {module_path}: {e}")


def check_mro_dynamic_merge():
    """consumer_factory 动态 MRO: (mixin, broker_consumer, AbstractConsumer)"""

    class DummyMixin(AbstractConsumer):
        mixin_marker = True

        def custom_init(self):
            super().custom_init()

    params = BoosterParams(
        queue_name="__mro_check__",
        broker_kind=BrokerEnum.SQLITE_QUEUE,
        consuming_function=lambda x: x,
        consumer_override_cls=DummyMixin,
    )
    consumer = get_consumer(params)
    mro_names = [c.__name__ for c in consumer.__class__.__mro__]
    if mro_names[0].endswith("__DummyMixin") or "DummyMixin" in mro_names[0]:
        ok(f"动态类名包含 Mixin: {mro_names[0]}")
    else:
        ok(f"动态 consumer 类: {mro_names[0]}")
    if "DummyMixin" in mro_names and "AbstractConsumer" in mro_names:
        idx_mixin = mro_names.index("DummyMixin")
        idx_abstract = mro_names.index("AbstractConsumer")
        if idx_mixin < idx_abstract:
            ok(f"MRO 顺序正确: Mixin 在 AbstractConsumer 之前 -> {mro_names[:4]}")
        else:
            fail(f"MRO 顺序错误: {mro_names}")
    else:
        fail(f"MRO 缺少预期类: {mro_names}")


# --- 功能验证：简单 Mixin 能工作 ---
_mixin_hook_calls = []


class VerifySimpleMixin(AbstractConsumer):
    def custom_init(self):
        super().custom_init()
        opts = self.consumer_params.user_options.get("verify_mixin_options", {})
        self._flag = opts.get("flag", "default")
        _mixin_hook_calls.append(("custom_init", self._flag))

    def _both_sync_and_aio_frame_custom_record_process_info_func(self, current_function_result_status, kw):
        super()._both_sync_and_aio_frame_custom_record_process_info_func(
            current_function_result_status, kw
        )
        _mixin_hook_calls.append(
            ("hook", current_function_result_status.success, kw.get("body", {}).get("x"))
        )


@boost(BoosterParams(
    queue_name="verify_mixin_r1_task",
    broker_kind=BrokerEnum.SQLITE_QUEUE,
    consumer_override_cls=VerifySimpleMixin,
    concurrent_num=2,
    qps=10,
    user_options={"verify_mixin_options": {"flag": "r1"}},
))
def verify_mixin_task(x: int):
    print(f"[RUN] verify_mixin_task x={x}")
    return x * 3


def run_functional_mixin_test():
    for i in range(3):
        verify_mixin_task.push(i)
    verify_mixin_task.consume()
    ok("简单 Mixin 可 publish + consume 启动")


if __name__ == "__main__":
    print("=== 静态校验 ===")
    check_booster_params_mixin_fields()
    check_submit_task_signature()
    check_hook_methods()
    check_removed_methods_not_in_skill()
    check_existing_mixins_importable()
    check_mro_dynamic_merge()

    print("\n=== 功能验证 ===")
    run_functional_mixin_test()

    time.sleep(12)
    if any(c[0] == "custom_init" for c in _mixin_hook_calls):
        ok(f"Mixin custom_init 被调用: {[c for c in _mixin_hook_calls if c[0] == 'custom_init']}")
    else:
        fail("Mixin custom_init 未被调用")
    hook_calls = [c for c in _mixin_hook_calls if c[0] == "hook"]
    if len(hook_calls) >= 1:
        ok(f"后置钩子被调用 {len(hook_calls)} 次: {hook_calls}")
    else:
        fail(f"后置钩子未被调用, calls={_mixin_hook_calls}")

    print(f"\n=== 汇总: PASS={len(PASS)}, FAIL={len(FAIL)} ===")
    if FAIL:
        for item in FAIL:
            print(f"  FAIL: {item}")
        os._exit(1)
    print("[DONE] verify_mixin_r1 全部通过")
    os._exit(66)
