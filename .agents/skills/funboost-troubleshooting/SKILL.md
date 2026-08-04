---
name: funboost-troubleshooting
description: 当使用 funboost 遇到错误、消费不正常、进程退出等问题时使用。触发场景：消费者不启动、消息不消费、进程卡死、event loop 报错、日志不输出、PYTHONPATH 问题、Ctrl+C 无法退出。关键词：troubleshooting, FAQ, 排错, 调试, PYTHONPATH, run_forever, Ctrl+C, event loop, 日志。
---

# Funboost 故障排查

## 概述

本 skill 面向**用户和 AI agent**，在 funboost 运行异常时按症状快速定位原因。

**排查原则：**
1. 先确认 `PYTHONPATH` 和 `funboost_config.py` 是否被正确加载
2. 再核对 **queue_name / broker_kind / 连接配置** 是否发布端与消费端一致
3. 最后看日志（控制台 + 文件）中的连接错误、参数校验错误、重试信息

---

## 1. Windows 下 Ctrl+C 为什么无法退出程序

`consume()` 启动非守护线程（`daemon=False`），Windows 的 Ctrl+C 无法中断非守护线程。解决：

```python
from funboost import enable_ctrl_c_quit_on_windows

my_task.consume()
enable_ctrl_c_quit_on_windows()  # 让 Ctrl+C 能停止进程；不加也能消费，只是得关窗口或 kill
```

AI 测试脚本用 `time.sleep(N); os._exit(66)` 自动退出。

---

## 2. PYTHONPATH 和配置文件找不到

### 2.1 为什么必须设置

funboost 通过 `importlib.import_module('funboost_config')` 读取配置（见 `funboost/set_frame_config.py`）。框架**不限制项目目录结构**，脚本可在任意深层目录运行，因此需要把**含 `funboost_config.py` 的目录**加入 `sys.path`。

### 2.2 设置方式

```powershell
# PowerShell
$env:PYTHONPATH="D:\codes\myproj"

# CMD
set PYTHONPATH=D:\codes\myproj & python dir2\dir3\run.py

# Linux / macOS
export PYTHONPATH=/home/user/myproj/; python3 dir2/dir3/run.py
```

**多环境 / 多项目共享配置：**

```bash
export PYTHONPATH=/data/config_prod/:/data/app/myproject/
```

PYTHONPATH 中**靠前**的路径优先被 `import funboost_config` 命中。

### 2.3 配置加载优先级

1. 启动脚本所在目录的 `funboost_config.py`（`sys.path[0]`）
2. 项目根目录（`sys.path[1]`）的 `funboost_config.py`
3. 任意在 PYTHONPATH 中的目录

首次找不到时，框架会在 `sys.path[1]`（通常是项目根目录）自动生成配置模板。

### 2.4 常见错误

| 错误 | 处理 |
|------|------|
| `ModuleNotFoundError: funboost_config` | 设置 PYTHONPATH 指向项目根，或在项目根目录下运行脚本 |

> **何时需要设 PYTHONPATH**：只有当你从深层子目录或项目外部目录运行脚本时才需要。如果 cwd 就是项目根目录（含 `funboost_config.py`），Python 自动把 cwd 加入 `sys.path`，无需额外设置。funboost 允许脚本放在任意位置运行，这是它的灵活性所在。

---

## 3. 消费者不消费

确认写了 `my_task.consume()` 即可。

---

## 4. Event loop 报错

### 4.1 `RuntimeError: This event loop is already running`

**典型场景：** 使用 `ConcurrentModeEnum.ASYNC` + `specify_async_loop=loop`，同时在主线程又调用 `loop.run_forever()`，而 funboost 子线程已通过 `is_auto_start_specify_async_loop_in_child_thread=True`（默认）启动了同一个 loop。

**解决：**

```python
@boost(BoosterParams(
    queue_name='my_async',
    concurrent_mode=ConcurrentModeEnum.ASYNC,
    specify_async_loop=loop,
    is_auto_start_specify_async_loop_in_child_thread=False,  # 禁止 funboost 自动启动 loop
))
async def my_task(x): ...

# 主线程自己启动 loop（仅当业务代码也需要同一 loop 时）
loop.run_forever()
```

或：**不要**在主线程再 `run_forever()`，让 funboost 自动管理 loop。

### 4.2 `attached to a different loop` / aiohttp 连接池报错

ASYNC 模式在**子线程**的 loop 中运行协程。若连接池（aiohttp、aiomysql 等）在主线程 loop 创建，子线程无法使用。

**解决：传递 `specify_async_loop`**

```python
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
ss = aiohttp.ClientSession(loop=loop)

@boost(BoosterParams(
    queue_name='test_async',
    concurrent_mode=ConcurrentModeEnum.ASYNC,
    specify_async_loop=loop,
))
async def async_task(x):
    async with ss.request('get', url=url) as resp:
        ...
```

