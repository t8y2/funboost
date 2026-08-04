# -*- coding: utf-8 -*-
"""
被监控重启的目标程序。

修改 watch_dir/my_app_config.py 后，restart_with_funboost.py 会杀掉本进程并重新启动。
"""
import os
import sys
import time

# 把 watch_dir 加入 import 路径，这样 run.py 会 import watch_dir 下的配置
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'watch_dir'))

from my_app_config import APP_NAME, INTERVAL, MESSAGE  # noqa: E402


if __name__ == '__main__':
    print(f"\n[{APP_NAME}] 进程启动, PID: {os.getpid()}")
    print(f"[{APP_NAME}] 当前配置: INTERVAL={INTERVAL}s, MESSAGE={MESSAGE!r}")
    print(f"[{APP_NAME}] 修改 watch_dir/my_app_config.py 可触发自动重启\n")

    count = 0
    while True:
        count += 1
        print(f"[{APP_NAME}] 第 {count} 次心跳: {MESSAGE}  {time.strftime('%H:%M:%S')}")
        time.sleep(INTERVAL)
