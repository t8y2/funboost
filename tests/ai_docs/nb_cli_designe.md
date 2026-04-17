# nb_cmd 设计稿（PyPI包名: nb-cmd）

## 一句话定位

**nb_cmd = "万能接口生成器"**——你写一个 Python class，自动获得 CLI + REST API + Web UI 三种接口。不是"更好的CLI框架"，而是"超越CLI的CLI"。

---

## 目录

- [1. 为什么要做 nb_cmd](#1-为什么要做-nb_cmd)
- [2. 核心设计哲学](#2-核心设计哲学)
- [3. 四步走转化思路](#3-四步走转化思路)
- [4. API 设计——基础用法](#4-api-设计基础用法)
- [5. API 设计——高级用法](#5-api-设计高级用法)
- [6. API 设计——三种接口模式](#6-api-设计三种接口模式)
- [7. API 设计——生态集成](#7-api-设计生态集成)
- [8. 核心实现原理](#8-核心实现原理)
- [9. 和竞品的对比](#9-和竞品的对比)
- [10. 项目结构](#10-项目结构)
- [11. 依赖](#11-依赖)
- [12. 开发路线](#12-开发路线)

---

## 1. 为什么要做 nb_cmd

### 1.1 CLI框架的根本痛点

现有CLI框架（typer、fire、click、argparse）只解决了一个问题："怎么方便地定义CLI参数"。

但实际开发中，你经常遇到这种场景：

```
你写了一个CLI工具 → 产品说要加个Web页面
你写了一个CLI工具 → 运维说要通过API远程调用
你写了一个CLI工具 → 测试说要写自动化测试脚本
你写了一个CLI工具 → 老板说要能在手机上点一下按钮就执行
```

每次都是 **重写**。CLI的参数定义、API的参数定义、Web表单的参数定义——本质上是同一套东西，但你要写三遍。

### 1.2 现有框架的局限

| 框架 | 能力 | 局限 |
|------|------|------|
| argparse | 标准库 | 手写大量代码，只能做CLI |
| click | 装饰器堆叠 | 学习成本中等，只能做CLI |
| typer | 类型注解驱动 | 不支持继承/重写，只能做CLI |
| fire | 零配置 | 不支持类型校验和帮助定制，只能做CLI |

**所有现有框架都是"CLI是终点"的世界观。**

### 1.3 nb_cmd 的世界观

**"Class是中心，接口是投影"。**

```
                 CLI模式
                  ↑
业务逻辑(class) → REST API模式
                  ↓
                Web UI模式
```

你的一个class，在不同"投影面"上，自动呈现为不同形态的接口。方法签名、参数类型、docstring 作为唯一的元数据源，驱动所有接口的生成。

> 为什么没有RPC模式？因为有HTTP REST API就够了，Python调Python用requests.post调API就行。真需要异步RPC，直接用funboost。不造没必要的轮子。

### 1.4 类比

funboost 让你写一个函数，装饰器一加就能跑在40种消息队列上。

nb_cmd 让你写一个class，run一调就能跑在3种接口模式上。

---

## 2. 核心设计哲学

### 2.1 零配置：方法签名即定义

不需要学任何新的API、装饰器、配置文件。你已经会写class了，你已经会写方法了，你已经会写type hints了——那你的CLI工具（和API、Web UI）已经写完了。

### 2.2 OOP继承：部分不同只需覆写部分方法

和 oop_4steps 的理念完全一致。基础部署工具写成基类，Docker部署、K8s部署只需继承覆写特定方法，不需要全量复制代码。

### 2.3 一次定义，四处使用

方法的参数列表是唯一的元数据源。从这个元数据自动生成：
- CLI参数解析（argparse）
- REST API路由和参数校验（FastAPI/Pydantic）
- Web UI表单
- RPC服务接口

### 2.4 和现有生态的集成

nb_cmd 不从零开始造轮子，而是充分复用已有的 nb_api（API生成）、nb_log（日志+增强print）、nb_config（配置管理）等。

---

## 3. 四步走转化思路

用 oop_4steps 的思路理解 nb_cmd 的设计：

### 第0步（灵魂步骤）：脑中打草稿

你有一组业务操作（部署、回滚、查询），它们共享一些状态（数据库连接、配置信息）。

### 第1步：模块 → 类名

```python
# deploy_tool.py 模块 → class DeployTool
class DeployTool(NbCmd):
    ...
```

### 第2步：全局变量 → 实例属性

```python
class DeployTool(NbCmd):
    def __init__(self):
        self.db_conn = connect_db()  # 共享的数据库连接
        self.config = load_config()   # 共享的配置
```

### 第3步：函数 → 实例方法

```python
class DeployTool(NbCmd):
    def deploy(self, host: str, port: int = 22):
        self.db_conn.log_deploy(host)  # 直接用self.xx
        ...
```

**转化完成——你的DeployTool不仅是一个CLI工具，还自动是一个API服务和Web UI。**

---

## 4. API 设计——基础用法

### 4.1 最简示例

```python
from nb_cmd import NbCmd

class MyTool(NbCmd):
    """我的超级工具（自动变成CLI的description）"""

    def greet(self, name: str, times: int = 1):
        """向某人问好（自动变成子命令的帮助信息）"""
        for _ in range(times):
            print(f"你好, {name}!")

    def deploy(self, host: str, port: int = 22, *, verbose: bool = False):
        """部署到远程服务器"""
        if verbose:
            print(f"[详细模式] 正在部署到 {host}:{port} ...")
        print(f"部署到 {host}:{port} 完成")

    def _private_helper(self):
        """下划线开头的方法不会暴露为子命令"""
        pass

if __name__ == '__main__':
    MyTool().run()
```

### 4.2 CLI调用效果

```bash
# 查看帮助
$ python my_tool.py --help
我的超级工具

用法: my_tool.py <命令> [参数...]

命令:
  greet    向某人问好
  deploy   部署到远程服务器

选项:
  --help       显示帮助信息
  --version    显示版本信息
  --serve      以REST API模式启动
  --web        以Web UI模式启动

# 执行子命令
$ python my_tool.py greet 张三 --times 3
你好, 张三!
你好, 张三!
你好, 张三!

# 查看子命令帮助
$ python my_tool.py deploy --help
部署到远程服务器

用法: my_tool.py deploy <host> [选项]

参数:
  host          (str, 必填)

选项:
  --port        (int, 默认: 22)
  --verbose     (bool, 默认: False)

# 执行
$ python my_tool.py deploy 192.168.1.1 --port 2222 --verbose
[详细模式] 正在部署到 192.168.1.1:2222 ...
部署到 192.168.1.1:2222 完成
```

### 4.3 自动推导规则

| Python方法签名元素 | CLI映射 |
|---|---|
| 公有方法名 | 子命令名 |
| 方法的docstring | 子命令帮助文本 |
| 无默认值的参数 | 位置参数（必填） |
| 有默认值的参数 | 可选参数（`--xxx`） |
| `*` 后面的关键字参数 | 可选参数（`--xxx`） |
| `bool` 类型 | 开关参数（`--flag / --no-flag`） |
| `int` / `float` 类型 | 自动类型转换和校验 |
| `str` 类型（默认） | 字符串参数 |
| `_` 开头的方法 | 不暴露为子命令 |
| 类的 `__init__` | 不暴露 |
| 继承自 NbCmd 的方法 | 不暴露（run/before_run/after_run等） |

---

## 5. API 设计——高级用法

### 5.1 类型驱动的高级参数

```python
from nb_cmd import NbCmd
from pathlib import Path
from typing import List, Optional, Tuple
from enum import Enum

class Environment(Enum):
    DEV = "dev"
    STAGING = "staging"
    PROD = "prod"

class DeployTool(NbCmd):
    """部署工具"""

    def deploy(self,
               config: Path,                        # Path类型 → 自动检查文件是否存在
               targets: List[str],                   # List类型 → --targets a b c 多值参数
               env: Environment = Environment.DEV,   # Enum类型 → --env dev|staging|prod 自动生成选择项
               dry_run: bool = False,                 # bool类型 → --dry-run / --no-dry-run 开关
               timeout: Optional[int] = None,         # Optional → 可选参数，不传则为None
               ports: Tuple[int, int] = (8080, 8443), # Tuple → --ports 8080 8443
               ):
        """执行部署

        将应用部署到指定的目标服务器。支持多环境切换。
        """
        print(f"环境: {env.value}")
        print(f"配置: {config}")
        print(f"目标: {targets}")
        print(f"端口: {ports}")
        if dry_run:
            print("** 试运行模式，不会实际执行 **")
```

类型映射规则：

| Python类型 | CLI行为 |
|---|---|
| `str` | 普通字符串 |
| `int` | 整数校验 |
| `float` | 浮点数校验 |
| `bool` | `--flag / --no-flag` 开关 |
| `Path` | 路径，自动校验文件/目录是否存在 |
| `Enum` | 枚举，`--xxx val1\|val2\|val3`，自动生成选择项 |
| `List[T]` | 多值参数 `--xxx a b c`，每个值按T类型转换 |
| `Tuple[T1, T2]` | 固定数量多值参数 |
| `Optional[T]` | 可选参数，不传则为None |
| `typing.IO` | 文件对象（自动打开文件） |

### 5.2 继承覆写——OOP的核心优势

```python
class BaseDeploy(NbCmd):
    """基础部署工具"""

    def deploy(self, host: str, port: int = 22):
        """部署"""
        self._connect(host, port)
        self._upload()
        self._restart()
        self._verify()

    def _connect(self, host, port):
        print(f"SSH连接 {host}:{port}")

    def _upload(self):
        print("SFTP上传文件")

    def _restart(self):
        """子类覆写此方法以自定义重启逻辑"""
        print("systemctl restart app")

    def _verify(self):
        print("验证服务状态: OK")


class DockerDeploy(BaseDeploy):
    """Docker部署——只需覆写_restart"""

    def _restart(self):
        print("docker-compose down && docker-compose up -d")


class K8sDeploy(BaseDeploy):
    """K8s部署——只需覆写_restart和_upload"""

    def _upload(self):
        print("kubectl apply -f deployment.yaml")

    def _restart(self):
        print("kubectl rollout restart deployment/app")


# 使用不同的部署方式
if __name__ == '__main__':
    import sys
    # 根据环境变量或参数选择部署方式
    deploy_type = sys.argv.pop(1) if len(sys.argv) > 1 else "base"
    deployers = {"base": BaseDeploy, "docker": DockerDeploy, "k8s": K8sDeploy}
    deployers[deploy_type]().run()
```

### 5.3 多层级子命令（嵌套命令组）

类似 `git remote add`、`docker container ls` 这种多层级子命令，通过**内部类**实现：

```python
from nb_cmd import NbCmd


class GitRemote(NbCmd):
    """远程仓库管理"""

    def add(self, name: str, url: str):
        """添加远程仓库"""
        print(f"git remote add {name} {url}")

    def remove(self, name: str):
        """删除远程仓库"""
        print(f"git remote remove {name}")

    def list(self):
        """列出所有远程仓库"""
        print("origin  https://github.com/xxx/xxx.git (fetch)")


class GitBranch(NbCmd):
    """分支管理"""

    def create(self, name: str, *, from_branch: str = "main"):
        """创建分支"""
        print(f"git checkout -b {name} {from_branch}")

    def delete(self, name: str, *, force: bool = False):
        """删除分支"""
        flag = "-D" if force else "-d"
        print(f"git branch {flag} {name}")

    def list(self):
        """列出所有分支"""
        print("* main")
        print("  develop")
        print("  feature/login")


class GitTool(NbCmd):
    """简易Git工具"""

    sub_commands = {
        'remote': GitRemote,
        'branch': GitBranch,
    }

    def status(self):
        """查看状态"""
        print("当前分支: main")

    def commit(self, message: str, *, all: bool = False):
        """提交"""
        if all:
            print("git add -A")
        print(f"git commit -m '{message}'")


if __name__ == '__main__':
    GitTool().run()
```

CLI调用效果：

```bash
# 一级命令
$ python git_tool.py status
当前分支: main

$ python git_tool.py commit "fix bug" --all

# 二级命令（通过sub_commands注册）
$ python git_tool.py remote add origin https://github.com/xxx.git
git remote add origin https://github.com/xxx.git

$ python git_tool.py remote list
origin  https://github.com/xxx/xxx.git (fetch)

$ python git_tool.py branch create feature/login --from-branch develop
git checkout -b feature/login develop

$ python git_tool.py branch delete feature/login --force
git branch -D feature/login

# 查看子命令组帮助
$ python git_tool.py remote --help
远程仓库管理

命令:
  add      添加远程仓库
  remove   删除远程仓库
  list     列出所有远程仓库

$ python git_tool.py --help
简易Git工具

命令:
  status     查看状态
  commit     提交
  remote     远程仓库管理（子命令组）
  branch     分支管理（子命令组）
```

**设计优势：**
- 每个子命令组都是独立的类，符合PEP8命名规范（大驼峰）
- 不用内部类嵌套，代码结构扁平清晰
- 子命令组的类可以被单独复用和测试
- `sub_commands` 字典的key就是CLI中的子命令组名称

**实现原理：** `_discover_commands()` 中检测 `sub_commands` 类变量，对其中的每个NbCmd子类递归构建 argparse 的 subparser。

多层级还可以继续嵌套：

```python
class ServerConfig(NbCmd):
    """配置管理"""
    def show(self):
        """显示配置"""
        print("server.config.show")

    def set(self, key: str, value: str):
        """设置配置"""
        print(f"设置 {key} = {value}")


class ServerGroup(NbCmd):
    """服务器管理"""
    sub_commands = {
        'config': ServerConfig,
    }

    def restart(self):
        """重启服务器"""
        print("重启中...")


class MyTool(NbCmd):
    """运维工具"""
    sub_commands = {
        'server': ServerGroup,
    }
```

```bash
$ python my_tool.py server config show
$ python my_tool.py server config set max_connections 100
$ python my_tool.py server restart
```

### 5.4 带状态的CLI（__init__参数 → 全局选项）

```python
class DbTool(NbCmd):
    """数据库管理工具"""

    def __init__(self, db_url: str = "sqlite:///default.db", verbose: bool = False):
        """
        __init__的参数自动变成全局选项（所有子命令共享）。
        """
        super().__init__()
        self.db_url = db_url
        self.verbose = verbose
        self.conn = None  # 延迟连接

    def before_run(self):
        """所有子命令执行前的钩子"""
        self.conn = connect_db(self.db_url)
        if self.verbose:
            print(f"已连接数据库: {self.db_url}")

    def after_run(self):
        """所有子命令执行后的钩子"""
        if self.conn:
            self.conn.close()

    def query(self, sql: str):
        """执行SQL查询"""
        result = self.conn.execute(sql)
        self.table(result)  # 内置表格输出

    def migrate(self, version: str = "latest"):
        """数据库迁移"""
        print(f"迁移到版本: {version}")
```

```bash
# 全局选项 + 子命令
$ python db_tool.py --db-url "mysql://localhost/mydb" --verbose query "SELECT * FROM users"
已连接数据库: mysql://localhost/mydb
┌──────┬──────┐
│ name │ age  │
├──────┼──────┤
│ 张三 │ 25   │
│ 李四 │ 30   │
└──────┴──────┘
```

### 5.5 返回值处理

```python
class DataTool(NbCmd):

    def query(self, table: str) -> list:
        """查询数据"""
        data = [{"name": "张三", "age": 25}, {"name": "李四", "age": 30}]
        return data  # 返回值自动格式化输出

    def count(self, table: str) -> int:
        """统计行数"""
        return 42  # 返回值自动打印
```

**返回值自动处理规则：**

| 返回类型 | CLI显示 | API响应 |
|---|---|---|
| `None` | 不输出 | `{"status": "ok"}` |
| `str` | 直接print | `{"result": "xxx"}` |
| `int`/`float` | 直接print | `{"result": 42}` |
| `dict` | JSON格式化输出 | 直接作为响应体 |
| `list[dict]` | 表格输出 | 直接作为响应体数组 |
| `list[str]` | 每行一个输出 | `{"result": [...]}` |
| `Path` | 输出路径 | 返回文件下载 |

### 5.6 进度条和表格

```python
class DataTool(NbCmd):

    def process(self, input_file: Path, output_file: Path):
        """处理大数据文件"""
        data = self.read_lines(input_file)
        results = []
        for item in self.progress(data, desc="处理中"):  # 内置进度条
            results.append(transform(item))
        self.write_lines(output_file, results)
        print(f"处理完成: {len(results)} 条")

    def show_users(self):
        """展示用户列表"""
        data = [
            {"名字": "张三", "年龄": 25, "城市": "北京"},
            {"名字": "李四", "年龄": 30, "城市": "上海"},
        ]
        self.table(data)  # 内置表格输出

    def show_status(self):
        """展示系统状态"""
        self.kv({  # 键值对输出
            "CPU": "45%",
            "内存": "2.3GB / 8GB",
            "磁盘": "120GB / 500GB",
            "运行时间": "3天12小时",
        })
```

```bash
$ python data_tool.py process ./input.csv ./output.csv
处理中 ████████████████████████████████ 100% 10000/10000  [00:05<00:00]
处理完成: 10000 条

$ python data_tool.py show-users
┌──────┬──────┬──────┐
│ 名字 │ 年龄 │ 城市 │
├──────┼──────┤──────┤
│ 张三 │ 25   │ 北京 │
│ 李四 │ 30   │ 上海 │
└──────┴──────┴──────┘

$ python data_tool.py show-status
CPU:       45%
内存:      2.3GB / 8GB
磁盘:      120GB / 500GB
运行时间:  3天12小时
```

### 5.7 方法命名转换

Python方法名中的下划线自动转换为CLI中的短横线：

```python
class MyTool(NbCmd):
    def create_user(self, name: str):     # CLI: create-user
        ...
    def delete_all_data(self):            # CLI: delete-all-data
        ...
    def run_migration(self, version: str): # CLI: run-migration
        ...
```

### 5.8 参数校验和自定义校验

```python
from nb_cmd import NbCmd, validate

class MyTool(NbCmd):

    @validate(port=lambda x: 1 <= x <= 65535, host=lambda x: '.' in x)
    def deploy(self, host: str, port: int = 22):
        """部署"""
        print(f"部署到 {host}:{port}")
```

```bash
$ python my_tool.py deploy localhost --port 99999
错误: port 必须满足约束条件 (当前值: 99999)

$ python my_tool.py deploy invalid_host
错误: host 必须满足约束条件 (当前值: invalid_host)
```

### 5.9 参数别名

```python
class MyTool(NbCmd):

    def deploy(self, host: str, port: int = 22, verbose: bool = False):
        """部署"""
        ...

    class Meta:
        aliases = {
            'deploy.host': ['-h', '--server'],
            'deploy.port': ['-p'],
            'deploy.verbose': ['-v'],
        }
```

```bash
$ python my_tool.py deploy -h 192.168.1.1 -p 2222 -v
```

---

## 6. API 设计——三种接口模式

### 6.1 CLI模式（默认）

就是上面展示的标准CLI调用方式。这是默认模式。

```bash
$ python tool.py <command> [args...]
```

### 6.2 REST API模式 `--serve`

```bash
$ python tool.py --serve --port 8080
```

自动生成FastAPI应用：

```
启动API服务器:
  - POST /greet         → 对应 greet() 方法
  - POST /deploy        → 对应 deploy() 方法
  - GET  /help          → 返回所有命令的帮助信息
  - GET  /help/{cmd}    → 返回指定命令的帮助信息
  - GET  /docs          → 自动生成的 Swagger UI

服务运行在 http://0.0.0.0:8080
```

调用示例：

```bash
$ curl -X POST http://localhost:8080/deploy \
    -H "Content-Type: application/json" \
    -d '{"host": "192.168.1.1", "port": 2222, "verbose": true}'

{
    "status": "success",
    "result": {"status": "deployed"},
    "duration_ms": 1523
}
```

**实现原理：** 复用 nb_api 的路由自动生成机制。遍历class的所有公有方法，用 `inspect.signature` 获取参数签名，自动创建FastAPI路由和Pydantic model。

### 6.3 Web UI模式 `--web`

```bash
$ python tool.py --web --port 8080
```

自动生成Web页面，浏览器打开 `http://localhost:8080` 后看到：

```
┌───────────────────────────────────────────────────────────────────┐
│  MyTool v1.0.0 - 我的超级工具                                      │
├─────────────────────────────┬─────────────────────────────────────┤
│                             │                                     │
│  🖥️ 命令行输入              │  📋 实时控制台输出                   │
│  $ deploy 192.168.1.1 ▏     │                                     │
│  (支持Tab补全和↑↓历史)       │  > 2026-04-17 15:30:22              │
│                             │  > 部署到 192.168.1.1:22 完成       │
│  ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─    │  >                                  │
│                             │  > 2026-04-17 15:30:45              │
│  💡 参数表单(可折叠,辅助填参) │  > 你好, 张三!                      │
│  ▶ deploy 部署到远程服务器   │  > 你好, 张三!                      │
│    host: [192.168.1.1]      │                                     │
│    port: [22]               │  ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─            │
│    env:  [dev ▼]            │                                     │
│    verbose: ☐               │  📜 命令历史                         │
│    [生成命令] [直接执行]      │  1. deploy 192.168.1.1 --port 22   │
│                             │  2. greet 张三 --times 3            │
│  ▶ greet 向某人问好(折叠)    │  3. deploy 10.0.0.1 --env prod     │
│                             │  (点击历史可重新执行)                 │
│                             │                                     │
├─────────────────────────────┴─────────────────────────────────────┤
│  状态: 就绪  |  最后执行: deploy 15:30:22  |  执行次数: 4          │
└───────────────────────────────────────────────────────────────────┘
```

**设计思路：** "命令行输入 + 辅助表单 + 实时控制台"三合一，兼顾开发者和非技术人员。

**左上 - 命令行输入框（主要交互方式）：**
- 开发者直接敲命令，和终端体验一致
- 支持Tab自动补全子命令和参数名
- 支持↑↓翻阅历史命令
- 回车直接执行

**左下 - 参数表单（辅助交互方式，可折叠）：**
- 不熟悉CLI的用户可以用表单填参数
- 参数类型自动映射为HTML控件（见下表）
- 点击[生成命令]：把表单内容转成命令字符串，填入上方命令行输入框
- 点击[直接执行]：跳过命令行输入，直接执行
- 默认折叠，不占空间

**右上 - 实时控制台输出：**
- stdout/stderr通过WebSocket实时推送
- 自动滚动到底部
- 和pyqt5demo的右侧控制台一样的体验

**右下 - 命令历史：**
- 自动记录所有执行过的命令
- 点击历史条目可以直接重新执行
- 持久化到浏览器localStorage

**为什么不是纯表单？**

纯表单式的Web UI效率低——一个一个填参数、点按钮，比直接敲命令还慢。
命令行输入框为主、表单为辅的设计，让开发者和非技术人员都能高效使用。

| Python类型 | Web UI表单控件 |
|---|---|
| `str` | `<input type="text">` |
| `int` | `<input type="number">` |
| `float` | `<input type="number" step="0.01">` |
| `bool` | `<input type="checkbox">` |
| `Path` | `<input type="file">` + 路径输入 |
| `Enum` | `<select>` 下拉选择 |
| `List[str]` | 可动态增减的多行输入 |
| `Optional[T]` | 可选输入（带"启用"复选框） |

### 6.4 模式切换——不改一行业务代码

```bash
# 开发阶段：CLI
$ python tool.py deploy 192.168.1.1

# 要变成服务：一个参数
$ python tool.py --serve --port 8080

# 给非技术人员用：一个参数
$ python tool.py --web --port 8080
```

**就像 funboost 的 @boost 一样——不改一行业务代码，切换运行模式。**

> 如果需要远程调用，直接用 REST API 模式的 HTTP 接口即可。如果需要异步队列式RPC，那是 funboost 的活。

---

## 7. API 设计——生态集成

### 7.1 Meta 配置类

```python
class MyTool(NbCmd):
    class Meta:
        name = "mytool"                     # CLI名称（默认用类名的snake_case）
        version = "1.0.0"                   # 版本号
        description = "我的超级工具"         # 覆盖类的docstring
        
        # nb_log 集成
        use_nb_log = True                   # 见下方说明
        log_level = "DEBUG"                 # 日志级别（仅use_nb_log=True时生效）
        log_file = "mytool.log"             # 日志文件（仅use_nb_log=True时生效）

        # 配置持久化（类似pyqt5demo的控件值保存/恢复）
        auto_save_last_args = True          # 自动保存上一次执行的参数
        config_file = "~/.mytool.ini"       # 配置文件路径
        
        # serve模式配置
        serve_host = "0.0.0.0"              # API服务绑定地址
        serve_port = 8080                   # API服务端口
        serve_workers = 4                   # API服务工作进程数
        
        # web模式配置
        web_title = "我的工具"              # Web页面标题
        web_theme = "dark"                  # Web页面主题
        
        # 参数别名
        aliases = {
            'deploy.host': ['-h', '--server'],
            'deploy.port': ['-p'],
        }
```

**`use_nb_log` 的效果对比：**

| 配置 | print行为 | self.logger | 日志文件 | 控制台颜色 |
|------|----------|-------------|---------|-----------|
| `use_nb_log = False`（默认） | 原生print，无增强 | 标准logging.getLogger | 无 | 无 |
| `use_nb_log = True` | 自动增强：print输出自带时间戳、文件名、行号（nb_print效果） | nb_log增强版logger，自带彩色控制台handler | 自动写入log_file | 有（nb_log彩色） |

简单来说：
- **False**：nb_cmd零外部依赖，纯标准库运行，适合轻量脚本
- **True**：自动获得nb_log全套能力（彩色日志 + 增强print + 文件日志），适合正式项目

```bash
# use_nb_log = False 时的输出
$ python tool.py deploy 192.168.1.1
部署到 192.168.1.1:22 完成

# use_nb_log = True 时的输出
$ python tool.py deploy 192.168.1.1
2026-04-17 15:30:22  "tool.py:15" -deploy-[print]-  部署到 192.168.1.1:22 完成
```

### 7.2 生命周期钩子

```python
class MyTool(NbCmd):

    def before_run(self):
        """所有子命令执行前的钩子"""
        # 初始化数据库连接、加载配置等
        self.logger.info("工具启动")

    def after_run(self):
        """所有子命令执行后的钩子"""
        # 关闭连接、清理资源等
        self.logger.info("工具结束")

    def on_error(self, command: str, error: Exception):
        """子命令执行出错时的钩子"""
        self.logger.error(f"命令 {command} 执行失败: {error}")
        # 可以选择是否重新抛出异常
```

### 7.3 内置工具方法

NbCmd 基类提供以下工具方法供子类使用：

```python
class NbCmd:
    # 输出工具
    def table(self, data: list, headers: list = None): ...     # 表格输出
    def kv(self, data: dict): ...                               # 键值对输出
    def tree(self, data: dict): ...                             # 树形输出
    def json_print(self, data): ...                             # JSON美化输出
    
    # 进度工具
    def progress(self, iterable, desc=None, total=None): ...   # 进度条
    
    # 交互工具
    def confirm(self, message: str) -> bool: ...                # 确认提示
    def prompt(self, message: str, default=None) -> str: ...   # 输入提示
    def select(self, message: str, choices: list) -> str: ...  # 选择提示
    
    # 彩色输出
    def success(self, msg): ...    # 绿色
    def warning(self, msg): ...    # 黄色
    def error(self, msg): ...      # 红色
    def info(self, msg): ...       # 蓝色
```

### 7.4 与 auto_run_on_remote 集成

```python
class DeployTool(NbCmd):
    
    def deploy(self, host: str):
        """部署"""
        print(f"部署到 {host}")

    def deploy_remote(self, host: str):
        """在远程服务器上执行部署（自动上传代码并远程执行）"""
        self.run_on_remote(
            host="deploy-server",
            command=f"python tool.py deploy {host}"
        )
```

---

## 8. 核心实现原理

### 8.1 主入口 `run()` 方法

```python
import argparse
import inspect
import sys
from typing import get_type_hints

class NbCmd:
    def run(self, args=None):
        """主入口"""
        # 1. 检查全局模式参数
        if '--serve' in (args or sys.argv):
            return self._start_api_server(args)
        if '--web' in (args or sys.argv):
            return self._start_web_server(args)
        
        # 2. CLI模式
        commands = self._discover_commands()
        parser = self._build_parser(commands)
        parsed = parser.parse_args(args)
        
        if not hasattr(parsed, 'command') or parsed.command is None:
            parser.print_help()
            return
        
        # 3. 执行命令
        method = getattr(self, parsed.command.replace('-', '_'))
        kwargs = self._extract_kwargs(method, parsed)
        
        self.before_run()
        try:
            result = method(**kwargs)
            self._handle_result(result)
        except Exception as e:
            self.on_error(parsed.command, e)
            raise
        finally:
            self.after_run()
```

### 8.2 命令发现 `_discover_commands()`

```python
def _discover_commands(self):
    """通过反射发现所有公有方法，以及 sub_commands 类变量中注册的子命令组"""
    commands = {}
    
    base_methods = set(dir(NbCmd))
    
    # 1. 发现普通方法（子命令）
    for name in dir(self):
        if name.startswith('_'):
            continue
        if name in base_methods:
            continue
        if name == 'sub_commands':
            continue
        
        attr = getattr(self, name)
        if not callable(attr) or not inspect.ismethod(attr):
            continue
            
        sig = inspect.signature(attr)
        doc = inspect.getdoc(attr) or ""
        
        commands[name] = {
            'method': attr,
            'signature': sig,
            'doc': doc.split('\n')[0],
            'full_doc': doc,
            'is_group': False,
        }
    
    # 2. 发现子命令组（通过 sub_commands 类变量注册）
    sub_cmds = getattr(self.__class__, 'sub_commands', {})
    for group_name, group_cls in sub_cmds.items():
        if inspect.isclass(group_cls) and issubclass(group_cls, NbCmd):
            commands[group_name] = {
                'cls': group_cls,
                'doc': (inspect.getdoc(group_cls) or "").split('\n')[0],
                'is_group': True,
            }
    
    return commands
```

### 8.3 参数解析器构建 `_build_parser()`

```python
def _build_parser(self, commands):
    """根据方法签名自动构建argparse"""
    parser = argparse.ArgumentParser(
        description=inspect.getdoc(self) or self.__class__.__name__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument('--version', action='version', version=getattr(self.Meta, 'version', '0.0.1'))
    parser.add_argument('--serve', action='store_true', help='以REST API模式启动')
    parser.add_argument('--web', action='store_true', help='以Web UI模式启动')
    parser.add_argument('--port', type=int, default=8080, help='服务端口（用于 --serve/--web）')
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    for cmd_name, cmd_info in commands.items():
        cli_name = cmd_name.replace('_', '-')  # snake_case → kebab-case
        sub = subparsers.add_parser(cli_name, help=cmd_info['doc'],
                                     description=cmd_info['full_doc'])
        
        sig = cmd_info['signature']
        type_hints = get_type_hints(cmd_info['method'])
        
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue
            
            param_type = type_hints.get(param_name, str)
            has_default = param.default is not inspect.Parameter.empty
            is_keyword_only = param.kind == inspect.Parameter.KEYWORD_ONLY
            
            if param_type is bool:
                # bool类型 → 开关参数
                sub.add_argument(
                    f'--{param_name.replace("_", "-")}',
                    action='store_true' if not (has_default and param.default) else 'store_false',
                    default=param.default if has_default else False,
                    help=f'(bool, 默认: {param.default if has_default else False})'
                )
            elif has_default or is_keyword_only:
                # 有默认值 → 可选参数
                sub.add_argument(
                    f'--{param_name.replace("_", "-")}',
                    type=self._get_argparse_type(param_type),
                    default=param.default if has_default else None,
                    nargs=self._get_nargs(param_type),
                    choices=self._get_choices(param_type),
                    help=f'({param_type.__name__ if hasattr(param_type, "__name__") else str(param_type)}, '
                         f'默认: {param.default if has_default else "None"})'
                )
            else:
                # 无默认值 → 位置参数
                sub.add_argument(
                    param_name,
                    type=self._get_argparse_type(param_type),
                    nargs=self._get_nargs(param_type),
                    help=f'({param_type.__name__ if hasattr(param_type, "__name__") else str(param_type)}, 必填)'
                )
    
    return parser
```

### 8.4 API服务器生成 `_start_api_server()`

```python
def _start_api_server(self, args):
    """自动生成FastAPI应用并启动"""
    try:
        from fastapi import FastAPI
        from pydantic import create_model
        import uvicorn
    except ImportError:
        print("REST API模式需要安装 fastapi 和 uvicorn: pip install fastapi uvicorn")
        return
    
    app = FastAPI(
        title=getattr(self.Meta, 'name', self.__class__.__name__),
        description=inspect.getdoc(self) or '',
        version=getattr(self.Meta, 'version', '0.0.1'),
    )
    
    commands = self._discover_commands()
    
    for cmd_name, cmd_info in commands.items():
        sig = cmd_info['signature']
        type_hints = get_type_hints(cmd_info['method'])
        
        # 动态创建Pydantic model
        fields = {}
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue
            param_type = type_hints.get(param_name, str)
            has_default = param.default is not inspect.Parameter.empty
            if has_default:
                fields[param_name] = (param_type, param.default)
            else:
                fields[param_name] = (param_type, ...)
        
        RequestModel = create_model(f'{cmd_name}_request', **fields)
        method = cmd_info['method']
        
        # 创建路由
        @app.post(f'/{cmd_name.replace("_", "-")}', summary=cmd_info['doc'])
        async def endpoint(request: RequestModel, _method=method):
            kwargs = request.dict()
            result = _method(**kwargs)
            return {"status": "success", "result": result}
    
    # 帮助接口
    @app.get('/help')
    async def help_all():
        return {name: info['doc'] for name, info in commands.items()}
    
    port = getattr(self.Meta, 'serve_port', 8080)
    # 从命令行参数中提取port
    if args and '--port' in args:
        idx = args.index('--port')
        if idx + 1 < len(args):
            port = int(args[idx + 1])
    
    print(f"API服务启动在 http://0.0.0.0:{port}")
    print(f"Swagger文档: http://0.0.0.0:{port}/docs")
    uvicorn.run(app, host="0.0.0.0", port=port)
```

### 8.5 Web UI 生成 `_start_web_server()`

```python
def _start_web_server(self, args):
    """自动生成Web UI并启动"""
    try:
        from fastapi import FastAPI
        from fastapi.responses import HTMLResponse
        from fastapi.websockets import WebSocket
        import uvicorn
    except ImportError:
        print("Web UI模式需要安装 fastapi 和 uvicorn: pip install fastapi uvicorn")
        return
    
    app = FastAPI()
    commands = self._discover_commands()
    
    # 生成HTML页面
    html = self._generate_web_ui_html(commands)
    
    @app.get('/', response_class=HTMLResponse)
    async def index():
        return html
    
    # WebSocket用于实时输出
    @app.websocket('/ws')
    async def websocket_endpoint(websocket: WebSocket):
        await websocket.accept()
        # 重定向stdout到websocket
        ...
    
    # 每个命令的执行接口
    for cmd_name, cmd_info in commands.items():
        method = cmd_info['method']
        
        @app.post(f'/api/{cmd_name}')
        async def execute(request: dict, _method=method):
            result = _method(**request)
            return {"result": result}
    
    port = 8080
    print(f"Web UI启动在 http://0.0.0.0:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)

def _generate_web_ui_html(self, commands):
    """根据命令列表生成HTML页面"""
    # 生成左侧命令表单 + 右侧控制台的HTML
    # 类似pyqt5demo的"左界面右控制台"布局
    # 每个方法的参数自动映射为HTML表单控件
    ...
```

### 8.6 类型辅助方法

```python
def _get_argparse_type(self, python_type):
    """Python类型 → argparse类型转换函数"""
    import enum
    from pathlib import Path as PathType
    
    origin = getattr(python_type, '__origin__', None)
    
    if python_type is bool:
        return None  # bool使用store_true/store_false
    if python_type in (int, float, str):
        return python_type
    if python_type is PathType or python_type is Path:
        return PathType
    if isinstance(python_type, type) and issubclass(python_type, enum.Enum):
        return lambda x: python_type(x)
    if origin is list:
        args = python_type.__args__
        return args[0] if args else str
    return str

def _get_nargs(self, python_type):
    """Python类型 → argparse nargs"""
    origin = getattr(python_type, '__origin__', None)
    if origin is list:
        return '+'
    if origin is tuple:
        return len(python_type.__args__)
    return None

def _get_choices(self, python_type):
    """Python类型 → argparse choices"""
    import enum
    if isinstance(python_type, type) and issubclass(python_type, enum.Enum):
        return [e.value for e in python_type]
    return None
```

---

## 9. 和竞品的对比

### 9.1 功能对比表

| 功能 | argparse | click | typer | fire | **nb_cmd** |
|------|----------|-------|-------|------|----------|
| 零配置 | ✗ | ✗ | 部分 | ✓ | **✓** |
| 类型驱动 | 手动 | 手动 | ✓ | ✗ | **✓** |
| 自动帮助 | 基础 | ✓ | ✓ | 基础 | **✓** |
| 继承/覆写 | ✗ | ✗ | ✗ | 有限 | **✓** |
| 生成REST API | ✗ | ✗ | ✗ | ✗ | **✓** |
| 生成Web UI | ✗ | ✗ | ✗ | ✗ | **✓** |
| 进度条/表格 | ✗ | ✓ | ✓(rich) | ✗ | **✓** |
| 参数持久化 | ✗ | ✗ | ✗ | ✗ | **✓** |
| 生命周期钩子 | ✗ | 有限 | ✗ | ✗ | **✓** |
| Enum支持 | 手动 | ✓ | ✓ | ✗ | **✓** |
| List/Tuple支持 | 手动 | ✓ | ✓ | 有限 | **✓** |
| 交互式确认 | ✗ | ✓ | ✓ | ✗ | **✓** |

### 9.2 代码量对比

同样实现一个"部署+回滚+查询"的工具：

**argparse: ~80行**
```python
parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers()
deploy_parser = subparsers.add_parser('deploy')
deploy_parser.add_argument('host')
deploy_parser.add_argument('--port', type=int, default=22)
# ... 大量重复代码
```

**click: ~40行**
```python
@click.group()
def cli(): pass

@cli.command()
@click.argument('host')
@click.option('--port', default=22)
def deploy(host, port):
    ...
# 每个命令都要堆装饰器
```

**typer: ~25行**
```python
app = typer.Typer()

@app.command()
def deploy(host: str, port: int = 22):
    ...
# 好多了，但还是需要装饰器
```

**fire: ~15行**
```python
class Tool:
    def deploy(self, host, port=22):
        ...
fire.Fire(Tool)
# 最简，但没有类型校验和帮助定制
```

**nb_cmd: ~15行 + 自动获得API/Web UI**
```python
class Tool(NbCmd):
    def deploy(self, host: str, port: int = 22):
        ...
Tool().run()
# 和fire一样简，但有类型校验 + 帮助定制 + 三种接口模式 + OOP继承覆写 + 多层级子命令
```

### 9.3 核心差异总结

| 维度 | typer/fire | nb_cmd |
|------|-----------|---------|
| **世界观** | CLI是终点 | Class是中心，接口是投影 |
| **扩展方式** | 无（火fire）或有限（typer） | OOP继承覆写 |
| **接口数量** | 1种（CLI） | 3种（CLI/API/Web） |
| **代码复用** | 每种接口写一遍 | 写一次，到处使用 |

---

## 10. 项目结构

```
nb_cmd/
├── __init__.py               # 核心入口，NbCmd基类
├── core/
│   ├── __init__.py
│   ├── discovery.py           # 命令发现（反射）
│   ├── parser.py              # argparse构建
│   ├── type_utils.py          # 类型映射工具
│   └── result_handler.py      # 返回值处理
├── modes/
│   ├── __init__.py
│   ├── cli_mode.py            # CLI模式
│   ├── api_mode.py            # REST API模式（依赖fastapi）
│   └── web_mode.py            # Web UI模式（依赖fastapi + jinja2）
├── ui/
│   ├── __init__.py
│   ├── table.py               # 表格输出（CLI模式）
│   ├── progress.py            # 进度条（CLI模式）
│   ├── colors.py              # 彩色输出（CLI模式）
│   └── static/                # **前端预构建产物（npm run build生成，随包发布）**
│       ├── index.html
│       ├── assets/
│       │   ├── index-xxxxx.js
│       │   └── index-xxxxx.css
│       └── favicon.ico
├── web_frontend/              # **前端源码（仅开发者需要，不随包发布）**
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── index.html
│   ├── src/
│   │   ├── main.ts
│   │   ├── App.vue
│   │   ├── components/
│   │   │   ├── CommandInput.vue      # 命令行输入框组件
│   │   │   ├── ParamForm.vue         # 参数表单组件（可折叠）
│   │   │   ├── ConsoleOutput.vue     # 实时控制台输出组件
│   │   │   ├── CommandHistory.vue    # 命令历史组件
│   │   │   └── StatusBar.vue         # 底部状态栏组件
│   │   ├── composables/
│   │   │   ├── useWebSocket.ts       # WebSocket连接管理
│   │   │   └── useCommandHistory.ts  # 命令历史（localStorage持久化）
│   │   └── types/
│   │       └── command.ts            # 命令/参数类型定义
│   └── build_to_package.sh    # 构建并复制到 ui/static/ 的脚本
├── utils/
│   ├── __init__.py
│   ├── config.py              # 参数持久化
│   └── validators.py          # 参数校验
├── README.md
├── setup.py
└── tests/
    ├── test_basic.py
    ├── test_types.py
    ├── test_inherit.py
    ├── test_api_mode.py
    └── test_web_mode.py
```

---

## 11. 依赖

### 核心依赖（必须）

```
无（纯标准库: argparse + inspect + typing）
```

### 可选依赖（按模式）

```
# REST API模式
fastapi>=0.68.0
uvicorn>=0.15.0
pydantic>=1.8.0

# Web UI模式（前端已预构建，用户无需安装Node.js）
fastapi>=0.68.0
uvicorn>=0.15.0
websockets>=10.0

# 增强输出
rich>=10.0.0  # 可选，用于更好的表格和进度条

# nb生态集成（可选）
nb_log    # 已包含nb_print的增强print功能
nb_config
```

**核心设计原则：CLI模式零外部依赖，其他模式按需安装。**

### 前端技术栈（仅作者开发时需要，用户无感知）

```
Vue 3 + Element Plus + Vite + TypeScript
```

**构建流程（仅作者执行）：**

```bash
cd nb_cmd/web_frontend/
npm install
npm run build
# vite自动将构建产物输出到 ../ui/static/
```

**用户使用时的体验：**

```bash
pip install nb-cmd
python tool.py --web --port 8080
# 直接启动Web UI，无需Node.js，前端文件已打包在Python包中
```

**关键配置 `vite.config.ts`：**

```typescript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import ElementPlus from 'unplugin-element-plus/vite'
import path from 'path'

export default defineConfig({
  plugins: [vue(), ElementPlus({})],
  build: {
    // 构建产物输出到Python包的static目录
    outDir: path.resolve(__dirname, '../ui/static'),
    emptyOutDir: true,
    // 生成单文件，减少HTTP请求
    rollupOptions: {
      output: {
        manualChunks: undefined,
      },
    },
  },
  base: './',  // 使用相对路径，适配任意部署路径
})
```

**Python端serve静态文件：**

```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import importlib.resources

app = FastAPI()

# 获取包内static目录路径
static_dir = importlib.resources.files('nb_cmd') / 'ui' / 'static'
app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
```

**`setup.py` / `pyproject.toml` 中包含静态文件：**

```toml
[tool.setuptools.package-data]
nb_cmd = ["ui/static/**/*"]
```

**前端与后端通信：**

```
前端（Vue3）                     后端（FastAPI）
    │                                │
    ├── POST /api/{command}  ────────┤  执行命令
    │                                │
    ├── WebSocket /ws  ──────────────┤  实时控制台输出推送
    │                                │
    ├── GET /api/commands  ──────────┤  获取所有命令和参数定义
    │                                │
    └── GET /api/help/{cmd}  ────────┤  获取命令帮助信息
```

**为什么用 Vue3 + Element Plus？**

1. **Element Plus** 提供了现成的表单组件（Input、Select、Switch、InputNumber等），参数类型到表单控件的映射开箱即用
2. **Vue3** 的响应式系统天然适合实时控制台输出和命令历史的状态管理
3. **Vite** 构建速度极快，开发体验好
4. **构建产物体积小**——gzip后整个前端通常 < 500KB

---

## 12. 开发路线

### 阶段1：MVP（核心CLI功能）

- [x] NbCmd 基类
- [x] 命令发现（反射）
- [x] 参数自动推导（inspect.signature）
- [x] 基础类型支持（str/int/float/bool）
- [x] 帮助信息自动生成
- [x] 方法名 snake_case → kebab-case 转换
- [x] before_run / after_run 钩子
### 阶段2：高级类型和输出

- [ ] Enum / List / Tuple / Optional / Path 类型支持
- [ ] 表格输出 table()
- [ ] 进度条 progress()
- [ ] 彩色输出 success/warning/error/info
- [ ] 键值对输出 kv()
- [ ] 返回值自动格式化输出
- [ ] 参数校验 @validate
- [ ] 参数别名

### 阶段3：API模式

- [ ] --serve 启动 REST API
- [ ] 自动生成 FastAPI 路由
- [ ] 自动生成 Pydantic model
- [ ] Swagger UI
- [ ] 错误处理和响应格式统一

### 阶段4：Web UI模式

- [ ] --web 启动 Web UI
- [ ] 左界面右控制台布局
- [ ] WebSocket 实时输出
- [ ] 参数类型 → HTML表单控件映射
- [ ] 执行历史记录

### 阶段5：生态集成

- [ ] nb_log / nb_config 集成
- [ ] 参数持久化（上次值记忆）
- [ ] __init__ 参数 → 全局选项

### 阶段6：打磨和发布

- [ ] 完善文档和README
- [ ] 丰富测试用例
- [ ] 性能优化
- [ ] PyPI 发布
- [ ] 和 funboost 集成示例

---

## 附录：完整示例

### A. 数据库管理工具

```python
from nb_cmd import NbCmd
from pathlib import Path
from typing import List, Optional
from enum import Enum
import json


class OutputFormat(Enum):
    TABLE = "table"
    JSON = "json"
    CSV = "csv"


class DbTool(NbCmd):
    """数据库管理工具 - 支持多种数据库的通用管理"""

    def __init__(self, db_url: str = "sqlite:///default.db", verbose: bool = False):
        super().__init__()
        self.db_url = db_url
        self.verbose = verbose
        self.conn = None

    class Meta:
        name = "dbtool"
        version = "1.0.0"
        use_nb_log = True
        auto_save_last_args = True

    def before_run(self):
        if self.verbose:
            self.info(f"连接数据库: {self.db_url}")
        # self.conn = create_engine(self.db_url).connect()

    def after_run(self):
        if self.conn:
            self.conn.close()

    def query(self, sql: str, output: OutputFormat = OutputFormat.TABLE, limit: int = 100):
        """执行SQL查询并展示结果"""
        self.info(f"执行: {sql}")
        # result = self.conn.execute(sql).fetchmany(limit)
        result = [{"id": 1, "name": "张三"}, {"id": 2, "name": "李四"}]  # mock
        
        if output == OutputFormat.TABLE:
            self.table(result)
        elif output == OutputFormat.JSON:
            self.json_print(result)
        elif output == OutputFormat.CSV:
            print("id,name")
            for row in result:
                print(",".join(str(v) for v in row.values()))
        
        return result

    def migrate(self, version: str = "latest", *, dry_run: bool = False):
        """执行数据库迁移"""
        if dry_run:
            self.warning("试运行模式，不会实际执行")
        self.info(f"迁移到版本: {version}")
        steps = ["检查版本", "备份数据", "执行迁移", "验证结果"]
        for step in self.progress(steps, desc="迁移进度"):
            import time; time.sleep(0.5)
        self.success("迁移完成")

    def backup(self, output: Path, tables: Optional[List[str]] = None, *, compress: bool = True):
        """备份数据库"""
        self.info(f"备份到: {output}")
        if tables:
            self.info(f"指定表: {tables}")
        if compress:
            self.info("启用压缩")
        self.success(f"备份完成: {output}")

    def restore(self, backup_file: Path):
        """从备份文件恢复数据库"""
        if not self.confirm(f"确认从 {backup_file} 恢复？这将覆盖现有数据！"):
            self.warning("已取消")
            return
        self.info(f"从 {backup_file} 恢复中...")
        self.success("恢复完成")

    def stats(self):
        """显示数据库统计信息"""
        self.kv({
            "数据库类型": "SQLite",
            "数据库大小": "15.3 MB",
            "表数量": "12",
            "总行数": "1,234,567",
            "最后备份": "2026-04-17 10:30:00",
            "连接池状态": "5/20 活跃",
        })


if __name__ == '__main__':
    DbTool().run()
```

CLI调用：

```bash
$ python db_tool.py --db-url "mysql://localhost/mydb" query "SELECT * FROM users" --output json --limit 50
$ python db_tool.py migrate --version v2.0 --dry-run
$ python db_tool.py backup ./backup.sql --tables users orders --compress
$ python db_tool.py stats
```

API调用：

```bash
$ python db_tool.py --serve --port 8080
# 自动生成:
# POST /query    {"sql": "...", "output": "table", "limit": 100}
# POST /migrate  {"version": "latest", "dry_run": false}
# POST /backup   {"output": "...", "tables": [...], "compress": true}
# POST /restore  {"backup_file": "..."}
# GET  /stats
```

### B. 服务器运维工具（继承示例）

```python
from nb_cmd import NbCmd
from typing import List


class BaseOps(NbCmd):
    """基础运维工具"""

    def __init__(self, ssh_key: str = "~/.ssh/id_rsa"):
        super().__init__()
        self.ssh_key = ssh_key

    def status(self, hosts: List[str]):
        """检查服务器状态"""
        for host in self.progress(hosts, desc="检查中"):
            status = self._check_host(host)
            if status['ok']:
                self.success(f"{host}: 正常 (CPU: {status['cpu']}%, MEM: {status['mem']}%)")
            else:
                self.error(f"{host}: 异常 - {status['error']}")

    def deploy(self, host: str, service: str, version: str = "latest"):
        """部署服务"""
        self._pre_deploy(host, service)
        self._do_deploy(host, service, version)
        self._post_deploy(host, service)
        self.success(f"{service}@{version} 已部署到 {host}")

    def _pre_deploy(self, host, service):
        self.info(f"部署前检查: {host}")

    def _do_deploy(self, host, service, version):
        self.info(f"部署 {service}@{version} 到 {host}")

    def _post_deploy(self, host, service):
        self.info(f"部署后验证: {host}")

    def _check_host(self, host):
        return {'ok': True, 'cpu': 45, 'mem': 67}


class DockerOps(BaseOps):
    """Docker运维工具——继承BaseOps，覆写部署逻辑"""

    def _do_deploy(self, host, service, version):
        self.info(f"docker pull {service}:{version}")
        self.info(f"docker-compose -f {service}.yml up -d")

    def _post_deploy(self, host, service):
        self.info(f"docker ps | grep {service}")
        super()._post_deploy(host, service)  # 也执行基类的验证


class K8sOps(BaseOps):
    """K8s运维工具——继承BaseOps，覆写部署逻辑"""

    def _do_deploy(self, host, service, version):
        self.info(f"kubectl set image deployment/{service} {service}={service}:{version}")

    def _post_deploy(self, host, service):
        self.info(f"kubectl rollout status deployment/{service}")

    def scale(self, service: str, replicas: int):
        """扩缩容（K8s特有命令）"""
        self.info(f"kubectl scale deployment/{service} --replicas={replicas}")
        self.success(f"{service} 已扩缩至 {replicas} 个副本")


if __name__ == '__main__':
    import sys
    # 选择运维模式
    ops_type = sys.argv.pop(1) if len(sys.argv) > 1 and sys.argv[1] in ('docker', 'k8s', 'base') else 'base'
    ops_map = {'base': BaseOps, 'docker': DockerOps, 'k8s': K8sOps}
    ops_map[ops_type]().run()
```

```bash
# 基础模式
$ python ops.py base status --hosts server1 server2 server3
$ python ops.py base deploy server1 myapp --version v2.0

# Docker模式（覆写了_do_deploy）
$ python ops.py docker deploy server1 myapp --version v2.0

# K8s模式（覆写了_do_deploy，还新增了scale命令）
$ python ops.py k8s deploy server1 myapp --version v2.0
$ python ops.py k8s scale myapp --replicas 5
```

---

## 总结

**nb_cmd 的核心颠覆点：**

1. **不是"更好的CLI框架"，而是"万能接口生成器"** —— 一个class，三种接口（CLI + REST API + Web UI）
2. **OOP继承覆写** —— typer/fire/click 都做不到的能力
3. **零核心依赖** —— CLI模式纯标准库，其他模式按需安装
4. **和nb生态无缝集成** —— nb_log/nb_config/nb_api/funboost
5. **不造没必要的轮子** —— 没有RPC模式，因为HTTP REST API已经能远程调用。真需要异步RPC就用funboost

**一句话：你已经会写class了，你的CLI/API/Web UI就已经写完了。**
