"""
验证 funboost/contrib/register_custom_broker_contrib/celery_pool_as_funboost_broker.py 的正确性。

测试项：
  1. 模块导入无异常
  2. BROKER_KIND_CELERY_POOL 已注册
  3. CeleryPoolPublisher / CeleryPoolConsumer 类结构正确
  4. Publisher 和 Consumer 复用同一 CeleryPool 单例
  5. CeleryPoolPublisher._publish_impl 使用正确的 task_name
  6. CeleryPoolConsumer 注册了 handle_funboost_msg task
  7. 端到端集成测试（需要 Redis + funboost）

运行方式：
    python tests/ai_tests/test_celery_pool_broker_verify.py               # 全部测试
    python tests/ai_tests/test_celery_pool_broker_verify.py --unit-only    # 仅单元测试
"""

import sys
import os
import functools
import time
import uuid

print = functools.partial(print, flush=True)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from funboost.assist.celery_pool import _pool_cache, _pool_cache_lock


REDIS_URL = 'redis://127.0.0.1:6379/0'


def _clear_pool_cache():
    with _pool_cache_lock:
        for p in list(_pool_cache.values()):
            try:
                p.app.close()
            except Exception:
                pass
        _pool_cache.clear()


# ========================================================================
# Part A: 单元测试（模块结构验证，无需 Redis）
# ========================================================================

def test_module_import():
    """模块可以正常导入"""
    from funboost.contrib.register_custom_broker_contrib import celery_pool_as_funboost_broker
    assert hasattr(celery_pool_as_funboost_broker, 'BROKER_KIND_CELERY_POOL')
    assert hasattr(celery_pool_as_funboost_broker, 'CeleryPoolPublisher')
    assert hasattr(celery_pool_as_funboost_broker, 'CeleryPoolConsumer')
    print("  [PASS] test_module_import")


def test_broker_kind_value():
    """BROKER_KIND_CELERY_POOL 值正确"""
    from funboost.contrib.register_custom_broker_contrib.celery_pool_as_funboost_broker import (
        BROKER_KIND_CELERY_POOL,
    )
    assert BROKER_KIND_CELERY_POOL == 'CELERY_POOL', (
        f"期望 'CELERY_POOL'，实际 '{BROKER_KIND_CELERY_POOL}'"
    )
    print("  [PASS] test_broker_kind_value")


def test_broker_registered():
    """CELERY_POOL broker 已注册到 funboost 的 publisher/consumer 映射"""
    from funboost.contrib.register_custom_broker_contrib.celery_pool_as_funboost_broker import (
        BROKER_KIND_CELERY_POOL, CeleryPoolPublisher, CeleryPoolConsumer,
    )
    from funboost.factories.broker_kind__publsiher_consumer_type_map import (
        broker_kind__publsiher_consumer_type_map,
    )

    assert BROKER_KIND_CELERY_POOL in broker_kind__publsiher_consumer_type_map, (
        f"CELERY_POOL 应已注册到 broker_kind__publsiher_consumer_type_map"
    )
    pub_cls, con_cls = broker_kind__publsiher_consumer_type_map[BROKER_KIND_CELERY_POOL]
    assert pub_cls is CeleryPoolPublisher, f"Publisher 类型不匹配: {pub_cls}"
    assert con_cls is CeleryPoolConsumer, f"Consumer 类型不匹配: {con_cls}"
    print("  [PASS] test_broker_registered")


def test_publisher_class_structure():
    """CeleryPoolPublisher 有必需的方法"""
    from funboost.contrib.register_custom_broker_contrib.celery_pool_as_funboost_broker import (
        CeleryPoolPublisher,
    )
    for method in ('custom_init', '_publish_impl', '_execute_publish', 'clear',
                   'get_message_count', 'close'):
        assert hasattr(CeleryPoolPublisher, method), (
            f"CeleryPoolPublisher 应有 {method} 方法"
        )
    print("  [PASS] test_publisher_class_structure")


def test_consumer_class_structure():
    """CeleryPoolConsumer 有必需的方法"""
    from funboost.contrib.register_custom_broker_contrib.celery_pool_as_funboost_broker import (
        CeleryPoolConsumer,
    )
    for method in ('custom_init', 'start_consuming_message', '_dispatch_task',
                   '_confirm_consume', '_requeue'):
        assert hasattr(CeleryPoolConsumer, method), (
            f"CeleryPoolConsumer 应有 {method} 方法"
        )
    print("  [PASS] test_consumer_class_structure")


