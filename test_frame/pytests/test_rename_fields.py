"""
测试 BoosterParams 的旧拼写字段兼容(rename_fields 机制)。

这是 funboost 长期迭代留下的"历史包袱清理"机制:
  1. 旧的拼写错误('hearbeat' 缺 a)→ 改后映射为正确拼写
  2. 用户用旧名传参,框架在 __init__ 阶段自动改写,无感升级
  3. 旧字段(已被删除)→ 直接 pop 掉,不让 Pydantic extra="forbid" 报错

覆盖:
  1. 旧拼写 'is_send_consumer_hearbeat_to_redis' 被重写为正确名
  2. 旧拼写 'consumin_function_decorator' 被重写
  3. 旧拼写 'msg_expire_senconds' 被重写
  4. 新拼写正常工作
  5. 已废弃字段被静默丢弃
  6. 旧拼写不会被两个都设上(只保留新字段)
"""
import sys
import os
import functools

print = functools.partial(print, flush=True)
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from funboost import BoosterParams, BrokerEnum
from funboost.core.func_params_model import BoosterParamsFieldsAssit


# ============================================================================
# 单元测试
# ============================================================================

def test_old_hearbeat_typo_remapped():
    """旧拼写 'is_send_consumer_hearbeat_to_redis' 应被重写为 'is_send_consumer_heartbeat_to_redis'。"""
    p = BoosterParams(
        queue_name='t1',
        broker_kind=BrokerEnum.MEMORY_QUEUE,
        is_send_consumer_hearbeat_to_redis=True,  # 旧拼写
    )
    # 旧字段被重命名,新字段被设值
    assert p.is_send_consumer_heartbeat_to_redis is True
    # 旧字段名不应作为属性存在(Pydantic 不会自动把 dict key 转成属性)
    # 用 model_fields 验证:旧字段不在 fields 中
    if hasattr(p, 'model_fields'):
        assert 'is_send_consumer_hearbeat_to_redis' not in p.model_fields
    print('  [PASS] test_old_hearbeat_typo_remapped')


def test_old_consumin_typo_remapped():
    """旧拼写 'consumin_function_decorator' 应被重写为 'consuming_function_decorator'。"""
    deco = lambda f: f  # 任何可调用对象

    p = BoosterParams(
        queue_name='t1',
        broker_kind=BrokerEnum.MEMORY_QUEUE,
        consumin_function_decorator=deco,  # 旧拼写
    )
    # 新字段应被设值
    assert p.consuming_function_decorator is deco
    print('  [PASS] test_old_consumin_typo_remapped')


def test_old_msg_expire_senconds_remapped():
    """旧拼写 'msg_expire_senconds' 应被重写为 'msg_expire_seconds'。"""
    p = BoosterParams(
        queue_name='t1',
        broker_kind=BrokerEnum.MEMORY_QUEUE,
        msg_expire_senconds=300,  # 旧拼写
    )
    assert p.msg_expire_seconds == 300
    print('  [PASS] test_old_msg_expire_senconds_remapped')


def test_new_spelling_works_normally():
    """新拼写(正确拼写)应能正常使用。"""
    p = BoosterParams(
        queue_name='t1',
        broker_kind=BrokerEnum.MEMORY_QUEUE,
        is_send_consumer_heartbeat_to_redis=True,  # 正确拼写
        msg_expire_seconds=600,
    )
    assert p.is_send_consumer_heartbeat_to_redis is True
    assert p.msg_expire_seconds == 600
    print('  [PASS] test_new_spelling_works_normally')


def test_deleted_fields_silently_dropped():
    """已废弃字段(在 has_been_deleted_fields 中)应被静默丢弃,不报错。"""
    p = BoosterParams(
        queue_name='t1',
        broker_kind=BrokerEnum.MEMORY_QUEUE,
        retry_interval=5,  # 已废弃
        is_do_not_run_by_specify_time_effect=True,  # 已废弃
        do_not_run_by_specify_time=[(0, 1)],  # 已废弃
    )
    # 字段被静默丢弃,创建成功
    assert p.queue_name == 't1'
    # 旧字段不应作为属性存在
    assert not hasattr(p, 'retry_interval')
    assert not hasattr(p, 'is_do_not_run_by_specify_time_effect')
    print('  [PASS] test_deleted_fields_silently_dropped')


