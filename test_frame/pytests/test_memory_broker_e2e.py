"""
端到端测试:使用 MEMORY_QUEUE broker 跑通 push → consume → 函数执行全流程。

这是 funboost 最干净的端到端验证(无任何外部依赖):
  1. push N 条消息
  2. 启动 consume 线程
  3. 验证函数被调用 N 次,入参正确
  4. 验证队列最终为空

注意:funboost 的 consume() 会启动一个 non-daemon 线程(框架 hardcode)。
在独立运行模式下,脚本末尾用 os._exit() 强退;在 pytest 模式下,测试函数返回后
线程会持续运行,pytest 会卡住——所以 pytest 跑这个文件时建议:
  pytest test_frame/pytests/test_memory_broker_e2e.py --timeout=30
或者用 pytest-xdist 的 --maxfail=1 + worker 隔离。

为简单起见,本文件**推荐独立运行**:`python test_memory_broker_e2e.py`。
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


# 在模块加载时注册强制退出钩子,确保无论独立跑还是 pytest 都能干净退出
def _force_exit():
    """funboost 的 consume 启动 non-daemon 线程,atexit 钩子在退出时强退整个进程。"""
    try:
        os._exit(0)
    except Exception:
        pass
atexit.register(_force_exit)


# ============================================================================
# 测试用例
# ============================================================================

def test_push_count_increments_queue_length():
    """push N 次,get_message_count 应该返回 N。"""
    queue_name = f'test_count_{uuid.uuid4().hex[:8]}'

    @boost(BoosterParams(queue_name=queue_name, broker_kind=BrokerEnum.MEMORY_QUEUE))
    def f(x):
        return x

    f.clear()
    for i in range(7):
        f.push(i)
    assert f.get_message_count() == 7
    print('  [PASS] test_push_count_increments_queue_length')


def test_e2e_consume_invokes_function_with_correct_args():
    """端到端:push 5 条消息,consume 后函数应被调用 5 次,入参正确。"""
    queue_name = f'test_e2e_{uuid.uuid4().hex[:8]}'
    results = []
    results_lock = threading.Lock()

    @boost(BoosterParams(
        queue_name=queue_name,
        broker_kind=BrokerEnum.MEMORY_QUEUE,
        concurrent_num=3,
    ))
    def add(x, y):
        with results_lock:
            results.append((x, y, x + y))
        return x + y

    add.clear()
    for i in range(5):
        add.push(i, i * 10)

    assert add.get_message_count() == 5

    # 启动消费(非阻塞,新线程跑死循环)
    add.consume()

    # 等消息处理完
    deadline = time.time() + 10
    while time.time() < deadline:
        with results_lock:
            if len(results) >= 5:
                break
        time.sleep(0.1)

    with results_lock:
        assert len(results) == 5, f'期望 5 次调用,实际 {len(results)} 次'
        # 验证所有 (x, y, x+y) 都被记录
        expected = [(i, i * 10, i + i * 10) for i in range(5)]
        assert sorted(results) == sorted(expected), f'入参结果不匹配: {results}'
    print('  [PASS] test_e2e_consume_invokes_function_with_correct_args')


def test_e2e_clear_then_push_then_consume():
    """clear → push → consume 应正确处理(确保 clear 真的清空了)。"""
    queue_name = f'test_clr_push_{uuid.uuid4().hex[:8]}'
    results = []
    results_lock = threading.Lock()

    @boost(BoosterParams(queue_name=queue_name, broker_kind=BrokerEnum.MEMORY_QUEUE))
    def f(x):
        with results_lock:
            results.append(x)
        return x

    # 先推 3 条
    for i in range(3):
        f.push(i)
    assert f.get_message_count() == 3

    # clear
    f.clear()
    assert f.get_message_count() == 0

    # 再推 2 条
    f.push(100)
    f.push(200)
    assert f.get_message_count() == 2

    # consume
    f.consume()
    deadline = time.time() + 5
    while time.time() < deadline:
        with results_lock:
            if len(results) >= 2:
                break
        time.sleep(0.1)

    with results_lock:
        assert sorted(results) == [100, 200], f'期望 [100, 200],实际 {sorted(results)}'
    print('  [PASS] test_e2e_clear_then_push_then_consume')


def test_e2e_concurrent_consume_in_parallel():
    """并发模式验证:concurrent_num=4 时,4 个线程并行处理,总耗时 < 串行。"""
    queue_name = f'test_conc_{uuid.uuid4().hex[:8]}'
    results = []
    results_lock = threading.Lock()
    sleep_per_msg = 0.5
    n_msgs = 4

    @boost(BoosterParams(
        queue_name=queue_name,
        broker_kind=BrokerEnum.MEMORY_QUEUE,
        concurrent_num=n_msgs,  # 4 个并发
    ))
    def slow_task(x):
        time.sleep(sleep_per_msg)
        with results_lock:
            results.append(x)
        return x

    slow_task.clear()
    start = time.time()
    for i in range(n_msgs):
        slow_task.push(i)
    slow_task.consume()

    # 等所有任务完成
    deadline = start + 10
    while time.time() < deadline:
        with results_lock:
            if len(results) >= n_msgs:
                break
        time.sleep(0.1)

    elapsed = time.time() - start
    with results_lock:
        assert len(results) == n_msgs, f'期望 {n_msgs} 条,实际 {len(results)}'
    # 4 个并发 * 0.5s ≈ 0.5s;如果串行则 2s
    # 留 1.8s 余量(框架启动 + 队列处理),应该 < 2.0s
    assert elapsed < 2.0, f'并发执行应 < 2.0s,实际 {elapsed:.2f}s(串行预期 2.0s)'
    print(f'  [PASS] test_e2e_concurrent_consume_in_parallel ({elapsed:.2f}s)')


# ============================================================================
# 独立运行入口
# ============================================================================

def _run_all():
    funcs = [
        test_push_count_increments_queue_length,
        test_e2e_consume_invokes_function_with_correct_args,
        test_e2e_clear_then_push_then_consume,
        test_e2e_concurrent_consume_in_parallel,
    ]
    passed = failed = 0
    print('=' * 60)
    print('MEMORY_QUEUE 端到端测试')
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
    # funboost 启动的是 non-daemon 线程,会卡住 sys.exit 后的 interpreter 清理。
    # 必须 os._exit 强退整个进程,pytest 模式也一样(由 atexit 钩子处理)。
    os._exit(0 if failed == 0 else 1)


if __name__ == '__main__':
    _run_all()
