# -*- coding: utf-8 -*-
"""
使用 funboost 的 WATCHDOG broker 实现文件变化自动重启程序。

演示场景：
    1. funboost watchdog 监控 watch_dir 目录下的 .py 文件
    2. 文件变化后防抖 5 秒（同一文件多次变化只触发一次）
    3. 消费函数中杀死旧的 run.py 进程
    4. 启动新的 run.py 进程

运行方式：
    set PYTHONPATH=d:\\codes\\funboost
    python restart_with_funboost.py

测试方式：
    1. 程序启动后会先拉起 run.py，每 2 秒打印一次心跳
    2. 修改 watch_dir/my_app_config.py 中的 MESSAGE 值并保存
    3. 5 秒后自动杀死旧 run.py，启动新 run.py，心跳消息变成新值

对比 flask_realod.py 的差异：
    - flask_realod.py 直接用原生 watchdog 库
    - 本文件用 funboost 的 WATCHDOG broker，享受 funboost 的并发控制、防抖、日志等能力
    - 代码更简洁：只需写一个消费函数，不用手写 Observer / EventHandler
"""
import atexit
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

from funboost import boost, BoosterParams, BrokerEnum, enable_ctrl_c_quit_on_windows,ConcurrentModeEnum

# ============================================================================
# 路径配置
# ============================================================================
SCRIPT_DIR = Path(__file__).resolve().parent
TARGET_SCRIPT = str(SCRIPT_DIR / 'run.py')
WATCH_DIR = SCRIPT_DIR / 'watch_dir'

# ============================================================================
# 进程管理（全局状态）
# ============================================================================
_current_process = None
_process_lock = threading.Lock()
_last_restart_time = 0  # 全局防抖时间戳

# 全局防抖间隔（秒）：任何文件变化后，在此时间内不重复重启
GLOBAL_DEBOUNCE_SECONDS = 5


def _kill_current_process():
    """杀死当前 run.py 子进程"""
    global _current_process
    if _current_process is not None:
        print(f"[重启器] 杀死旧进程 (PID: {_current_process.pid})")
        _current_process.terminate()
        try:
            _current_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            _current_process.kill()
            _current_process.wait()
        print("[重启器] 旧进程已停止")
        _current_process = None


def _start_new_process():
    """启动新的 run.py 子进程"""
    global _current_process
    print(f"[重启器] 启动新进程: {TARGET_SCRIPT}")
    _current_process = subprocess.Popen(
        [sys.executable, TARGET_SCRIPT],
        cwd=str(SCRIPT_DIR),
    )
    print(f"[重启器] 新进程已启动 (PID: {_current_process.pid})")


# ============================================================================
# funboost watchdog 消费函数
# ============================================================================
@boost(BoosterParams(
    queue_name='restart_program_via_watchdog',
    broker_kind=BrokerEnum.WATCHDOG,
    concurrent_mode=ConcurrentModeEnum.SOLO,  
    broker_exclusive_config={
        # 监控目录
        'watch_path': WATCH_DIR.absolute().as_posix(),
        # 只监控 .py 文件
        'patterns': ['*.py'],
        'ignore_patterns': ['*/__pycache__/*', '*.pyc'],
        'ignore_directories': True,
        'case_sensitive': False,
        # 只监听 modified 事件（修改已有文件），避免 created+modified 双触发
        'event_types': ['modified'],
        # 递归监控子目录
        'recursive': True,
        # 纯监控模式，不删除 / 不归档文件
        'ack_action': 'none',
        'archive_path': None,
        # 不需要读取文件内容
        'read_file_content': False,
        # funboost 自带防抖：同一文件 5 秒内的多次变化只触发一次消费
        'debounce_seconds': 30,
    },
    should_check_publish_func_params=False,
))
def restart_program(event_type, src_path, dest_path, is_directory, timestamp, file_content):
    """
    文件变化时重启 run.py。

    两层防抖：
      1. funboost 的 debounce_seconds=5：同一文件的多次变化只触发一次
      2. 全局防抖 GLOBAL_DEBOUNCE_SECONDS=5：不同文件变化在 5 秒内只重启一次
    """
    global _last_restart_time

    print(f"\n[重启器] 收到文件事件: {event_type} - {src_path}")

    # ---- 第二层：全局防抖 ----
    now = time.time()
    elapsed = now - _last_restart_time
    if elapsed < GLOBAL_DEBOUNCE_SECONDS:
        print(f"[重启器] 全局防抖中，跳过本次重启（距上次重启仅 {elapsed:.1f}s < {GLOBAL_DEBOUNCE_SECONDS}s）")
        return
    _last_restart_time = now

    print(f"[重启器] 防抖通过，开始重启...")
    print(f"{'=' * 60}")

    with _process_lock:
        # 1. 杀死旧进程
        _kill_current_process()
        # 2. 启动新进程
        _start_new_process()

    print(f"{'=' * 60}\n")


# ============================================================================
# 启动入口
# ============================================================================
def start_initial_process():
    """启动时先拉起一次 run.py"""
    print(f"\n[重启器] 初始启动目标程序: {TARGET_SCRIPT}")
    _start_new_process()


if __name__ == '__main__':
    # 确保监控目录存在
    WATCH_DIR.mkdir(parents=True, exist_ok=True)

    # 程序退出时清理子进程
    atexit.register(_kill_current_process)

    # 1. 先启动 run.py
    start_initial_process()

    # 2. 启动 funboost watchdog 消费者（阻塞）
    print(f"\n[重启器] 开始监控目录: {WATCH_DIR}")
    print(f"[重启器] 修改该目录下的 .py 文件，{GLOBAL_DEBOUNCE_SECONDS} 秒后自动重启 {TARGET_SCRIPT}")
    print(f"[重启器] 按 Ctrl+C 停止\n")

    restart_program.consume()
    enable_ctrl_c_quit_on_windows()
