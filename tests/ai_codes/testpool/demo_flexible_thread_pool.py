import asyncio
import importlib.util
import sys
import threading
import time
import types
from pathlib import Path


def _load_flexible_pool_class():
    repo_root = Path(__file__).resolve().parents[3]
    file_path = repo_root / "funboost" / "concurrent_pool" / "flexible_thread_pool.py"

    module_names = [
        "funboost",
        "funboost.concurrent_pool",
        "funboost.core",
        "funboost.core.loggers",
    ]
    backups = {name: sys.modules.get(name) for name in module_names}

    try:
        funboost_mod = types.ModuleType("funboost")
        concurrent_pool_mod = types.ModuleType("funboost.concurrent_pool")
        core_mod = types.ModuleType("funboost.core")
        loggers_mod = types.ModuleType("funboost.core.loggers")

        class DummyBasePool:
            pass

        class DummyFunboostFileLoggerMixin:
            logger = None

        class DummyLoggerLevelSetterMixin:
            pass

        class DummyLogger:
            def debug(self, *args, **kwargs):
                pass

            def error(self, *args, **kwargs):
                pass

            def exception(self, *args, **kwargs):
                pass

        dummy_logger = DummyLogger()
        DummyFunboostFileLoggerMixin.logger = dummy_logger

        concurrent_pool_mod.FunboostBaseConcurrentPool = DummyBasePool
        loggers_mod.FunboostFileLoggerMixin = DummyFunboostFileLoggerMixin
        loggers_mod.LoggerLevelSetterMixin = DummyLoggerLevelSetterMixin
        loggers_mod.flogger = dummy_logger
        loggers_mod.get_funboost_file_logger = lambda name: dummy_logger

        sys.modules["funboost"] = funboost_mod
        sys.modules["funboost.concurrent_pool"] = concurrent_pool_mod
        sys.modules["funboost.core"] = core_mod
        sys.modules["funboost.core.loggers"] = loggers_mod

        spec = importlib.util.spec_from_file_location("flexible_thread_pool", str(file_path))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.FlexibleThreadPool
    finally:
        for name, old_module in backups.items():
            if old_module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = old_module


def verify_scale_out_on_burst_submit():
    FlexibleThreadPool = _load_flexible_pool_class()
    pool = FlexibleThreadPool(max_workers=4, work_queue_maxsize=200)
    pool.KEEP_ALIVE_TIME = 0.2

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


def verify_specify_loop_auto_start():
    FlexibleThreadPool = _load_flexible_pool_class()
    loop = asyncio.new_event_loop()
    pool = FlexibleThreadPool(
        max_workers=2,
        work_queue_maxsize=20,
        specify_async_loop=loop,
        is_auto_start_specify_async_loop_in_child_thread=True,
    )
    pool.KEEP_ALIVE_TIME = 0.2

    async def async_job(x):
        await asyncio.sleep(0.02)
        return x * 2

    result = pool.submit(async_job, 21).result(timeout=1)
    assert result == 42
    assert loop.is_running()

    loop.call_soon_threadsafe(loop.stop)
    time.sleep(0.05)
    print("verify_specify_loop_auto_start: OK")


def verify_keep_alive_shrink_to_zero():
    FlexibleThreadPool = _load_flexible_pool_class()
    pool = FlexibleThreadPool(max_workers=2, work_queue_maxsize=20)
    pool.KEEP_ALIVE_TIME = 0.05
    pool.MIN_WORKERS = 0

    futures = [pool.submit(lambda: time.sleep(0.02)) for _ in range(6)]
    for fut in futures:
        fut.result(timeout=1)

    deadline = time.time() + 1.0
    while time.time() < deadline:
        if pool._total_threads == 0:
            break
        time.sleep(0.02)

    assert pool._total_threads == 0
    assert pool._free_threads == 0
    print("verify_keep_alive_shrink_to_zero: OK")


if __name__ == "__main__":
    verify_scale_out_on_burst_submit()
    verify_specify_loop_auto_start()
    verify_keep_alive_shrink_to_zero()
    print("all flexible-thread-pool demos passed")
