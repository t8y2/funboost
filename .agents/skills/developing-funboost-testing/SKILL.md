---
name: developing-funboost-testing
description: 当需要为 funboost 框架编写测试、运行测试脚本、或验证新 broker/mixin 实现时使用。触发场景：编写测试脚本、验证消费者/发布者功能、AI Agent 运行 funboost 脚本。关键词：test funboost, 写测试, 运行测试, test_frame, regression test, 验证消费, AI testing, os._exit, timeout。
compatibility: Python 3.7+, funboost source code access, Windows with PowerShell
---

# Funboost 测试规范

## 概述

Funboost 使用独立的 Python 脚本作为测试（非 pytest）。核心挑战：`consume()` 启动后是无限循环，测试必须设定超时或 `os._exit()` 来终止。

**核心原则：** 每个测试必须有终止机制——要么外部超时，要么内部 `os._exit()`。

## 适用场景

- 为新 broker 实现编写测试
- 验证 mixin/扩展行为
- 运行已有测试脚本
- 修复 bug 后编写回归测试
- AI Agent 需要验证 funboost 代码

## 测试目录规范

| 类型 | 目录 | 场景 |
|------|------|------|
| AI 编写的 demo/示例 | `tests/ai_codes/ai_demos/{子文件夹}/` | AI 写的示例代码（必须新建子文件夹） |
| AI 回归测试 | `tests/ai_codes/regression_testing/` | AI 测试框架修改 |
| 人工测试 | `test_frame/` | 框架作者的手动测试 |

**注意：** AI 写 demo 必须在 `ai_demos/` 下新建合理的子文件夹，不要直接在 `ai_demos/` 根下放脚本。

## 测试脚本模板

```python
"""测试：[测试内容描述]"""
import os
import time

# PYTHONPATH 必须在运行脚本前通过命令行设置，不要在脚本内设置
# PowerShell: $env:PYTHONPATH="D:\codes\funboost"
# CMD: set PYTHONPATH=D:\codes\funboost

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = "test_feature_xyz_run1"
os.environ["SYS_STD_FILE_NAME"] = "test_feature_xyz_std1"

from funboost import boost, BoosterParams, BrokerEnum

@boost(BoosterParams(
    queue_name="test_feature_xyz",
    broker_kind=BrokerEnum.SQLITE_QUEUE,  # 零配置，适合测试
    concurrent_num=5,
    qps=10,
))
def test_task(x: int):
    print(f"处理 {x}，结果 = {x * 2}")
    return x * 2

if __name__ == "__main__":
    # 发布测试消息
    for i in range(10):
        test_task.push(i)

    # 启动消费
    test_task.consume()

    # 等待足够时间后自动退出
    time.sleep(15)
    os._exit(66)
```

## 两种运行方式（AI Agent）

### 方式一：内部 os._exit + 日志文件（推荐）

```python
import os
import time

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = "test_xyz_run1"
os.environ["SYS_STD_FILE_NAME"] = "test_xyz_std1"

# ... 测试代码 ...

time.sleep(15)
os._exit(66)
```

运行后读取 `D:\pythonlogs\ai_console_outs\` 下生成的日志文件查看输出（nb_log 会自动添加日期前缀，如 `2026-06-29.0001.test_xyz_run1.print`，需模糊搜索匹配）。

**重要：** 每次运行使用不同的文件名后缀（时间戳或序号），避免读到上次的老日志。

### 方式二：subprocess.run 外部超时

```python
import subprocess
result = subprocess.run(
    ['python', 'tests/ai_codes/my_test.py'],
    cwd=r'D:\codes\funboost',
    timeout=30,
    env={**os.environ, 'PYTHONPATH': r'D:\codes\funboost'}
)
```

脚本无需 `os._exit` — subprocess 超时后自动终止子进程。

⚠️ **不要使用** `cmd /c "timeout /t N & python xxx.py"`：`timeout` 命令是先空等 N 秒再启动 python，不会限制 python 运行时长。

**超时/休眠时间估算（一般要大于 10 秒）：**
- 框架启动时间：5-10 秒
- 默认值：`concurrent_num=50`，`qps=None`（不限制）
- 不设 qps 时：`实际吞吐量 ≈ concurrent_num / 函数耗时`
- 设 qps 时：`实际吞吐量 ≈ min(qps, concurrent_num / 函数耗时)`
- `合理时间 ≈ 框架启动时间(5-10秒) + (消息个数 / 实际吞吐量) + 缓冲时间(2-5秒)`
- **最大不超过 50 秒**

## 测试验证清单

Broker 测试：
- [ ] 消息发布成功（无发布错误）
- [ ] 消费者正常启动（无错误）
- [ ] 消息被消费（print/日志显示处理结果）
- [ ] 正确数量的消息被处理
- [ ] ACK 正常工作（消息不会重复出现）
- [ ] 重试功能正常（模拟失败时）

Mixin 测试：
- [ ] Mixin 初始化成功（`custom_init` 执行）
- [ ] 钩子方法触发（前置/后置）
- [ ] super() 链正常工作（MRO 不断裂）
- [ ] `user_options` 中的配置被正确读取
- [ ] 多个 mixin 组合正常

## PYTHONPATH 必须设置

**运行任何 funboost 脚本前必须设置 PYTHONPATH = 项目根目录：**

```powershell
# PowerShell
$env:PYTHONPATH="D:\codes\funboost"