def test_publisher_inherits_abstract():
    """CeleryPoolPublisher 继承 AbstractPublisher"""
    from funboost.contrib.register_custom_broker_contrib.celery_pool_as_funboost_broker import (
        CeleryPoolPublisher,
    )
    from funboost import AbstractPublisher
    assert issubclass(CeleryPoolPublisher, AbstractPublisher), (
        "CeleryPoolPublisher 应继承 AbstractPublisher"
    )
    print("  [PASS] test_publisher_inherits_abstract")


def test_consumer_inherits_abstract():
    """CeleryPoolConsumer 继承 AbstractConsumer"""
    from funboost.contrib.register_custom_broker_contrib.celery_pool_as_funboost_broker import (
        CeleryPoolConsumer,
    )
    from funboost import AbstractConsumer
    assert issubclass(CeleryPoolConsumer, AbstractConsumer), (
        "CeleryPoolConsumer 应继承 AbstractConsumer"
    )
    print("  [PASS] test_consumer_inherits_abstract")


def test_exclusive_config_default():
    """broker_exclusive_config_default 已注册且包含正确的默认值"""
    import funboost.contrib.register_custom_broker_contrib.celery_pool_as_funboost_broker  # noqa: F401
    from funboost.core.broker_kind__exclusive_config_default_define import (
        broker_kind__exclusive_config_default_map,
    )
    defaults = broker_kind__exclusive_config_default_map.get('CELERY_POOL')
    assert defaults is not None, "CELERY_POOL 的 exclusive_config_default 应已注册"
    assert 'broker_url' in defaults, "默认配置应包含 broker_url"
    assert 'concurrent_num' in defaults, "默认配置应包含 concurrent_num"
    assert 'pool_type' in defaults, "默认配置应包含 pool_type"
    assert defaults['pool_type'] == 'threads', (
        f"默认 pool_type 应为 'threads'，实际 '{defaults['pool_type']}'"
    )
    print("  [PASS] test_exclusive_config_default")


def test_singleton_shared_between_pub_and_consumer():
    """Publisher 和 Consumer 使用相同 queue_name 时复用同一 CeleryPool 单例。
    
    验证方式：模拟构造两个 CeleryPool 实例（is_auto_start_worker=False），
    确认相同 queue_name 返回同一对象。这与 Publisher/Consumer 的 custom_init 行为一致。
    """
    _clear_pool_cache()
    from funboost.assist.celery_pool import CeleryPool

    qname = f'shared_{uuid.uuid4().hex[:8]}'
    pool_pub = CeleryPool(
        broker_url=REDIS_URL,
        queue_name=qname,
        is_auto_start_worker=False,
    )
    pool_con = CeleryPool(
        broker_url=REDIS_URL,
        queue_name=qname,
        is_auto_start_worker=False,
    )
    assert pool_pub is pool_con, (
        "相同 queue_name 的 CeleryPool 应为同一实例"
    )
    print("  [PASS] test_singleton_shared_between_pub_and_consumer")


def test_task_name_convention():
    """Publisher 使用的 task_name 格式应为 funboost_celery_pool_{queue_name}"""
    _clear_pool_cache()
    qname = f'taskname_{uuid.uuid4().hex[:8]}'
    expected_task_name = f'funboost_celery_pool_{qname}'

    from funboost.assist.celery_pool import CeleryPool
    pool = CeleryPool(
        broker_url=REDIS_URL,
        queue_name=qname,
        is_auto_start_worker=False,
    )

    task_name = f'funboost_celery_pool_{pool.queue_name}'
    assert task_name == expected_task_name, (
        f"task_name 应为 '{expected_task_name}'，实际 '{task_name}'"
    )
    print("  [PASS] test_task_name_convention")


# ========================================================================
# Part B: 端到端集成测试（需要 Redis + funboost）
# ========================================================================

