# 用 funboost watchdog broker 实现文件变化自动重启程序

## 例子的意义

演示 funboost 的 `WATCHDOG` broker 能力：**把文件系统事件当消息队列**，文件变化自动触发消费函数，在函数内杀旧进程、启新进程。

## 对比原生 watchdog

同样的"文件变化重启程序"逻辑，用原生 watchdog 需要手写 Observer、EventHandler、防抖 Timer、进程管理（参考上级目录的 `flask_realod.py`，200+ 行）。

用 funboost 只需一个 `@boost` 装饰器 + 一个消费函数（`restart_with_funboost.py`），防抖、并发控制、日志全部自带。

## 文件说明

| 文件 | 作用 |
|------|------|
| `restart_with_funboost.py` | 重启管理器，funboost WATCHDOG 消费者 |
| `run.py` | 被重启的目标程序 |
| `watch_dir/my_app_config.py` | 应用配置，改这个文件触发重启 |

## 运行

```powershell
$env:PYTHONPATH="D:\codes\funboost"
python test_frame\test_watchdog_broker\demo_restart_programe_use_funboost_watchdog\restart_with_funboost.py
```

修改 `watch_dir/my_app_config.py` 中的 `MESSAGE` 值并保存，5 秒后自动重启 `run.py`。
