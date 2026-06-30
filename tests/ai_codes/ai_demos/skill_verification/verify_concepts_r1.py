"""验证 understanding-funboost-concepts skill 中的核心概念与 API 声明"""
import os
import sys
import time

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"verify_concepts_r1_{int(time.time())}"
os.environ["SYS_STD_FILE_NAME"] = f"verify_concepts_r1_std_{int(time.time())}"

from funboost import (
    boost,
    BoosterParams,
    BrokerEnum,
    ConcurrentModeEnum,
    TaskOptions,
    fct,
    enable_ctrl_c_quit_on_windows,
)
from funboost.core.func_params_model import BoosterParams as BoosterParamsModel
from pydantic import ValidationError


def check_booster_params_fields():
    required_fields = [
        "queue_name",
        "broker_kind",
        "concurrent_mode",
        "concurrent_num",
        "qps",
        "max_retry_times",
        "function_timeout",
        "is_using_rpc_mode",
        "consumer_override_cls",
        "user_options",
        "broker_exclusive_config",
        "is_using_advanced_retry",
    ]
    model_fields = set(BoosterParamsModel.model_fields.keys())
    missing = [f for f in required_fields if f not in model_fields]
    assert not missing, f"BoosterParams 缺少字段: {missing}"
    print(f"[OK] BoosterParams 字段验证通过 ({len(required_fields)} 个)")

    # queue_name 必填
    try:
        BoosterParamsModel()
        raise AssertionError("queue_name 应为必填")
    except ValidationError:
        pass
    print("[OK] queue_name 为必填字段")

    # extra=forbid：臆造字段应报错
    try:
        BoosterParamsModel(queue_name="x", timeout=30)
        raise AssertionError("臆造字段 timeout 应被拒绝")
    except ValidationError:
        pass
    print("[OK] Pydantic extra=forbid 生效，臆造字段 timeout 被拒绝")


def check_fct_import():
    from funboost.core.current_task import _FctProxy

    assert fct is not None
    # 无消费上下文时 hasattr(fct, 'task_id') 会因 property getter 抛错而返回 False，应检查类定义
    for attr in ("task_id", "queue_name", "full_msg", "logger", "function_result_status"):
        assert attr in _FctProxy.__dict__ or hasattr(_FctProxy, attr), f"fct 缺少属性 {attr}"
    print("[OK] fct 对象导入及属性验证通过")


def check_broker_enum():
    expected = [
        "REDIS",
        "REDIS_ACK_ABLE",
        "SQLITE_QUEUE",
        "RABBITMQ",
        "RABBITMQ_AMQPSTORM",
        "MEMORY_QUEUE",
        "KAFKA",
    ]
    for name in expected:
        assert hasattr(BrokerEnum, name), f"BrokerEnum 缺少 {name}"
    assert BrokerEnum.RABBITMQ == BrokerEnum.RABBITMQ_AMQPSTORM
    print(f"[OK] BrokerEnum 枚举值验证通过 ({len(expected)} 个)")


def check_concurrent_mode_enum():
    modes = ["THREADING", "GEVENT", "EVENTLET", "ASYNC", "SINGLE_THREAD"]
    for name in modes:
        assert hasattr(ConcurrentModeEnum, name), f"ConcurrentModeEnum 缺少 {name}"
    assert ConcurrentModeEnum.THREADING == "threading"
    print(f"[OK] ConcurrentModeEnum 验证通过 ({len(modes)} 种模式)")


def check_push_publish_and_ctrl_c():
    @boost(BoosterParams(queue_name="verify_concepts_r1_task", broker_kind=BrokerEnum.SQLITE_QUEUE))
    def sample_task(x, y=1):
        return x + y

    assert hasattr(sample_task, "push")
    assert hasattr(sample_task, "publish")
    assert hasattr(sample_task, "consume")
    assert callable(enable_ctrl_c_quit_on_windows)
    print("[OK] push/publish/consume 方法存在，enable_ctrl_c_quit_on_windows 可导入")

    # 直接调用 vs push
    direct = sample_task(1, 2)
    assert direct == 3
    print("[OK] func(x,y) 直接调用仍可用（反框架设计）")

    sample_task.push(10, 20)
    print("[OK] func.push() 发布消息成功")

    sample_task.publish({"x": 5, "y": 6}, task_options=TaskOptions(task_id="verify-concepts-r1"))
    print("[OK] func.publish() + TaskOptions 发布成功")


def check_task_options_fields():
    opts = TaskOptions(task_id="t1", countdown=0, eta=None)
    assert opts.task_id == "t1"
    assert not hasattr(TaskOptions, "model_fields") or "priority" not in TaskOptions.model_fields
    print("[OK] TaskOptions 含 task_id/countdown；无 priority 字段（优先级走 other_extra_params）")


def check_config_module_loaded():
    import funboost.funboost_config_deafult as default_cfg

    assert hasattr(default_cfg, "BrokerConnConfig")
    assert hasattr(default_cfg, "FunboostCommonConfig")
    print("[OK] funboost_config_deafult 含 BrokerConnConfig / FunboostCommonConfig")


if __name__ == "__main__":
    errors = []
    checks = [
        check_booster_params_fields,
        check_fct_import,
        check_broker_enum,
        check_concurrent_mode_enum,
        check_push_publish_and_ctrl_c,
        check_task_options_fields,
        check_config_module_loaded,
    ]
    for fn in checks:
        try:
            fn()
        except Exception as e:
            errors.append(f"{fn.__name__}: {e}")

    if errors:
        print("\n[FAIL] 验证失败:")
        for err in errors:
            print(f"  - {err}")
        os._exit(1)

    print("\n[DONE] verify_concepts_r1 全部静态/API 验证通过")
    os._exit(66)