**不需要 `specify_async_loop` 的情况：** 函数内临时创建请求（如 `async with aiohttp.request(...)`），不用全局连接池。

**httpx、sqlalchemy 等** 通常无此问题。

### 4.3 在 FastAPI / 已有 event loop 中阻塞

**禁止**在 async 路由里用同步 `AsyncResult.result`——会阻塞整个 event loop。异步环境用 `AioAsyncResult` + `await`。

### 4.4 ASYNC 模式内写同步阻塞代码

`concurrent_mode=ASYNC` 时，函数内**不能**出现 `requests.get`、`time.sleep` 等同步阻塞，否则卡死整个 loop。IO 密集型可改用默认 `THREADING` 模式。

---

## 5. 日志不输出 / 找不到日志文件

### 5.1 日志位置

- **控制台：** 框架启动即有输出（含 funboost 标志、配置提示）
- **文件：** 由项目根目录 `nb_log_config.py` 的 **`LOG_PATH`** 决定（默认常为 `~/pythonlogs` 或 `D:/pythonlogs`）
- 消费者启动时会打印：`队列 xxx 的日志写入到 {LOG_PATH} 文件夹的 {log_filename} ...`

### 5.2 BoosterParams 日志相关字段

| 字段 | 说明 |
|------|------|
| `log_level=10` | 默认 DEBUG。**99.999% 的情况下保持 DEBUG 即可**——funboost 的 publisher/consumer 日志使用独立的 logger 命名空间，不会影响其他模块的日志级别 |
| `create_logger_file=False` | 仅控制台，不写文件 |
| `log_filename=None` | 默认用 `funboost.{queue_name}.log` |


### 5.4 AI agent 捕获输出（推荐）

脚本**最开头**设置环境变量（参考 `funboost/md_for_ai/for_ai_run_demo.py`）：

```python
import os
os.environ["LOG_PATH"] = r"D:/pythonlogs/ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = "my_test_run_20260630_1"  # 每次唯一后缀
os.environ["SYS_STD_FILE_NAME"] = "my_test_std_20260630_1"
```

运行后读取 `LOG_PATH` 下带日期前缀的文件，如 `2026-06-30.0001.my_test_run_20260630_1.print`。

### 5.5 排查清单

- [ ] `create_logger_file` 是否为 True
- [ ] `LOG_PATH` 目录是否存在、有写权限
- [ ] 是否把 `log_level` 设太高导致看不到 DEBUG
- [ ] 多进程消费时，各进程写同一日志文件（正常）

---

## 6. 安装依赖冲突

### 6.1 总体原则（FAQ 10.0）

funboost 固定了部分依赖版本，但**用户可自由选择三方包版本**。建议 `requirements.txt` **第一行写 `funboost`**，后面写项目依赖，让 pip 用你指定的版本覆盖。小版本差异通常无问题；报错再针对性降级/升级。

### 6.2 pydantic

funboost 40.0+ 使用 `BoosterParams`（Pydantic 模型）。臆造字段会 `ValidationError`——查 `md_for_ai` 确认字段名（如 `function_timeout` 不是 `timeout`）。

IDE 补全：PyCharm 安装 pydantic 插件；高版本 PyCharm 已内置支持。

### 6.3 pywin32（仅 Windows）

```
ImportError: DLL load failed while importing win32file
```

到 Python 安装目录的 `Scripts` 下执行：

```bash
python.exe pywin32_postinstall.py -install
```

（用**当前环境**对应的 `python.exe`）

### 6.5 SQLite 队列 read-only（Linux/macOS）

默认 `SQLLITE_QUEUES_PATH='/sqllite_queues'` 无写权限。在 `funboost_config.py` 改为有权限的路径：

```python
class BrokerConnConfig(DataClassBase):
    SQLLITE_QUEUES_PATH = '/home/user/myproj/sqlite_queues'
```

---

## 7. AI agent 运行 funboost 脚本注意事项

### 7.1 必须设置 PYTHONPATH

```powershell
$env:PYTHONPATH="D:\codes\funboost"   # 项目根目录
```

**在命令行设置**，不要假设脚本内设置一定生效（import funboost 时配置已加载）。

### 7.2 消费脚本不会自动退出

`consume()` 后进程永久运行。**禁止**直接 `python script.py` 不设超时。

**方式 A — subprocess + timeout（脚本无需 os._exit）：**

```python
import subprocess, os
subprocess.run(
    ['python', 'tests/ai_codes/my_test.py'],
    cwd=r'D:\codes\funboost',
    timeout=30,  # 一般 >10s，最大不超过 50s
    env={**os.environ, 'PYTHONPATH': r'D:\codes\funboost'},
)
```

⚠️ 不要用 `cmd /c "timeout /t 30 & python script.py"`——那是先空等再启动，不能限制 python 运行时长。

**方式 B — 脚本内 os._exit（推荐，配合日志文件）：**

