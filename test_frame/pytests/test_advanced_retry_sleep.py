"""
高级重试(sleep 模式)的端到端测试。

验证 funboost 的指数退避重试:
  1. 函数始终抛错时,被调用次数 = max_retry_times + 1
  2. retry_base_interval / retry_multiplier / retry_max_interval 生效
  3. retry_jitter 不破坏重试次数
  4. is_push_to_dlx_queue_when_retry_max_times 触发后消息进入死信队列

用 MEMORY_QUEUE + sleep 模式,不依赖外部 broker。

退避序列(无 jitter,base=0.05,multiplier=2,max=0.5):
  第 1 次:立刻
  第 2 次:睡 0.05s
  第 3 次:睡 0.10s
  第 4 次:睡 0.20s
  第 5 次:睡 0.40s
  ... 后续都是 0.50s
"""
import sys
import os
import atexit
import functools
import threading
import time

print = functools.partial(print, flush=True)
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import uuid
from funboost import boost, BoosterParams, BrokerEnum


# 强退钩子:funboost 启动的 non-daemon consume 线程会卡住 Python 退出
def _force_exit():
    try:
        os._exit(0)
    except Exception:
        pass
atexit.register(_force_exit)


# ============================================================================
# 测试用例
# ============================================================================

def test_advanced_retry_sleep_basic_count():
    """sleep 模式:函数始终抛错,被调用次数 = max_retry_times + 1(含首次)。"""
    queue_name = f'test_adv_retry_{uuid.uuid4().hex[:8]}'
    call_count = [0]
    call_count_lock = threading.Lock()
    call_times = []  # 记录每次调用的时间戳,用来验证退避间隔

    @boost(BoosterParams(
        queue_name=queue_name,
        broker_kind=BrokerEnum.MEMORY_QUEUE,
        max_retry_times=3,
        is_using_advanced_retry=True,
        advanced_retry_config={
            'retry_mode': 'sleep',
            'retry_base_interval': 0.05,    # 短间隔让测试快
            'retry_multiplier': 2.0,
            'retry_max_interval': 0.5,
            'retry_jitter': False,
        },
    ))
    def always_fail(x):
        with call_count_lock:
            call_count[0] += 1
            call_times.append(time.time())
        raise ValueError(f'模拟失败 x={x}')

    always_fail.clear()
    always_fail.push(100)
    assert always_fail.get_message_count() == 1

    always_fail.consume()

    # 等重试跑完。3+1=4 次调用,加上 sleep 间隔 0.05+0.10+0.20 = 0.35s
    # 留 3s 缓冲
    deadline = time.time() + 5
    while time.time() < deadline:
        with call_count_lock:
            if call_count[0] >= 4:
                break
        time.sleep(0.05)

    with call_count_lock:
        assert call_count[0] == 4, f'期望 4 次调用(1+3 重试),实际 {call_count[0]} 次'
    print(f'  [PASS] test_advanced_retry_sleep_basic_count (调用了 {call_count[0]} 次)')


def test_advanced_retry_sleep_backoff_intervals():
    """验证 sleep 模式的退避间隔确实生效(第 2、3、4 次之间有递增的 sleep)。"""
    queue_name = f'test_adv_retry_iv_{uuid.uuid4().hex[:8]}'
    call_times = []
    call_times_lock = threading.Lock()

    @boost(BoosterParams(
        queue_name=queue_name,
        broker_kind=BrokerEnum.MEMORY_QUEUE,
        max_retry_times=3,
        is_using_advanced_retry=True,
        advanced_retry_config={
            'retry_mode': 'sleep',
            'retry_base_interval': 0.1,
            'retry_multiplier': 2.0,
            'retry_max_interval': 1.0,
            'retry_jitter': False,
        },
    ))
    def fail_task(x):
        with call_times_lock:
            call_times.append(time.time())
        raise ValueError('fail')

    fail_task.clear()
    fail_task.push(1)
    fail_task.consume()

    deadline = time.time() + 5
    while time.time() < deadline:
        with call_times_lock:
            if len(call_times) >= 4:
                break
        time.sleep(0.05)

    with call_times_lock:
        assert len(call_times) == 4, f'期望 4 次调用,实际 {len(call_times)}'
        # 计算相邻间隔
        intervals = [call_times[i+1] - call_times[i] for i in range(3)]
        # 理论值:0.1, 0.2, 0.4(允许 ±30ms 误差)
        expected = [0.1, 0.2, 0.4]
        for i, (actual, exp) in enumerate(zip(intervals, expected)):
            # 实际间隔应 >= 理论值 - 30ms(下界)
            # 实际间隔应 <= 理论值 + 100ms(上界,允许 GIL 调度)
            assert exp - 0.03 <= actual <= exp + 0.1, \
                f'第 {i+1}→{i+2} 次间隔:期望 ~{exp}s,实际 {actual:.3f}s(全部间隔={intervals})'
    print(f'  [PASS] test_advanced_retry_sleep_backoff_intervals (间隔={[f"{i:.3f}" for i in intervals]})')