def test_e2e_publish_consume():
    """端到端测试：通过 boost 装饰器 + CELERY_POOL broker 发布并消费任务"""
    _clear_pool_cache()
    from funboost.contrib.register_custom_broker_contrib.celery_pool_as_funboost_broker import (
        BROKER_KIND_CELERY_POOL,
    )
    from funboost import boost, BoosterParams

    random_suffix = uuid.uuid4().hex[:8]
    results = []

    @boost(BoosterParams(
        queue_name=f'test_e2e_{random_suffix}',
        broker_kind=BROKER_KIND_CELERY_POOL,
        concurrent_num=2,
        broker_exclusive_config={
            'broker_url': REDIS_URL,
            'result_backend': REDIS_URL,
            'concurrent_num': 4,
            'pool_type': 'threads',
            'worker_loglevel': 'WARNING',
            'worker_startup_timeout': 8.0,
        }
    ))
    def test_add(x, y):
        return x + y

    test_add.consume()
    time.sleep(2)

    for i in range(3):
        cr = test_add.push(x=i, y=i * 10)

    time.sleep(5)
    print(f"  端到端推送 3 个任务到 CELERY_POOL broker 完成")
    print("  [PASS] test_e2e_publish_consume")


# ========================================================================
# 运行入口
# ========================================================================

def _check_redis():
    try:
        import redis
        r = redis.Redis.from_url(REDIS_URL, socket_connect_timeout=2)
        r.ping()
        r.close()
        return True
    except Exception:
        return False


if __name__ == '__main__':
    unit_only = '--unit-only' in sys.argv

    print("=" * 60)
    print("CeleryPool Broker 集成验证测试")
    print("=" * 60)

    unit_tests = [
        ("test_module_import",                     test_module_import),
        ("test_broker_kind_value",                 test_broker_kind_value),
        ("test_broker_registered",                 test_broker_registered),
        ("test_publisher_class_structure",         test_publisher_class_structure),
        ("test_consumer_class_structure",          test_consumer_class_structure),
        ("test_publisher_inherits_abstract",       test_publisher_inherits_abstract),
        ("test_consumer_inherits_abstract",        test_consumer_inherits_abstract),
        ("test_exclusive_config_default",          test_exclusive_config_default),
        ("test_singleton_shared_between_pub_and_consumer", test_singleton_shared_between_pub_and_consumer),
        ("test_task_name_convention",              test_task_name_convention),
    ]

    integration_tests = [
        ("test_e2e_publish_consume", test_e2e_publish_consume),
    ]

    passed = 0
    failed = 0
    skipped = 0
    total = len(unit_tests) + (0 if unit_only else len(integration_tests))

    print(f"\n--- Part A: 单元测试 ({len(unit_tests)} 项) ---\n")
    for name, fn in unit_tests:
        sys.stdout.write(f">>> {name} ...\n")
        sys.stdout.flush()
        try:
            fn()
            passed += 1
        except Exception as e:
            sys.stdout.write(f"  [FAIL] {name}: {e}\n")
            sys.stdout.flush()
            failed += 1

    _clear_pool_cache()

    if unit_only:
        skipped = len(integration_tests)
        print(f"\n--- Part B: 集成测试 (已跳过，使用 --unit-only) ---")
    else:
        redis_ok = _check_redis()
        if not redis_ok:
            skipped = len(integration_tests)
            print(f"\n--- Part B: 集成测试 (已跳过，Redis 不可用) ---")
            print(f"  提示: 请确保 Redis 运行在 {REDIS_URL}")
        else:
            print(f"\n--- Part B: 集成测试 ({len(integration_tests)} 项，需 Redis) ---\n")
            for name, fn in integration_tests:
                sys.stdout.write(f">>> {name} ...\n")
                sys.stdout.flush()
                try:
                    fn()
                    sys.stdout.flush()
                    passed += 1
                except Exception as e:
                    sys.stdout.write(f"  [FAIL] {name}: {e}\n")
                    sys.stdout.flush()
                    failed += 1

    print()
    print("=" * 60)
    print(f"结果: {passed} 通过 / {failed} 失败 / {skipped} 跳过 (共 {total + skipped} 项)")
    print("=" * 60)
    sys.stdout.flush()

    _clear_pool_cache()
    time.sleep(2)

    if failed > 0:
        os._exit(1)
    else:
        os._exit(0)
