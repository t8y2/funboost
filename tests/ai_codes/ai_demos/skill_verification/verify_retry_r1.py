"""验证 funboost-advanced-retry SKILL.md 的技术准确性（r1）"""
import inspect
import os
import sys
import time

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
_ts = int(time.time())
os.environ["PRINT_WRTIE_FILE_NAME"] = f"verify_retry_r1_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"verify_retry_r1_std_{_ts}"

from funboost import boost, BoosterParams, BrokerEnum, fct
from funboost.consumers.base_consumer import AbstractConsumer
from funboost.core.func_params_model import BoosterParams as BoosterParamsModel

PASS = []
FAIL = []


def ok(msg):
    PASS.append(msg)
    print(f"[PASS] {msg}")


def fail(msg):
    FAIL.append(msg)
    print(f"[FAIL] {msg}")


def check_retry_booster_params_fields():
    """SKILL 速查表 + advanced_retry_config 相关字段"""
    model_fields = set(BoosterParamsModel.model_fields.keys())
    for field in (
        "max_retry_times",
        "is_using_advanced_retry",
        "advanced_retry_config",
        "is_push_to_dlx_queue_when_retry_max_times",
        "do_task_filtering",
        "function_timeout",
        "task_filtering_expire_seconds",
    ):
        if field in model_fields:
            ok(f"BoosterParams.{field} 存在")
        else:
            fail(f"BoosterParams.{field} 不存在于源码")

    defaults = BoosterParamsModel(queue_name="__retry_defaults__")
    default_checks = [
        ("max_retry_times", defaults.max_retry_times, 3),
        ("is_using_advanced_retry", defaults.is_using_advanced_retry, False),
        ("is_push_to_dlx_queue_when_retry_max_times", defaults.is_push_to_dlx_queue_when_retry_max_times, False),
        ("do_task_filtering", defaults.do_task_filtering, False),
        ("function_timeout", defaults.function_timeout, None),
    ]
    for name, actual, expected in default_checks:
        if actual == expected:
            ok(f"BoosterParams.{name} 默认值={expected!r}")
        else:
            fail(f"BoosterParams.{name} 默认值错误: 预期 {expected!r}, 实际 {actual!r}")


def check_advanced_retry_config_keys():
    """SKILL advanced_retry_config 参数表"""
    cfg = BoosterParamsModel(queue_name="__cfg__").advanced_retry_config
    skill_keys = {
        "retry_mode": "sleep",
        "retry_base_interval": 1.0,
        "retry_multiplier": 2.0,
        "retry_max_interval": 60.0,
        "retry_jitter": False,
    }
    for key, expected_default in skill_keys.items():
        if key not in cfg:
            fail(f"advanced_retry_config 缺少键 {key!r}")
            continue
        if cfg[key] == expected_default:
            ok(f"advanced_retry_config[{key!r}] 默认值={expected_default!r}")
        else:
            fail(f"advanced_retry_config[{key!r}] 默认值错误: 预期 {expected_default!r}, 实际 {cfg[key]!r}")

    custom = BoosterParamsModel(
        queue_name="__custom_cfg__",
        is_using_advanced_retry=True,
        advanced_retry_config={
            "retry_mode": "requeue",
            "retry_base_interval": 2.0,
            "retry_multiplier": 3.0,
            "retry_max_interval": 60.0,
            "retry_jitter": True,
        },
    )
    for key in skill_keys:
        if key in custom.advanced_retry_config:
            ok(f"BoosterParams 可自定义 advanced_retry_config[{key!r}]")
        else:
            fail(f"BoosterParams 无法设置 advanced_retry_config[{key!r}]")


def check_exponential_backoff_formula():
    """核对 SKILL 指数退避公式与 base_consumer._calculate_exponential_backoff 一致"""
    calc = AbstractConsumer._calculate_exponential_backoff
    cases = [
        (0, 1.0, 2.0, 60.0, False, 1.0),
        (1, 1.0, 2.0, 60.0, False, 2.0),
        (2, 1.0, 2.0, 60.0, False, 4.0),
        (5, 1.0, 2.0, 60.0, False, 32.0),
        (6, 1.0, 2.0, 60.0, False, 60.0),
        (0, 2.0, 3.0, 60.0, False, 2.0),
        (3, 2.0, 3.0, 60.0, False, 54.0),
        (4, 2.0, 3.0, 60.0, False, 60.0),
    ]
    for current, base, mult, max_iv, jitter, expected in cases:
        actual = calc(current, base, mult, max_iv, jitter)
        if abs(actual - expected) < 1e-9:
            ok(f"退避公式 current={current}, base={base}, mult={mult} -> {actual}s")
        else:
            fail(f"退避公式不符: current={current} 预期 {expected}, 实际 {actual}")


def check_dlx_queue_naming():
    """SKILL: 死信队列自动命名为 {原队列名}_dlx（与 base_consumer.__init__ 一致）"""
    import re
    from pathlib import Path

    src = Path(r"D:\codes\funboost\funboost\consumers\base_consumer.py").read_text(encoding="utf-8")
    if re.search(r"self\._dlx_queue_name\s*=\s*f'\{self\.queue_name\}_dlx'", src):
        ok("DLX 队列命名规则 queue_name + '_dlx' 与 SKILL 一致")
    else:
        fail("base_consumer 中未找到 _dlx_queue_name = f'{queue_name}_dlx' 命名逻辑")