# CMD
set PYTHONPATH=D:\codes\funboost
```

**为什么必须设置：**
1. 解决 `import funboost` 的路径问题
2. **funboost 启动时通过 `importlib.import_module('funboost_config')` 从 `sys.path` 中加载配置文件。** 设置 PYTHONPATH 让项目根目录进入 `sys.path`，框架就能找到 `funboost_config.py` 并读取 Redis/RabbitMQ 等连接配置。不设则用框架默认值（localhost）。首次运行找不到时会自动生成配置模板。

## 示例：测试新 Broker

```python
"""测试：TXT 文件 broker"""
import os
import time

# PYTHONPATH 须在命令行设置，脚本内设置无效
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = "test_txt_broker_run1"
os.environ["SYS_STD_FILE_NAME"] = "test_txt_broker_std1"

from funboost import boost, BoosterParams, BrokerEnum

@boost(BoosterParams(
    queue_name="test_txt_broker",
    broker_kind=BrokerEnum.TXT_FILE,
    concurrent_num=3,
    qps=5,
))
def txt_task(name: str, value: int):
    result = f"{name}={value * 10}"
    print(f"[OK] {result}")
    return result

if __name__ == "__main__":
    # 阶段1：发布
    for i in range(5):
        txt_task.push(f"item_{i}", value=i)
    print(f"已发布 5 条消息")

    # 阶段2：消费
    txt_task.consume()

    # 阶段3：等待并验证
    time.sleep(15)
    print("测试完成")
    os._exit(66)
```

## 示例：测试 Mixin

```python
"""测试：自定义监控 mixin"""
import os
import time

# PYTHONPATH 须在命令行设置，脚本内设置无效
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = "test_mixin_run1"
os.environ["SYS_STD_FILE_NAME"] = "test_mixin_std1"

from funboost import boost, BoosterParams, BrokerEnum
from funboost.consumers.base_consumer import AbstractConsumer

class CounterMixin(AbstractConsumer):
    def custom_init(self):
        super().custom_init()
        self._success_count = 0
        self._fail_count = 0

    def _both_sync_and_aio_frame_custom_record_process_info_func(self, status, kw):
        super()._both_sync_and_aio_frame_custom_record_process_info_func(status, kw)
        if status.success:
            self._success_count += 1
        else:
            self._fail_count += 1
        print(f"[COUNTER] success={self._success_count}, fail={self._fail_count}")

@boost(BoosterParams(
    queue_name="test_counter_mixin",
    broker_kind=BrokerEnum.SQLITE_QUEUE,
    consumer_override_cls=CounterMixin,
    concurrent_num=2,
    qps=5,
))
def counted_task(x: int):
    if x % 3 == 0:
        raise ValueError(f"模拟失败 {x}")
    return x * 2

if __name__ == "__main__":
    for i in range(10):
        counted_task.push(i)

    counted_task.consume()
    time.sleep(20)
    os._exit(66)
```

## 常见错误

| 错误 | 修正 |
|------|------|
| 没有超时/退出机制 | 必须用外部 timeout 或 `os._exit()` |
| 忘记设置 PYTHONPATH | 运行前必须设置 |
| 超时太短（< 10 秒） | 框架启动需要 5-10 秒 |
| 读到上次的旧日志 | 每次运行用不同的文件名 |
| 用 pytest 而不是独立脚本 | funboost 测试是独立 `.py` 文件 |
| 没有验证输出 | 检查控制台输出是否含预期 print 内容 |
| 无限运行 | 最长 50 秒后必须终止 |
| 测试间没有隔离 | 使用 `SQLITE_QUEUE` 或唯一队列名进行隔离 |

## 快速排错

- 消息没有被消费：检查 broker 连接配置
- import 错误：确认 PYTHONPATH 设置正确
- 超时无输出：框架可能卡在缺失依赖上
- 消息消费了但结果不对：检查函数签名是否与发布参数匹配

## 相关 Skill

- `using-funboost-basics` — 基础使用入门
- `funboost-troubleshooting` — 排错与 FAQ