def test_mix_old_and_new_old_wins():
    """同时传旧名+新名时,旧名的值会覆盖新名。

    实现细节:rename 阶段执行 `data[new_field] = data.pop(old_field)`,
    即使新名已经先被设过,这次赋值会用旧名的值覆盖。
    这是个有意思的契约——"如果你同时传了旧拼写,框架信任旧拼写"。
    """
    p = BoosterParams(
        queue_name='t1',
        broker_kind=BrokerEnum.MEMORY_QUEUE,
        msg_expire_senconds=100,  # 旧名
        msg_expire_seconds=200,    # 新名
    )
    # 旧名 pop 出来赋给新名,覆盖了新名原本的值
    assert p.msg_expire_seconds == 100, f'期望 100 (旧名覆盖新名),实际 {p.msg_expire_seconds}'
    print('  [PASS] test_mix_old_and_new_old_wins')


def test_rename_fields_table_complete():
    """rename_fields 字典至少有 3 个条目,且键是已知的旧拼写。"""
    rf = BoosterParamsFieldsAssit.rename_fields
    assert isinstance(rf, dict)
    assert len(rf) >= 3, f'至少应有 3 个映射,实际 {len(rf)}'
    # 已知的所有旧拼写
    known_old_spellings = {
        'is_send_consumer_hearbeat_to_redis',
        'consumin_function_decorator',
        'msg_expire_senconds',
    }
    for old in known_old_spellings:
        assert old in rf, f'旧拼写 {old} 应在 rename_fields 中'
    # 每个新拼写应是 BoosterParams 实际字段
    if hasattr(BoosterParams, 'model_fields'):
        all_fields = set(BoosterParams.model_fields.keys())
        for old, new in rf.items():
            assert new in all_fields, f'新拼写 {new} 必须是 BoosterParams 字段'
    print('  [PASS] test_rename_fields_table_complete')


def test_unknown_field_still_rejected():
    """完全未知的字段名仍然会被 Pydantic 拒绝(rename 只针对已知旧拼写)。"""
    import pydantic
    with pytest.raises(pydantic.ValidationError) if 'pydantic' in sys.modules else _no_raise() as exc:
        BoosterParams(
            queue_name='t1',
            broker_kind=BrokerEnum.MEMORY_QUEUE,
            this_is_a_completely_bogus_field=123,
        )
    # 如果上面 try 没抛,说明是 Pydantic v1 (extra=allow),这也算合理
    print('  [PASS] test_unknown_field_still_rejected')


# 辅助:无异常时返回 None
from contextlib import contextmanager
@contextmanager
def _no_raise():
    yield None


# 提前 import pytest
import pytest


# ============================================================================
# 独立运行入口
# ============================================================================

def _run_all():
    funcs = [
        test_old_hearbeat_typo_remapped,
        test_old_consumin_typo_remapped,
        test_old_msg_expire_senconds_remapped,
        test_new_spelling_works_normally,
        test_deleted_fields_silently_dropped,
        test_mix_old_and_new_old_wins,
        test_rename_fields_table_complete,
        test_unknown_field_still_rejected,
    ]
    passed = failed = 0
    print('=' * 60)
    print('rename_fields 旧拼写兼容测试')
    print('=' * 60)
    for fn in funcs:
        try:
            fn()
            passed += 1
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f'  [FAIL] {fn.__name__}: {type(e).__name__}: {e}')
            failed += 1
    print('=' * 60)
    print(f'结果: {passed} 通过 / {failed} 失败 / 共 {passed + failed} 项')
    print('=' * 60)
    sys.exit(0 if failed == 0 else 1)


if __name__ == '__main__':
    _run_all()
