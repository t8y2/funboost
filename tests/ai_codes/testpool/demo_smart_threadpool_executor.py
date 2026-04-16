import importlib.util
import threading
import time
from pathlib import Path


def _load_smart_pool_class():
    repo_root = Path(__file__).resolve().parents[3]
    file_path = repo_root / "funboost" / "concurrent_pool" / "smart_threadpool_executor.py"
    spec = importlib.util.spec_from_file_location("smart_threadpool_executor", str(file_path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.SmartThreadPoolExecutor


def verify_no_lost_wakeup_race():
    SmartThreadPoolExecutor = _load_smart_pool_class()
    pool = SmartThreadPoolExecutor(max_workers=1, keep_alive=0.003, max_queue_size=10)

    # 先预热一个 worker，再人为拉长“入队路径”验证不会出现队列有任务但线程归零的卡死。
    pool.submit(lambda: None).result(timeout=1)
    original_put_nowait = pool._task_queue.put_nowait

    def slow_put_nowait(item):
        time.sleep(0.02)
        return original_put_nowait(item)

    pool._task_queue.put_nowait = slow_put_nowait
    result = pool.submit(lambda: 123).result(timeout=0.5)
    assert result == 123
    assert pool._task_queue.qsize() == 0
    assert pool._total_threads >= 1
    print("verify_no_lost_wakeup_race: OK")


def verify_scale_out_on_burst_submit():
    SmartThreadPoolExecutor = _load_smart_pool_class()
    pool = SmartThreadPoolExecutor(max_workers=6, keep_alive=0.2, max_queue_size=200)

    running = 0
    max_running = 0
    lock = threading.Lock()

    def job():
        nonlocal running, max_running
        with lock:
            running += 1
            if running > max_running:
                max_running = running
        time.sleep(0.05)
        with lock:
            running -= 1
        return 1

    futures = [pool.submit(job) for _ in range(24)]
    for fut in futures:
        fut.result(timeout=2)

    assert max_running >= 2, f"并发扩容失败，max_running={max_running}"
    print(f"verify_scale_out_on_burst_submit: OK (max_running={max_running})")


if __name__ == "__main__":
    verify_no_lost_wakeup_race()
    verify_scale_out_on_burst_submit()
    print("all smart-threadpool demos passed")
