---
name: funboost-funweb-ops
description: 当需要使用 funboost 的 Web 管理界面进行队列运维时使用。触发场景：启动管理后台、查看消费状态、查看消费者配置、失败重投、查看结果、定时任务管理。关键词：funweb, Web 管理, 运维, start_funboost_web_manager, 队列监控, 消费曲线。
compatibility: Python 3.7+, funboost with `pip install funboost[flask]`
---

# Funweb 队列运维（Web 管理界面）

## 概述

**funweb** 是 `funboost_web_manager` 的简称，是 funboost 内置的 Flask Web 管理界面。安装 funboost 后无需单独下载 Web 代码，即可在浏览器中完成队列运维：查看消费结果、管理消费者、失败重投、RPC 调用、定时任务管理等。

**核心原则：** Web 界面依赖 Redis 心跳上报获取运行时信息；函数结果持久化依赖 MongoDB（可选）。大部分运维页面只需 Redis，不必安装 Mongo。

**等价导入路径：**

```python
from funboost.funweb.app import start_funboost_web_manager
# 与 from funboost.funboost_web_manager.app import start_funboost_web_manager 效果相同
```

## 适用场景

- 启动 funboost Web 管理后台，在浏览器中运维队列
- 查看函数消费状态、失败记录，一键重新投递失败消息
- 查看在线消费者及其 BoosterParams 配置
- 按 IP 或队列名查看在线消费者
- 在页面上发起 RPC 调用、管理 APScheduler 定时任务
- 配置队列告警、脚本部署、日志查看、服务器资源监控

---

## 1. 启动方式

### 前置依赖

```bash
pip install funboost[flask]
```

### 必须设置 PYTHONPATH

Web 服务需要读取项目根目录下的 `funboost_config.py`（Redis/Mongo 连接等配置），**启动前必须将 PYTHONPATH 设为项目根目录**：

| 平台 | 命令 |
|------|------|
| Linux/macOS | `export PYTHONPATH=/path/to/your/project` |
| Windows CMD | `set PYTHONPATH=D:\codes\your_project` |
| Windows PowerShell | `$env:PYTHONPATH = "D:\codes\your_project"` |

### 方式一：命令行启动（推荐独立运维）

```bash
python -m funboost.funweb.app
```

Linux 生产环境可用 gunicorn（性能更好）：

```bash
gunicorn -w 4 --threads=30 --bind 0.0.0.0:27018 funboost.funweb.app:app
```

### 方式二：代码中启动（可与消费程序同进程）

```python
from funboost.funweb.app import start_funboost_web_manager

# 默认：host=0.0.0.0, port=27018, block=False（后台线程启动，不阻塞主线程）
start_funboost_web_manager()

# 常用参数
start_funboost_web_manager(
    host="0.0.0.0",
    port=27018,
    block=False,          # True 则阻塞当前线程（等同 app.run）
    debug=False,
    care_project_name="my_project",  # 启动时直接设置关注的项目名
)
```

### 访问与登录

- 浏览器打开：`http://127.0.0.1:27018`（或部署机器 IP:端口）
- 默认账号：`admin` / `123456`
- 可通过环境变量自定义：`FUNWEB_USER`、`FUNWEB_PASSWORD`、`FUNWEB_SECRET_KEY`

### funweb 目录结构（源码位置）

```
funboost/funweb/
├── app.py                  # Flask 入口，含 start_funboost_web_manager()
├── functions.py            # 结果查询、消费速率等业务逻辑
├── flask_bps/              # 蓝图模块
│   ├── dashboard.py        # Dashboard 概览
│   ├── queue_alerts.py     # 告警配置
│   ├── script_deploy.py    # 脚本部署
│   ├── system_monitor.py   # 资源监控
│   └── log_viewer.py       # 日志查看器
└── templates/              # 前端页面模板
    ├── fun_result_table.html       # 函数结果表
    ├── queue_op.html               # 队列操作
    ├── timing_jobs_management.html # 定时任务
    └── ...
```

---

## 2. 核心功能列表

### 数据监控

| 页面 | 功能 |
|------|------|
| **Dashboard** | 队列运行概览仪表盘 |
| **函数结果表** | 查看/搜索函数实时消费状态和结果；失败消息可点击「重新运行」一键重投 |
| **消费速率图** | 实时与历史消费速度统计 |
| **告警配置** | 积压/QPS 骤降/消费者掉线/失败率/耗时过高 5 类告警，支持企微/钉钉/飞书/Webhook |

