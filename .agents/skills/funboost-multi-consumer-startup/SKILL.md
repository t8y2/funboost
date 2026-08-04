---
name: funboost-multi-consumer-startup
description: 当需要在 funboost 中连续启动多个函数消费（多个消费者同时运行）时使用。触发场景：一个脚本里同时跑多个 @boost 任务函数的消费、为不同队列启动多个消费者。关键词：连续启动, 多个消费者, consume, multi consume, 同时消费, 启动多个, 多个队列消费。
---

# Funboost 连续启动多个消费者

## 概述

Funboost 的 `consume()` **天生非阻塞**——调用后立即返回，消费在后台运行。因此连续启动多个函数消费非常简单：**最基本的用法就是 2 个函数直接顺序调用 `consume()`**，不需要线程、进程或任何包装。

## 适用场景

- 一个脚本里同时运行多个任务函数的消费者
- 多个队列同时被消费

## 铁律（绝对不可违反）

1. **禁止用 `threading.Thread` 包装 `consume()`** — 如 `threading.Thread(target=func1.consume).start()` 是多此一举，`func1.consume()` 本身不会阻塞主线程
2. **禁止用 `subprocess` 或 `multiprocessing.Process` 逐个启动消费** — 框架已从层面支持直接连续调用

## 速查表

| 启动方式 | 代码 | 说明 |
|----------|------|------|
| 连续启动多个 | `func1.consume(); func2.consume()` | 最基本的用法，直接顺序调用 |
| 主线程保活 | `enable_ctrl_c_quit_on_windows()` | 主线程无其他阻塞任务时建议调用，Ctrl+C 可退出 |

## 核心代码模式

### 最基本的连续启动：2 个函数顺序调用

```python
from funboost import boost, BoosterParams, BrokerEnum, enable_ctrl_c_quit_on_windows

@boost(BoosterParams(queue_name="queue_a", broker_kind=BrokerEnum.SQLITE_QUEUE, concurrent_num=3, qps=5))
def task_a(x: int):
    return x * 1

@boost(BoosterParams(queue_name="queue_b", broker_kind=BrokerEnum.SQLITE_QUEUE, concurrent_num=3, qps=5))
def task_b(x: int):
    return x * 10

if __name__ == "__main__":
    task_a.push(1); task_b.push(1)

    # 最基本的连续启动 —— 2 个函数直接顺序调用，互不阻塞
    task_a.consume()
    task_b.consume()

    # 主线程保活（可选，不加也能通过关闭窗口/kill 进程停止）
    enable_ctrl_c_quit_on_windows()
```

> 每个消费者拥有独立的并发池、控频、重试等配置，互不影响。函数更多时同理，继续顺序调用 `func3.consume()` 即可。

## 验证脚本

`scripts/demo_multi_consume.py` 验证多个消费者连续启动后各自独立消费，可运行：


> 运行前必须设置 `PYTHONPATH=项目根目录`。

## 常见错误

| 错误写法 | 正确写法 |
|----------|----------|
| `threading.Thread(target=func1.consume).start()` | `func1.consume()` 直接调用 |
| `subprocess.Popen([...func1...])` 启动消费 | `func1.consume()` |
| 用 `time.sleep` 前没启动消费就 push | 先 push 再 consume，或 push 后 consume |
| 脚本没有保活导致主线程退出 | 末尾加 `enable_ctrl_c_quit_on_windows()` |

## 相关 Skill

- `using-funboost-basics` — 基础使用入门（启动消费、push/publish）
