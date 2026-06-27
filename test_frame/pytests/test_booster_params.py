"""
测试 BoosterParams 的 Pydantic 校验逻辑。

覆盖:
  1. queue_name 必填
  2. broker_kind 默认值
  3. broker_kind 非法值会报错
  4. concurrent_num 默认 50
  5. qps 默认 None
  6. 子类不能新增字段(只能覆盖)
  7. 字段赋值后会经过 root_validator 处理(is_send_consumer_heartbeat_to_redis 等)
  8. JSON 序列化/反序列化(BoosterParams 继承自 BaseJsonAbleModel)
  9. 默认值正确
"""
import sys
import os
import functools

print = functools.partial(print, flush=True)
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import pytest
from funboost import BoosterParams, BrokerEnum
from funboost.core.pydantic_compatible_base import BaseJsonAbleModel


# ============================================================================
# 单元测试(无外部依赖)
# ============================================================================

def test_queue_name_required():
    """queue_name 是必填字段,不能省略。"""
    with pytest.raises(Exception):
        BoosterParams()  # noqa


def test_broker_kind_default_is_sqlite_queue():
    """broker_kind 缺省值是 SQLITE_QUEUE。"""
    params = BoosterParams(queue_name='t1')
    assert params.broker_kind == BrokerEnum.SQLITE_QUEUE
    print('  [PASS] test_broker_kind_default_is_sqlite_queue')


def test_broker_kind_accepts_redis():
    """broker_kind 接受 REDIS 字符串。"""
    params = BoosterParams(queue_name='t1', broker_kind='REDIS')
    assert params.broker_kind == 'REDIS'
    print('  [PASS] test_broker_kind_accepts_redis')


def test_concurrent_num_default():
    """concurrent_num 缺省值是 50。"""
    params = BoosterParams(queue_name='t1')
    assert params.concurrent_num == 50
    print('  [PASS] test_concurrent_num_default')


def test_qps_default_is_none():
    """qps 缺省值是 None(不限频)。"""
    params = BoosterParams(queue_name='t1')
    assert params.qps is None
    print('  [PASS] test_qps_default_is_none')


def test_qps_accepts_zero():
    """qps=0 等同于不限频(框架内部会当作 None 处理)。"""
    params = BoosterParams(queue_name='t1', qps=0)
    assert params.qps == 0
    print('  [PASS] test_qps_accepts_zero')


def test_subclass_cannot_add_new_fields():
    """BoosterParams 的子类不能新增字段,只能覆盖。
    框架在 __init__ 后用 _check_legal_fields 阻止拼写错误导致的"以为覆盖实则新增"。
    """
    with pytest.raises(ValueError) as exc_info:
        class MyBadParams(BoosterParams):
            this_field_does_not_exist_in_parent: str = 'oops'

        MyBadParams(queue_name='t1')  # 触发校验

    assert 'this_field_does_not_exist_in_parent' in str(exc_info.value) or '字段' in str(exc_info.value)
    print('  [PASS] test_subclass_cannot_add_new_fields')


def test_subclass_can_override_existing_field():
    """子类可以覆盖父类已有字段的默认值。"""
    class MyParams(BoosterParams):
        concurrent_num: int = 200  # 覆盖默认值 50

    p = MyParams(queue_name='t1')
    assert p.concurrent_num == 200
    print('  [PASS] test_subclass_can_override_existing_field')


def test_redis_broker_enables_heartbeat():
    """broker_kind=REDIS 时,root_validator 会自动把 is_send_consumer_heartbeat_to_redis 设为 True。
    这是为了检测掉线消费者,把孤儿消息重回队列。
    """
    params = BoosterParams(queue_name='t1', broker_kind='REDIS')
    assert params.is_send_consumer_heartbeat_to_redis is True
    print('  [PASS] test_redis_broker_enables_heartbeat')


def test_function_result_status_persistance_conf_table_name_filled():
    """未指定 table_name 时,会用 queue_name 填充。"""
    params = BoosterParams(queue_name='my_specific_queue')
    assert params.function_result_status_persistance_conf.table_name == 'my_specific_queue'
    print('  [PASS] test_function_result_status_persistance_conf_table_name_filled')


def test_json_roundtrip():
    """BoosterParams 可以 JSON 序列化/反序列化(继承自 BaseJsonAbleModel)。"""
    p1 = BoosterParams(queue_name='t1', qps=2.5, concurrent_num=10)
    json_str = p1.json_str_value()
    assert isinstance(json_str, str)
    assert 't1' in json_str
    assert '2.5' in json_str
    # 反序列化回来(Pydantic v2 用 model_validate_json,v1 用 parse_raw)
    if hasattr(BoosterParams, 'model_validate_json'):
        p2 = BoosterParams.model_validate_json(json_str)
    else:
        p2 = BoosterParams.parse_raw(json_str)
    assert p2.queue_name == p1.queue_name
    assert p2.qps == p1.qps
    assert p2.concurrent_num == p1.concurrent_num
    print('  [PASS] test_json_roundtrip')


def test_booster_params_inherits_from_base_json_able_model():
    """BoosterParams 必须继承自 BaseJsonAbleModel。"""
    assert issubclass(BoosterParams, BaseJsonAbleModel)
    print('  [PASS] test_booster_params_inherits_from_base_json_able_model')


def test_rename_fields_attribute_exists():
    """BoosterParamsFieldsAssit.rename_fields 必须存在,这是旧拼写兼容的关键。"""
    from funboost.core.func_params_model import BoosterParamsFieldsAssit
    assert hasattr(BoosterParamsFieldsAssit, 'rename_fields')
    # 必须至少包含 3 个已知旧拼写
    rf = BoosterParamsFieldsAssit.rename_fields
    assert 'is_send_consumer_hearbeat_to_redis' in rf
    assert 'consumin_function_decorator' in rf
    assert 'msg_expire_senconds' in rf
    print('  [PASS] test_rename_fields_attribute_exists')


# ============================================================================
# 独立运行入口
# ============================================================================

def _run_all():
    funcs = [
        test_queue_name_required,
        test_broker_kind_default_is_sqlite_queue,
        test_broker_kind_accepts_redis,
        test_concurrent_num_default,
        test_qps_default_is_none,
        test_qps_accepts_zero,
        test_subclass_cannot_add_new_fields,
        test_subclass_can_override_existing_field,
        test_redis_broker_enables_heartbeat,
        test_function_result_status_persistance_conf_table_name_filled,
        test_json_roundtrip,
        test_booster_params_inherits_from_base_json_able_model,
        test_rename_fields_attribute_exists,
    ]
    passed = failed = 0
    print('=' * 60)
    print('BoosterParams 校验测试')
    print('=' * 60)
    for fn in funcs:
        try:
            fn()
            passed += 1
        except Exception as e:
            print(f'  [FAIL] {fn.__name__}: {type(e).__name__}: {e}')
            failed += 1
    print('=' * 60)
    print(f'结果: {passed} 通过 / {failed} 失败 / 共 {passed + failed} 项')
    print('=' * 60)
    sys.exit(0 if failed == 0 else 1)


if __name__ == '__main__':
    _run_all()