### 消费者管理

| 页面 | 功能 |
|------|------|
| **运行中消费者 (by ip)** | 按机器 IP 分组查看在线消费者 |
| **运行中消费者 (by queue)** | 按队列名分组查看在线消费者 |

### 队列操作（核心运维）

| 操作 | 说明 |
|------|------|
| 查看队列深度 | 剩余待消费消息数量 |
| 清空队列 | 清空队列中待消费消息 |
| 查看消费者详情 | 查看某队列所有消费者的 IP、PID、启动时间等 |
| 查看 BoosterParams 配置 | 在页面上查看消费者完整装饰器参数（只读） |
| 消费曲线图 | 历史运行次数、失败次数、近 10 秒完成/失败、平均耗时、剩余消息数 |

### 其他功能

| 页面 | 功能 |
|------|------|
| **RPC 调用** | 在网页上向队列发布消息并获取函数执行结果；也可按 task_id 查结果 |
| **定时任务** | 增删改查 APScheduler 定时任务，支持 cron/interval/date 触发器 |
| **脚本部署** | 进程守护、Git 更新重启、日志查看（不依赖 funboost 消费） |
| **日志查看器** | 通用日志文件查看，支持时间范围筛选、关键字搜索、SSE 实时 tail |
| **资源监控** | CPU/内存/磁盘使用率实时仪表盘与历史曲线 |
| **设置 care_project_name** | 过滤只显示指定 `project_name` 下的队列 |

---

## 3. 配置要求

### Redis（大部分功能必需）

在 `funboost_config.py` 中配置 Redis 连接（`BrokerConnConfig.REDIS_*`）。以下功能依赖 Redis：

- 消费者心跳与在线状态
- 队列深度、消费指标曲线
- 队列深度、消费指标曲线
- 定时任务存储（`job_store_kind='redis'`）
- 告警规则与记录
- 脚本部署配置持久化

### 关键 BoosterParams 字段

```python
from funboost import BoosterParams, FunctionResultStatusPersistanceConfig, BrokerEnum

class WebOpsBoosterParams(BoosterParams):
    project_name: str = "my_project"  # 配合 care_project_name 过滤队列
    broker_kind: str = BrokerEnum.REDIS_ACK_ABLE

    # 【必需】向 Redis 发送消费者心跳，否则 Web 无法获取队列运行信息
    is_send_consumer_heartbeat_to_redis: bool = True

    # 【RPC 页面必需】启用 RPC 模式才能在网页上获取函数返回值
    is_using_rpc_mode: bool = True

    # 【函数结果表必需】持久化消费状态和结果到 MongoDB
    function_result_status_persistance_conf: FunctionResultStatusPersistanceConfig = (
        FunctionResultStatusPersistanceConfig(
            is_save_result=True,
            is_save_status=True,
            expire_seconds=7 * 24 * 3600,
        )
    )
```

| 配置项 | 作用 | 缺少时的影响 |
|--------|------|-------------|
| `is_send_consumer_heartbeat_to_redis=True` | 消费者每 10 秒向 Redis 上报心跳和运行指标 | 队列操作、消费者列表、告警、曲线图均无数据 |
| `project_name` | 项目标签 | 无法通过 care_project_name 过滤 |
| `function_result_status_persistance_conf` | 结果/status 持久化 | 函数结果表、消费速率图无数据 |
| `is_using_rpc_mode=True` | 启用 RPC | RPC 调用页面无法获取返回值 |

### MongoDB（可选，仅影响前 2 个数据监控页面）

- **函数结果表**、**消费速率图** 依赖 MongoDB 存储消费结果
- 不使用这两个页面则**不必安装 Mongo**
- Mongo 连接在 `funboost_config.py` 的 `BrokerConnConfig.MONGO_CONNECT_URL` 配置
- funweb 启动时会自动检测 Mongo 是否可用；不可用时队列列表仍显示，但结果 count 为 -1

### care_project_name（项目过滤）

在 Web 页面「设置 care_project_name」中填写项目名，或在代码启动时传入：

```python
start_funboost_web_manager(care_project_name="my_project")
```

设置后界面只显示 `BoosterParams.project_name` 匹配的队列，减少无关信息干扰。设为 `all` 或留空则显示全部。

---

## 4. 多消费者管理

### 查看在线消费者

