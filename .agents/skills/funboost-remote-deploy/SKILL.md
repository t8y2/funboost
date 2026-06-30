---
name: funboost-remote-deploy
description: 当需要将 funboost 消费者远程部署到 Linux 服务器时使用。触发场景：fabric 部署、远程启动消费者、multi_process_consume 多进程部署。关键词：fabric, deploy, 远程部署, Linux, SSH, multi_process_consume, 自动上传。
compatibility: Python 3.7+, funboost, fabric2, paramiko（Python 3.12+ 需注意 fabric2 兼容性）
---

# Funboost 远程部署（fabric_deploy）

## 概述

Funboost 提供 **函数级** 远程部署能力：从本地 Python 代码出发，通过 SSH 自动上传项目代码到 Linux 服务器，并在远程自动导入指定函数、启动消费进程。无需在远程机器安装 git，也无需手动上传代码或登录逐台启动。

**核心原则：** 部署粒度是 **单个 @boost 函数**，不是整个 `.py` 脚本；远程通过 `python3 -c "from module import func; func.multi_process_consume(n)"` 精确启动指定函数的消费者。

## 适用场景

- 多台物理机/测试机，不方便用 k8s / CodePipeline 等运维工具
- 需要灵活指定「哪台机器跑哪个函数、开几个进程」
- 本地开发机一键把消费者部署到远程 Linux 并启动
- 与 `multi_process_consume` 结合，在远程充分利用多核 CPU

## 不适用场景

- 已有 **阿里云 CodePipeline、k8s 一键部署** 等成熟运维体系 → 优先用那些，不必用 fabric_deploy
- 远程机器是 **Windows** → 不支持，仅支持 Linux
- 远程机器 **没有 Python 基本环境** → 需先自行安装 Python 及项目依赖

---

## 1. 远程部署的核心概念

### 分布式 + 函数级部署

Funboost 是分布式函数调度框架：消息队列任务在多机间共享，任意机器上的消费者都能消费同一队列。`fabric_deploy` 在此基础上增加了 **代码级自动化**：

| 步骤 | 行为 |
|------|------|
| 1. 上传代码 | 通过 SFTP（Paramiko）将本地项目目录同步到远程 |
| 2. 设置环境 | 自动设置 `PYTHONPATH`、`-funboostmark` 进程标识 |
| 3. 杀死旧进程 | 按 mark 查找并 kill 同函数的旧消费进程 |
| 4. 启动消费 | 远程执行 `python3 -c "from ... import func; func.multi_process_consume(n)"` |

### 函数级 vs 脚本级

传统部署是上传脚本后在远程 `python worker.py`。Funboost 会根据函数所在文件自动推导模块路径，例如：

```
test_frame/test_fabric_deploy/test_deploy1.py 中的 f2
→ from test_frame.test_fabric_deploy.test_deploy1 import f2
→ f2.multi_process_consume(2)
```

因此可以 **同一文件内不同函数部署到不同机器**，或同一机器上只启动部分函数。

### 导入方式说明

`funboost/__init__.py` 中 **未导出** `fabric_deploy`（fabric2 尚未适配 Python 3.12+，顶层导入会导致高版本报错）。正确用法：

```python
# ✅ 推荐：@boost 装饰后的函数对象自带 .fabric_deploy 方法
my_task.fabric_deploy(host, port, user, password, process_num=2)

# ✅ 也可直接导入底层函数
from funboost.core.fabric_deploy_helper import fabric_deploy, kill_all_remote_tasks
fabric_deploy(my_task, host, port, user, password, process_num=2)

# ❌ 不要写（高版本 Python 可能报错或不存在）
from funboost import fabric_deploy
```

---

## 2. fabric_deploy 配置方式

### 基本 SSH 连接参数（必填）

| 参数 | 说明 |
|------|------|
| `host` | 远程 Linux 机器 IP |
| `port` | SSH 端口，通常 `22` |
| `user` | SSH 用户名 |
| `password` | SSH 密码（若设置了 `pkey_file_path` 则用私钥登录） |

### 上传控制参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `path_pattern_exluded_tuple` | `('/.git/', '/.idea/', '/dist/', '/build/')` | 排除的目录 |
| `file_suffix_tuple_exluded` | `('.pyc', '.log', '.gz')` | 排除的文件后缀 |
| `only_upload_within_the_last_modify_time` | 约 10 年（秒） | 只上传最近 N 秒内修改的文件；首次全量上传后可改小（如 `86400`）避免重复全量 |
| `file_volume_limit` | `1000000`（1MB） | 超过此大小的文件不上传 |
| `sftp_log_level` | `20`（INFO） | 上传日志级别 |
| `pkey_file_path` | `None` | SSH 私钥路径；设置后使用密钥登录，忽略密码 |