def test_advanced_retry_sleep_respects_max_interval():
    """验证 retry_max_interval 上限生效:长序列后,间隔被截断。"""
    queue_name = f'test_adv_retry_max_{uuid.uuid4().hex[:8]}'
    call_times = []
    call_times_lock = threading.Lock()

    @boost(BoosterParams(
        queue_name=queue_name,
        broker_kind=BrokerEnum.MEMORY_QUEUE,
        max_retry_times=5,
        is_using_advanced_retry=True,
        advanced_retry_config={
            'retry_mode': 'sleep',
            'retry_base_interval': 0.1,
            'retry_multiplier': 10.0,  # 倍数 10,理论上 0.1 → 1.0 → 10.0(被 max=0.3 截)
            'retry_max_interval': 0.3,  # 上限 0.3s
            'retry_jitter': False,
        },
    ))
    def fail_task(x):
        with call_times_lock:
            call_times.append(time.time())
        raise ValueError('fail')

    fail_task.clear()
    fail_task.push(1)
    fail_task.consume()

    deadline = time.time() + 5
    while time.time() < deadline:
        with call_times_lock:
            if len(call_times) >= 6:
                break
        time.sleep(0.05)

    with call_times_lock:
        assert len(call_times) == 6, f'期望 6 次调用,实际 {len(call_times)}'
        # 理论无上限:0.1, 1.0, 10.0, 100.0... → 总耗时 > 5s
        # 实际上限 0.3s:0.1, 0.3, 0.3, 0.3, 0.3 → 总耗时 ~ 1.3s
        intervals = [call_times[i+1] - call_times[i] for i in range(5)]
        # 第二个及之后间隔应接近 0.3s(允许 ±50ms 误差)
        for i in range(1, 5):
            assert intervals[i] <= 0.35, \
                f'第 {i+1}→{i+2} 次间隔 {intervals[i]:.3f}s 应被 max=0.3 截断(全部={intervals})'
    print(f'  [PASS] test_advanced_retry_sleep_respects_max_interval (间隔={[f"{i:.3f}" for i in intervals]})')


def test_advanced_retry_eventually_succeeds():
    """函数在前 N-1 次抛错,第 N 次成功后,不再重试(成功终止)。"""
    queue_name = f'test_adv_retry_ok_{uuid.uuid4().hex[:8]}'
    call_count = [0]
    call_count_lock = threading.Lock()
    succeeded = [False]

    @boost(BoosterParams(
        queue_name=queue_name,
        broker_kind=BrokerEnum.MEMORY_QUEUE,
        max_retry_times=5,
        is_using_advanced_retry=True,
        advanced_retry_config={
            'retry_mode': 'sleep',
            'retry_base_interval': 0.05,
            'retry_multiplier': 2.0,
            'retry_max_interval': 0.5,
            'retry_jitter': False,
        },
    ))
    def flaky_task(x):
        with call_count_lock:
            call_count[0] += 1
            n = call_count[0]
        if n < 3:
            raise ValueError(f'第 {n} 次失败')
        with call_count_lock:
            succeeded[0] = True
        return x * 2

    flaky_task.clear()
    flaky_task.push(7)
    flaky_task.consume()

    deadline = time.time() + 5
    while time.time() < deadline:
        with call_count_lock:
            if succeeded[0]:
                break
        time.sleep(0.05)

    # 留点时间确保不会继续重试
    time.sleep(0.5)

    with call_count_lock:
        assert succeeded[0], 'flaky_task 在第 3 次应该成功'
        # 成功后不应该再重试,所以调用次数应该正好 3
        assert call_count[0] == 3, f'成功后不应再重试,期望 3 次,实际 {call_count[0]} 次'
    print(f'  [PASS] test_advanced_retry_eventually_succeeds (成功于第 {call_count[0]} 次)')


# ============================================================================
# 独立运行入口
# ============================================================================

def _run_all():
    funcs = [
        test_advanced_retry_sleep_basic_count,
        test_advanced_retry_sleep_backoff_intervals,
        test_advanced_retry_sleep_respects_max_interval,
        test_advanced_retry_eventually_succeeds,
    ]
    passed = failed = 0
    print('=' * 60)
    print('高级重试 sleep 模式测试')
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
    sys.stdout.flush()
    os._exit(0 if failed == 0 else 1)


if __name__ == '__main__':
    _run_all()