```python
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"test_{unique_id}"
os.environ["SYS_STD_FILE_NAME"] = f"test_std_{unique_id}"
# ... push + consume ...
time.sleep(estimated_seconds)
os._exit(66)
```

然后读取 `LOG_PATH` 下输出文件验证。

### 7.3 超时 / sleep 时间估算

- 框架启动：5–10 秒
- 默认 `concurrent_num=50`，`qps=None`
- 无 qps：`吞吐量 ≈ concurrent_num / 函数耗时`
- 有 qps：`吞吐量 ≈ min(qps, concurrent_num / 函数耗时)`
- `合理时间 ≈ 启动(5-10s) + 消息数/吞吐量 + 缓冲(2-5s)`

### 7.4 禁止行为

- **禁止 flush Redis**（不要清空用户数据）
- 不要用 `threading.Thread` 包装 `consume()`
- 不要臆造 `BoosterParams` 字段名

---

## 8. 常见错误信息 → 解决方案对照表

| 错误信息 / 症状 | 原因 | 解决方案 |
|-----------------|------|----------|
| Ctrl+C 无反应（Windows） | 非守护线程阻止进程退出 | 如果想用 Ctrl+C 结束程序，加 `enable_ctrl_c_quit_on_windows()` |
| `ModuleNotFoundError: funboost_config` | 未设 PYTHONPATH / 无配置文件 | 设置 PYTHONPATH；首次运行自动生成模板 |
| Redis 连 localhost 失败 | 未加载用户 funboost_config | 检查 PYTHONPATH 与配置路径 |
| 消息 push 成功但不执行 | queue_name 不一致 | 发布/消费 queue_name 完全相同 |
| 消息 push 成功但不执行 | 未调用 consume() | 启动消费者 |
| 消息 push 成功但不执行 | broker_kind 不一致 | 统一 broker_kind 与连接配置 |
| `TypeError: ... unexpected keyword argument` | 消息字段与函数参数不匹配 | 对齐参数名；或用 `**kwargs` + `should_check_publish_func_params=False` |
| `ValidationError`（BoosterParams） | 臆造或拼错字段名 | 查 `BoosterParams` 官方字段（如 `max_retry_times`） |
| `RuntimeError: This event loop is already running` | 同一 loop 被 funboost 与主线程重复 `run_forever` | 设 `is_auto_start_specify_async_loop_in_child_thread=False` 或去掉主线程 `run_forever` |
| `attached to a different loop` / aiohttp 超时上下文错误 | 连接池 loop 与消费 loop 不一致 | `specify_async_loop=主线程loop` |
| `ImportError: DLL load failed ... win32file` | pywin32 未正确安装 | 运行 `pywin32_postinstall.py -install` |
| `read-only file system ... /sqllite_queues` | SQLite 路径无写权限 | 修改 `SQLLITE_QUEUES_PATH` |
| 日志「掉线或关闭消费者」「重新放入未确认任务」 | ACK broker 重启后的正常行为 | 无需处理；不需 ACK 则用 `BrokerEnum.REDIS` |
| `AsyncResult.result` 在 async 环境卡死 | 阻塞 event loop | 用 `AioAsyncResult` + `await` |
| 进程「卡死」不退出 | consume 永久循环 | 预期行为；测试用 timeout 或 `os._exit` |
| 找不到日志文件 | LOG_PATH 或 create_logger_file | 查启动日志中的路径；设 `LOG_PATH` 环境变量 |
| funboost 30.0 配置升级报错 | 旧版 flat 配置 | 删除旧配置，用 `BrokerConnConfig` 类 |
| RPC 无返回值 | 未开 RPC 模式 | `is_using_rpc_mode=True` 且配置 Redis |

---

## 快速决策树

```
遇到问题
├─ 配置文件找不到？
│   └─ 从项目根目录运行，或设 PYTHONPATH
├─ 消费者不消费？
│   └─ 确认调了 consume()
├─ Windows Ctrl+C 停不掉？
│   └─ 加 enable_ctrl_c_quit_on_windows()
├─ asyncio 报错？
│   └─ specify_async_loop | 勿重复 run_forever | 勿在 ASYNC 里写同步阻塞
└─ 安装/依赖报错？
    └─ pywin32_postinstall | pydantic 字段 | requirements 第一行 funboost
```

---

## 参考文档

- FAQ：`funboost_docs/source/articles/c6.md`（6.18 PYTHONPATH、6.25 Ctrl+C、6.26 ASYNC、6.28 ACK 提示）
- 安装兼容：`funboost_docs/source/articles/c10.md`（pywin32、APScheduler、SQLite read-only）
- 配置加载：`funboost/set_frame_config.py`
- Ctrl+C 实现：`funboost/utils/ctrl_c_end.py`
- AI 运行规范：`AGENTS.md` 第十二节
- 测试 skill：`.agents/skills/developing-funboost-testing/SKILL.md`

## 相关 Skill

- `developing-funboost-testing` — 编写与运行测试
- `funboost-async-programming` — async/await 异步编程