### 远程执行参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `process_num` | `1` | 远程启动的 **进程数**，内部调用 `multi_process_consume(process_num)` |
| `python_interpreter` | `'python3'` | 远程 Python 解释器；多版本环境可写绝对路径如 `/usr/bin/python3.9` |
| `extra_shell_str` | `''` | 部署前额外执行的 shell 命令（如 `export MY_VAR=1`），会自动加 `;` 拼接 |
| `invoke_runner_kwargs` | 见下表 | 传给 fabric `Connection.run()` 的参数 |

### invoke_runner_kwargs 常用项

| 键 | 默认值 | 说明 |
|----|--------|------|
| `hide` | `None` | 隐藏远程输出：`False` 不隐藏；`'out'`/`'err'` 部分隐藏；`True` 全部隐藏 |
| `pty` | `True` | **`True`**：本地脚本结束 → 远程进程也结束；**`False`**：本地关闭后远程仍继续运行（生产常驻常用） |
| `warn` | `False` | **`False`**：远程返回非零 exit code 时本机直接退出；**`True`** 仅警告 |

### 远程目录规则

源码根据 `sys.path[1]` 解析本地项目根目录名，远程路径为：

- `user == 'root'` → `/codes/{项目目录名}/`
- 其他用户 → `/home/{user}/codes/{项目目录名}/`

---

## 3. 函数级粒度部署

每个 `@boost` 装饰后的函数（Booster 对象）独立调用 `.fabric_deploy()`，互不影响：

```python
from funboost import boost, BoosterParams, BrokerEnum

@boost(BoosterParams(queue_name="queue_a", broker_kind=BrokerEnum.REDIS_ACK_ABLE))
def task_a(x):
    return x * 2

@boost(BoosterParams(queue_name="queue_b", broker_kind=BrokerEnum.REDIS_ACK_ABLE))
def task_b(x):
    return x + 1

if __name__ == "__main__":
    # 机器 1 只跑 task_a，2 进程
    task_a.fabric_deploy("192.168.1.10", 22, "deploy", "password", process_num=2)

    # 机器 2 只跑 task_b，1 进程
    task_b.fabric_deploy("192.168.1.11", 22, "deploy", "password", process_num=1)
```

框架会为每个部署生成唯一进程标识：

```
funboost_fabric_mark__{queue_name}__{func_name}
```

重新部署时会先 kill 带该 mark 的旧进程，再启动新进程。

---

## 4. multi_process_consume 与远程部署结合

`fabric_deploy` 的 `process_num` 参数会直接传给远程的 `multi_process_consume(process_num)`：

- **多进程**：每个进程独立消费，充分利用多核 CPU
- **进程内并发**：每个进程内部仍按 `BoosterParams` 的 `concurrent_mode` / `concurrent_num` / `qps` 等配置运行线程/协程

**进程数建议：** 达到最大 CPU 性能时，进程数 ≈ CPU 核数即可；每个进程内已有并发池，无需盲目开大。

远程实际执行的命令等价于：

```bash
export is_funboost_remote_run=1
export PYTHONPATH=/home/user/codes/your_project:$PYTHONPATH
cd /home/user/codes/your_project
python3 -c "from your_module import your_func; your_func.multi_process_consume(2)" \
  -funboostmark funboost_fabric_mark__your_queue__your_func
```

本地等价写法（不远程时）：

```python
my_task.multi_process_consume(2)   # 或 mp_consume(2)
```

---

## 5. 代码示例

### 完整示例：发布 + 远程部署消费

参考 `test_frame/test_fabric_deploy/test_deploy1.py`：

```python
import time
from funboost import boost, BoosterParams, BrokerEnum

@boost(BoosterParams(
    queue_name="queue_test30",
    qps=0.2,
    broker_kind=BrokerEnum.REDIS,
))
def f2(a, b):
    time.sleep(7)
    print(f"{a} + {b} = {a + b}")
    return a + b

@boost(BoosterParams(
    queue_name="queue_test31",
    qps=0.2,
    broker_kind=BrokerEnum.REDIS,
))
def f3(a, b):
    print(f"{a} - {b} = {a - b}")
    return a - b

if __name__ == "__main__":
    # 本地发布消息
    for i in range(20):
        f3.push(i, i * 2)

    # 远程部署 f3：2 进程消费，增量上传最近 1 天修改的文件
    f3.fabric_deploy(
        "106.55.244.xx", 22, "root", "your_password",
        only_upload_within_the_last_modify_time=1 * 24 * 60 * 60,
        file_volume_limit=100 * 1000,
        process_num=2,
    )
```