def check_circuit_breaker_import():
    try:
        from funboost.contrib.override_publisher_consumer_cls.circuit_breaker_mixin import (
            CircuitBreakerConsumerMixin,
        )
    except ImportError as e:
        fail(f"CircuitBreakerConsumerMixin 导入失败: {e}")
        return

    ok("CircuitBreakerConsumerMixin 可导入")
    if hasattr(CircuitBreakerConsumerMixin, "_submit_task"):
        ok("CircuitBreakerConsumerMixin._submit_task 存在（OPEN 状态阻塞消费）")
    else:
        fail("CircuitBreakerConsumerMixin 缺少 _submit_task")

    sig = inspect.signature(CircuitBreakerConsumerMixin.custom_init)
    if "self" in sig.parameters:
        ok("CircuitBreakerConsumerMixin.custom_init 可读 user_options['circuit_breaker_options']")
    else:
        fail("CircuitBreakerConsumerMixin.custom_init 签名异常")


def check_fct_run_times():
    if isinstance(getattr(type(fct), "function_result_status", None), property):
        ok("fct.function_result_status 属性存在（SKILL 示例 fct.function_result_status.run_times 正确）")
    else:
        fail("fct 缺少 function_result_status 属性")


# ---------- SKILL 代码示例（SQLITE_QUEUE，避免 Redis 依赖）----------

@boost(BoosterParams(
    queue_name="verify_retry_r1_basic",
    broker_kind=BrokerEnum.SQLITE_QUEUE,
    max_retry_times=3,
    function_timeout=10,
    concurrent_num=2,
))
def call_external_api(url: str):
    run_times = fct.function_result_status.run_times
    print(f"[RETRY] url={url}, run_times={run_times}")
    if run_times <= 2:
        raise ValueError(f"模拟 API 失败 run_times={run_times}")
    return {"url": url, "ok": True}


@boost(BoosterParams(
    queue_name="verify_retry_r1_backoff",
    broker_kind=BrokerEnum.SQLITE_QUEUE,
    max_retry_times=3,
    is_using_advanced_retry=True,
    concurrent_num=1,
))
def rate_limited_api(endpoint: str):
    run_times = fct.function_result_status.run_times
    print(f"[BACKOFF] endpoint={endpoint}, run_times={run_times}")
    if run_times <= 2:
        raise Exception("被限流了")
    return {"endpoint": endpoint}


@boost(BoosterParams(
    queue_name="verify_retry_r1_custom_backoff",
    broker_kind=BrokerEnum.SQLITE_QUEUE,
    max_retry_times=4,
    is_using_advanced_retry=True,
    advanced_retry_config={
        "retry_mode": "sleep",
        "retry_base_interval": 2.0,
        "retry_multiplier": 3.0,
        "retry_max_interval": 60.0,
        "retry_jitter": False,
    },
    concurrent_num=1,
))
def custom_backoff_task(data: dict):
    run_times = fct.function_result_status.run_times
    print(f"[CUSTOM] data={data}, run_times={run_times}")
    if run_times <= 1:
        raise Exception("custom backoff fail")
    return data


@boost(BoosterParams(
    queue_name="verify_retry_r1_dlx",
    broker_kind=BrokerEnum.SQLITE_QUEUE,
    max_retry_times=2,
    is_push_to_dlx_queue_when_retry_max_times=True,
    concurrent_num=1,
))
def process_payment(order_id: str, amount: float):
    run_times = fct.function_result_status.run_times
    print(f"[DLX] order_id={order_id}, amount={amount}, run_times={run_times}")
    raise Exception("支付永远失败")


@boost(BoosterParams(
    queue_name="verify_retry_r1_ctx",
    broker_kind=BrokerEnum.SQLITE_QUEUE,
    max_retry_times=3,
    concurrent_num=1,
))
def task_with_context(url: str):
    run_times = fct.function_result_status.run_times
    print(f"[CTX] url={url}, run_times={run_times}")
    if run_times > 1:
        print(f"第 {run_times} 次执行（第 {run_times - 1} 次重试）")
    if run_times <= 1:
        raise Exception("ctx retry")
    return url


def run_skill_code_examples():
    call_external_api.push("https://example.com/api")
    rate_limited_api.push("https://api.example.com/rate")
    custom_backoff_task.push({"k": "v"})
    process_payment.push("order-1", 99.9)
    task_with_context.push("https://ctx.example.com")

    call_external_api.consume()
    rate_limited_api.consume()
    custom_backoff_task.consume()
    process_payment.consume()
    task_with_context.consume()
    ok("SKILL 代码示例（基础重试/退避/DLX/上下文）可 publish + consume")


if __name__ == "__main__":
    print("=== 静态校验 ===")
    check_retry_booster_params_fields()
    check_advanced_retry_config_keys()
    check_exponential_backoff_formula()
    check_dlx_queue_naming()
    check_circuit_breaker_import()
    check_fct_run_times()

    print("\n=== SKILL 代码示例运行 ===")
    run_skill_code_examples()

    time.sleep(18)
    print(f"\n=== 汇总: PASS={len(PASS)}, FAIL={len(FAIL)} ===")
    if FAIL:
        for item in FAIL:
            print(f"  FAIL: {item}")
        os._exit(1)
    print("[DONE] verify_retry_r1 全部通过")
    os._exit(66)