- **by ip**：查看某台机器上运行了哪些队列的消费者（IP、PID、进程信息）
- **by queue**：查看某队列有哪些消费者实例在运行

**前提：** 对应队列的 `@boost` 装饰器必须设置 `is_send_consumer_heartbeat_to_redis=True`。

### 队列级运维操作

在「队列操作」页面选中队列后可：

1. 查看该队列所有消费者详情（多进程 `multi_process_consume` 场景下每个进程独立显示）
2. 查看每个消费者的完整 `BoosterParams` 配置
3. 查看该队列**所有在线消费者**的完整 `BoosterParams` 配置（只读）
4. 查看消费曲线：近 10 秒完成数、失败数、平均耗时、剩余消息数等

### 多进程消费示例

```python
@boost(WebOpsBoosterParams(queue_name="worker_queue", qps=2, concurrent_num=10))
def process_task(x):
    return x * 2

if __name__ == "__main__":
    start_funboost_web_manager(port=27018)
    process_task.multi_process_consume(4)  # 4 进程，Web 可看到 4 个消费者
    process_task.push(1)
    enable_ctrl_c_quit_on_windows()
```

---

## 5. 定时任务管理界面

### 入口

左侧导航 → **定时任务**（`timing_jobs_management.html`）

### 功能

- 列表展示所有队列的定时任务（计划总数、运行中/暂停数统计）
- 新增任务：支持 **cron 定时**、**interval 间隔**、**date 一次性** 三种触发器
- 查看任务详情、编辑、删除
- 暂停/恢复单个 Job，或暂停/恢复整个 Scheduler（定时器）

### 重要说明

- 定时任务数据存储在 Redis（`job_store_kind='redis'`），Web 管理**不依赖导入用户的任务函数**，可跨项目统一管理
- **推荐做法：** 在消费脚本中用 `ApsJobAdder` 启动 Scheduler 和定时器；Web 后台的 Scheduler 保持「暂停」状态，仅用于增删改查
- 暂停 Scheduler = 该队列下所有定时任务停止调度（配置保留）；暂停 Job = 仅暂停单个任务

### 代码侧配合（ApsJobAdder）

```python
from funboost import boost, BoosterParams, BrokerEnum, ApsJobAdder

@boost(BoosterParams(queue_name="cron_queue", broker_kind=BrokerEnum.REDIS_ACK_ABLE))
def daily_report(type: str):
    print(f"running daily report: {type}")

if __name__ == "__main__":
    # 在消费脚本中启动定时器（推荐）
    ApsJobAdder(daily_report, job_store_kind="redis").add_push_job(
        trigger="cron", hour=2, minute=0, kwargs={"type": "daily"}, id="job1"
    )
    daily_report.consume()
```

Web 页面通过 `/funboost/get_timing_jobs?job_store_kind=redis` 等 FaaS 接口读写定时任务。

---

## 6. 完整代码示例

```python
import asyncio
import random
import time

from funboost import (
    boost, BoosterParams, BrokerEnum, ConcurrentModeEnum,
    FunctionResultStatusPersistanceConfig, enable_ctrl_c_quit_on_windows,
)
from funboost.funweb.app import start_funboost_web_manager


class MyBoosterParams(BoosterParams):
    project_name: str = "test_project1"
    broker_kind: str = BrokerEnum.REDIS_ACK_ABLE
    is_send_consumer_heartbeat_to_redis: bool = True   # Web 运维必需
    is_using_rpc_mode: bool = True                     # RPC 页面必需
    booster_group: str = "test_group1"
    function_result_status_persistance_conf: FunctionResultStatusPersistanceConfig = (
        FunctionResultStatusPersistanceConfig(
            is_save_result=True,
            is_save_status=True,
            expire_seconds=7 * 24 * 3600,
        )
    )


@boost(MyBoosterParams(queue_name="queue_test_g01t", qps=1))
def f(x):
    time.sleep(5)
    if random.random() > 0.9:
        raise ValueError("f error")
    return x + 1


@boost(MyBoosterParams(queue_name="queue_test_g02t", qps=0.5, max_retry_times=0))
def f2(x, y):
    time.sleep(2)
    if random.random() > 0.5:
        raise ValueError("f2 error")
    return x + y


@boost(MyBoosterParams(
    queue_name="queue_test_g03t", qps=0.5, max_retry_times=0,
    concurrent_mode=ConcurrentModeEnum.ASYNC,
))
async def aio_f3(x):
    await asyncio.sleep(3)
    if random.random() > 0.5:
        raise ValueError("f3 error")
    return x + 1


if __name__ == "__main__":
    # 启动 Web 管理界面（后台线程，不阻塞）
    start_funboost_web_manager(port=27018, care_project_name="test_project1")

    # 启动消费者
    f.multi_process_consume(4)
    f2.multi_process_consume(5)
    aio_f3.consume()

    # 发布测试消息
    for i in range(100):
        f.push(i)
        f2.push(i, i)
        aio_f3.push(i)
        time.sleep(1)

    enable_ctrl_c_quit_on_windows()
```

