"""
测试 Booster.__call__ 的"双分支"魔法:

这是 funboost 反框架设计的灵魂:
  - 第一次调用(装饰阶段):args==(func,) 且 callable → 装饰,返回 Booster
  - 后续调用(业务阶段):args 是业务数据 → 直接执行原函数,行为与无装饰时一致

覆盖:
  1. 装饰后,f 仍然是 callable
  2. f(1,2) 返回 1+2=3(直接调原函数)
  3. f(1,2) 不会触发 publish/consume
  4. f.push / f.consume / f.clear 已绑定
  5. 多次装饰不同函数,生成独立 Booster
  6. f.__name__ 保持原函数名(functools.wraps 效果)
  7. f 是 Booster 实例(isinstance)
  8. 直接调用不会跑进 publish 计数
"""
import sys
import os
import functools

print = functools.partial(print, flush=True)
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import uuid
from funboost import boost, BoosterParams, BrokerEnum, Booster


# ============================================================================
# 单元测试
# ============================================================================

def test_booster_is_callable():
    """装饰后,f 仍是 callable。"""
    @boost(BoosterParams(queue_name='t1', broker_kind=BrokerEnum.MEMORY_QUEUE))
    def add(a, b):
        return a + b

    assert callable(add), '装饰后应保持 callable'
    assert isinstance(add, Booster), '装饰后 f 应该是 Booster 实例'
    print('  [PASS] test_booster_is_callable')


def test_direct_call_invokes_original_function():
    """f(1, 2) 应该直接执行原函数,返回 3。"""
    @boost(BoosterParams(queue_name='t2', broker_kind=BrokerEnum.MEMORY_QUEUE))
    def add(a, b):
        return a + b

    result = add(1, 2)
    assert result == 3, f'直接调用应返回 3,实际 {result}'
    print('  [PASS] test_direct_call_invokes_original_function')


def test_direct_call_does_not_publish():
    """f(1, 2) 不应该向队列推任何东西。"""
    queue_name = f'test_no_pub_{uuid.uuid4().hex[:8]}'

    @boost(BoosterParams(queue_name=queue_name, broker_kind=BrokerEnum.MEMORY_QUEUE))
    def add(a, b):
        return a + b

    # 直接调用 3 次
    for i in range(3):
        add(i, i * 10)

    # 队列里应该没有任何消息
    count = add.get_message_count()
    assert count == 0, f'直接调用不应推消息,但队列里有 {count} 条'
    print('  [PASS] test_direct_call_does_not_publish')


def test_push_consume_clear_bound():
    """装饰后,f 上有 push / consume / clear 方法。"""
    @boost(BoosterParams(queue_name='t3', broker_kind=BrokerEnum.MEMORY_QUEUE))
    def f(x):
        return x

    assert hasattr(f, 'push')
    assert hasattr(f, 'consume')
    assert hasattr(f, 'clear')
    assert hasattr(f, 'publish')  # 别名
    assert hasattr(f, 'delay')    # push 的别名
    assert hasattr(f, 'pub')      # publish 的别名
    print('  [PASS] test_push_consume_clear_bound')


def test_push_actually_publishes():
    """f.push(1) 应该真的把消息推到队列里。"""
    queue_name = f'test_push_{uuid.uuid4().hex[:8]}'

    @boost(BoosterParams(queue_name=queue_name, broker_kind=BrokerEnum.MEMORY_QUEUE))
    def f(x):
        return x

    f.clear()
    assert f.get_message_count() == 0

    f.push(1)
    f.push(2)
    f.push(3)
    assert f.get_message_count() == 3, f'应推 3 条,实际 {f.get_message_count()}'
    print('  [PASS] test_push_actually_publishes')


def test_clear_empties_queue():
    """f.clear() 应该清空队列。"""
    queue_name = f'test_clear_{uuid.uuid4().hex[:8]}'

    @boost(BoosterParams(queue_name=queue_name, broker_kind=BrokerEnum.MEMORY_QUEUE))
    def f(x):
        return x

    for i in range(5):
        f.push(i)
    assert f.get_message_count() == 5

    f.clear()
    assert f.get_message_count() == 0, f'clear 后应为空,实际 {f.get_message_count()}'
    print('  [PASS] test_clear_empties_queue')


def test_wraps_preserves_function_metadata():
    """functools.wraps 应保留原函数的 __name__ / __doc__。"""
    @boost(BoosterParams(queue_name='t4', broker_kind=BrokerEnum.MEMORY_QUEUE))
    def my_specific_function_name(x):
        """这是我的特殊函数文档"""
        return x

    assert my_specific_function_name.__name__ == 'my_specific_function_name', \
        f'__name__ 应保持原函数名,实际 {my_specific_function_name.__name__}'
    assert '特殊函数文档' in (my_specific_function_name.__doc__ or ''), \
        '__doc__ 应保持原函数文档'
    print('  [PASS] test_wraps_preserves_function_metadata')


def test_separate_decorators_create_separate_boosters():
    """两个 @boost 装饰应该生成两个独立的 Booster 实例(不共享 publisher/consumer)。"""
    @boost(BoosterParams(queue_name='q1', broker_kind=BrokerEnum.MEMORY_QUEUE))
    def f1(x):
        return x

    @boost(BoosterParams(queue_name='q2', broker_kind=BrokerEnum.MEMORY_QUEUE))
    def f2(x):
        return x * 2

    assert f1 is not f2, '两个装饰应生成两个 Booster 实例'
    assert f1.boost_params.queue_name == 'q1'
    assert f2.boost_params.queue_name == 'q2'
    assert f1.push is not f2.push, '不同 Booster 应有独立的 push'
    print('  [PASS] test_separate_decorators_create_separate_boosters')


def test_publish_accepts_dict_form():
    """f.publish({'x': 1}) 应该接受字典形式(与 push 互为别名)。"""
    queue_name = f'test_pub_{uuid.uuid4().hex[:8]}'

    @boost(BoosterParams(queue_name=queue_name, broker_kind=BrokerEnum.MEMORY_QUEUE))
    def f(x):
        return x

    f.clear()
    f.publish({'x': 100})
    assert f.get_message_count() == 1
    print('  [PASS] test_publish_accepts_dict_form')


def test_booster_equality_by_queue_name():
    """两个 Booster 实例的 queue_name 不同就不相等。"""
    @boost(BoosterParams(queue_name='eq1', broker_kind=BrokerEnum.MEMORY_QUEUE))
    def a(x): return x

    @boost(BoosterParams(queue_name='eq2', broker_kind=BrokerEnum.MEMORY_QUEUE))
    def b(x): return x

    assert str(a) != str(b)
    print('  [PASS] test_booster_equality_by_queue_name')


# ============================================================================
# 独立运行入口
# ============================================================================

def _run_all():
    funcs = [
        test_booster_is_callable,
        test_direct_call_invokes_original_function,
        test_direct_call_does_not_publish,
        test_push_consume_clear_bound,
        test_push_actually_publishes,
        test_clear_empties_queue,
        test_wraps_preserves_function_metadata,
        test_separate_decorators_create_separate_boosters,
        test_publish_accepts_dict_form,
        test_booster_equality_by_queue_name,
    ]
    passed = failed = 0
    print('=' * 60)
    print('Booster.__call__ 双分支测试')
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
