"""round3b 验证 funboost-troubleshooting SKILL — enable_ctrl_c_quit_on_windows import 与 daemon=False"""
import inspect
import os
import sys
import threading
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"r2_ctrl_c_daemon_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"r2_ctrl_c_daemon_std_{_ts}"

PASS = True


def report(name: str, ok: bool, detail: str = ""):
    global PASS
    if not ok:
        PASS = False
    status = "PASS" if ok else "FAIL"
    msg = f"[{status}] {name}"
    if detail:
        msg += f" — {detail}"
    print(msg)


def find_daemon_false_in_source(source: str, context: str) -> bool:
    """检查源码片段中是否显式使用 daemon=False"""
    return "daemon=False" in source


if __name__ == "__main__":
    # SKILL: from funboost import enable_ctrl_c_quit_on_windows
    try:
        from funboost import enable_ctrl_c_quit_on_windows
        src_file = inspect.getfile(enable_ctrl_c_quit_on_windows)
        report(
            "from funboost import enable_ctrl_c_quit_on_windows",
            callable(enable_ctrl_c_quit_on_windows),
            src_file,
        )
        report(
            "定义模块为 funboost.utils.ctrl_c_end",
            enable_ctrl_c_quit_on_windows.__module__ == "funboost.utils.ctrl_c_end",
        )
    except Exception as e:
        report("enable_ctrl_c_quit_on_windows import", False, str(e))

    # 验证 SKILL 声明: consume() 启动非守护线程 daemon=False
    try:
        from funboost import boost, BoosterParams, BrokerEnum
        from funboost.consumers.base_consumer import ConcurrentModeDispatcher
        from funboost.concurrent_pool.flexible_thread_pool import FlexibleThreadPool
        from funboost.concurrent_pool.async_pool_executor import AsyncPoolExecutor

        @boost(BoosterParams(
            queue_name=f"r2_daemon_check_{_ts}",
            broker_kind=BrokerEnum.MEMORY_QUEUE,
            concurrent_num=2,
        ))
        def daemon_check_task(x):
            return x

        consumer = daemon_check_task.consumer
        dispatcher = consumer._concurrent_mode_dispatcher

        # 1) schedulal_task_with_no_block 源码含 daemon=False
        dispatch_src = inspect.getsource(dispatcher.schedulal_task_with_no_block)
        report(
            "ConcurrentModeDispatcher.schedulal_task_with_no_block 使用 daemon=False",
            find_daemon_false_in_source(dispatch_src, "schedulal_task_with_no_block"),
        )

        # 2) start_consuming_message 中心跳线程 daemon=False
        start_src = inspect.getsource(consumer.start_consuming_message)
        report(
            "AbstractConsumer.start_consuming_message 心跳线程 daemon=False",
            "keep_circulating(60, block=False, daemon=False)" in start_src,
        )

        # 3) THREADING 模式默认 FlexibleThreadPool 工作线程 daemon=False
        pool_src = inspect.getsource(FlexibleThreadPool.submit)
        report(
            "FlexibleThreadPool 工作线程 daemon=False",
            "threading.Thread(target=self._worker, daemon=False)" in pool_src,
        )

        # 4) ASYNC 模式 loop 线程 daemon=False
        async_src = inspect.getsource(AsyncPoolExecutor.__init__)
        report(
            "AsyncPoolExecutor loop 线程 daemon=False",
            "daemon=False" in async_src,
        )

        # 5) 运行时验证: consume() 后 _dispatch_task 循环线程 daemon=False
        daemon_check_task.consume()
        time.sleep(2)
        non_daemon_threads = [
            t for t in threading.enumerate()
            if not t.daemon and t is not threading.main_thread()
        ]
        report(
            "consume() 后存在非守护线程(daemon=False)",
            len(non_daemon_threads) > 0,
            f"count={len(non_daemon_threads)}, names={[t.name for t in non_daemon_threads[:5]]}",
        )
    except Exception as e:
        report("daemon=False 源码/运行时验证", False, str(e))

    print(f"\n=== 最终结果: {'PASS' if PASS else 'FAIL'} ===")
    sys.stdout.flush()
    time.sleep(12)
    os._exit(66)