### 生产常驻：本地脚本退出后远程继续运行

```python
my_task.fabric_deploy(
    host="192.168.1.10",
    port=22,
    user="deploy",
    password="secret",
    process_num=4,
    invoke_runner_kwargs={
        "hide": None,
        "pty": False,   # 关键：本地退出后远程进程不退出
        "warn": True,
    },
)
```

### SSH 私钥登录

```python
my_task.fabric_deploy(
    "192.168.1.10", 22, "deploy", password="",  # 密码可留空
    pkey_file_path="/home/me/.ssh/id_rsa",
    process_num=2,
)
```

### 部署前设置远程环境变量

```python
my_task.fabric_deploy(
    "192.168.1.10", 22, "deploy", "secret",
    extra_shell_str="export FUNBOOST_CONFIG=/home/deploy/funboost_config.py",
    process_num=2,
)
```

### 杀死远程所有 fabric 部署的进程（慎用）

```python
from funboost.core.fabric_deploy_helper import kill_all_remote_tasks

kill_all_remote_tasks("192.168.1.10", 22, "deploy", "secret")
```

---

## 6. 注意事项

### 环境与依赖

| 项 | 要求 |
|----|------|
| 远程 OS | **仅 Linux**，不支持 Windows |
| 远程 Python | 需预先安装，且能 `import funboost` 及项目依赖 |
| 本地依赖 | `fabric2`、`paramiko`（funboost 远程部署内部使用） |
| Python 3.12+ | `fabric2` 尚未完全适配，`__init__.py` 不顶层导出 `fabric_deploy`；用 `.fabric_deploy()` 方法或按需安装兼容版本 |
| 消息中间件 | 远程消费者需能连接与本地相同的 Redis/RabbitMQ 等（配置 `funboost_config.py`） |

### 运行 deploy 脚本前

1. **设置 `PYTHONPATH` 为项目根目录**（框架用 `sys.path[1]` 定位上传目录和模块路径）：

   ```powershell
   $env:PYTHONPATH="D:\codes\funboost"
   python deploy_script.py
   ```

2. **从项目根目录或确保 `sys.path[1]` 指向项目根** 运行部署脚本，否则模块路径推导和上传目录会错误。

3. 远程需存在 **`funboost_config.py`**（或框架默认配置），且 broker 连接信息与本地一致。

### SSH 与安全

- 密码写在代码中有泄露风险，生产环境优先 **`pkey_file_path` 私钥** 或密钥管理
- 确保远程用户有权限写入 `/home/{user}/codes/` 或 `/codes/`
- 防火墙放行 SSH 端口及消息队列端口

### 进程生命周期

- `pty=True`（默认）：适合调试，本地 Ctrl+C 或脚本结束会连带终止远程消费
- `pty=False`：适合生产常驻；部署脚本可立即退出，消费者在远程后台持续运行
- `fabric_deploy` 在 **后台线程** 中执行上传与启动，调用后立即返回，不会阻塞主线程

### 上传优化

- 首次部署用默认 `only_upload_within_the_last_modify_time` 做全量上传
- 之后可改为 `86400`（1 天）或更小，只同步近期修改文件，加快部署
- 大文件、日志、`.git` 等已通过排除规则过滤，勿把二进制大资源放在代码目录

### 与 Celery 对比

Celery 需要在每台机器手动拉代码并启动 worker；Funboost `fabric_deploy` 可在 Python 代码层 **自动上传 + 自动按函数启动消费**，实现函数级精确部署。

---

## 速查表

| 操作 | 代码 |
|------|------|
| 远程部署单函数 | `my_task.fabric_deploy(host, port, user, password, process_num=2)` |
| 远程常驻（本地可退出） | `invoke_runner_kwargs={'pty': False}` |
| 私钥登录 | `pkey_file_path='/path/to/key'` |
| 增量上传 | `only_upload_within_the_last_modify_time=86400` |
| 本地多进程消费（对照） | `my_task.multi_process_consume(2)` |
| 杀死远程所有 fabric 进程 | `kill_all_remote_tasks(host, port, user, password)` |

## 源码位置

| 文件 | 说明 |
|------|------|
| `funboost/core/fabric_deploy_helper.py` | `fabric_deploy()`、`kill_all_remote_tasks()` 实现 |
| `funboost/core/booster.py` | Booster 对象 `.fabric_deploy()` 方法 |
| `funboost/utils/paramiko_util.py` | `ParamikoFolderUploader` SFTP 上传 |
| `test_frame/test_fabric_deploy/test_deploy1.py` | 官方示例 |

## 相关 Skill

- `using-funboost-basics` — 基础使用入门
- `funboost-broker-selection` — Broker 中间件选型