**运行步骤：**

```powershell
$env:PYTHONPATH = "D:\codes\your_project"
python your_script.py
# 浏览器打开 http://127.0.0.1:27018 ，登录 admin / 123456
```

---

## 7. 注意事项

### 启动相关

1. **必须先 `pip install funboost[flask]`**，否则缺少 Flask 依赖无法启动
2. **必须设置 PYTHONPATH** 指向含 `funboost_config.py` 的项目根目录，否则 Redis/Mongo 连接配置读不到
3. `start_funboost_web_manager(block=False)` 默认在后台线程启动，主线程可继续 `consume()`；若 `block=True` 则阻塞当前线程
4. 命令行方式 `python -m funboost.funweb.app` 与代码方式等价，适合独立部署 Web 服务

### 数据依赖

5. **Redis 是核心依赖**：消费者心跳、队列运维、告警、定时任务、脚本部署均依赖 Redis
6. **MongoDB 可选**：仅函数结果表和消费速率图需要；不用这两个页面可不装 Mongo
7. 消费者必须设置 `is_send_consumer_heartbeat_to_redis=True`，否则 Web 上看不到该队列的任何运行信息
8. RPC 页面要求 `is_using_rpc_mode=True`；函数结果表要求 `function_result_status_persistance_conf` 开启 `is_save_result` 和/或 `is_save_status`

### 安全与运维

9. 默认密码 `admin/123456` 仅供开发测试，生产环境务必通过 `FUNWEB_USER` / `FUNWEB_PASSWORD` 修改
10. 远程访问时在防火墙/安全组放行端口（默认 27018）；脚本部署功能支持远程 Git 更新重启
11. 定时任务：**推荐在消费脚本中启动 Scheduler**，Web 后台保持 Scheduler 暂停，避免重复调度
12. AI 运行含 `consume()` 的脚本时必须加 timeout 或 `os._exit`，否则消费循环永不退出（参见 AGENTS.md 测试规范）

### 常见错误排查

| 现象 | 可能原因 | 解决 |
|------|----------|------|
| 队列操作页无队列 | 无消费者在线或未设心跳 | 启动 `consume()` 并设 `is_send_consumer_heartbeat_to_redis=True` |
| 函数结果表为空 | Mongo 未配置或未开启持久化 | 配置 Mongo + `function_result_status_persistance_conf` |
| RPC 调用无返回值 | 未启用 RPC 模式 | 设 `is_using_rpc_mode=True` |
| 页面显示队列过多 | 未设置项目过滤 | 配置 `project_name` + `care_project_name` |
| 连接 Redis 失败 | PYTHONPATH 未设置或 config 错误 | 检查 `funboost_config.py` 中 Redis 配置 |

---

## 速查表

| 操作 | 命令/代码 |
|------|-----------|
| 安装依赖 | `pip install funboost[flask]` |
| 命令行启动 | `python -m funboost.funweb.app` |
| 代码启动 | `from funboost.funweb.app import start_funboost_web_manager` |
| 默认地址 | `http://127.0.0.1:27018` |
| 默认登录 | `admin` / `123456` |
| 心跳开关 | `BoosterParams(is_send_consumer_heartbeat_to_redis=True)` |
| 项目过滤 | `start_funboost_web_manager(care_project_name="xxx")` 或 Web 页面设置 |
| 失败重投 | 函数结果表 → 选中失败记录 → 重新运行 |
| 暂停/恢复 | 需通过 FaaS FastAPI 接口 `/funboost/pause_consume`、`/funboost/resume_consume`（funweb 页面可能不支持） |
| 调 QPS/并发 | 需重启消费者进程并修改 BoosterParams 配置 |

## 相关 Skill

- `funboost-observability` — 监控、链路追踪与告警
- `funboost-timing-jobs` — 定时/周期性任务
