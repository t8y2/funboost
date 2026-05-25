# new_feature_demo - AI 新特性演示目录

本目录用于存放 AI 编写的 funboost 新特性演示脚本。

## 运行方式

### 方式一：CMD
```cmd
set PYTHONPATH=D:\codes\funboost
python tests/ai_codes/ai_demos/new_feature_demo/multi_broker_task_demo.py
```

### 方式二：PowerShell
```powershell
$env:PYTHONPATH="D:\codes\funboost"
python tests/ai_codes/ai_demos/new_feature_demo/multi_broker_task_demo.py
```

## 当前演示脚本

### multi_broker_task_demo.py
**功能**：多队列分组消费演示

**包含任务**：
1. `fast_calc_task` - SQLite 快速计算任务（30 条，qps=50, concurrent=20）
2. `slow_io_task` - SQLite 慢速 IO 任务（5 条，qps=2, concurrent=5）
3. `user_action_task` - 用户行为处理任务（10 条，qps=10, concurrent=10）

**特点**：
- 使用 `SQLITE_QUEUE`，零外部依赖
- 演示分组消费（`booster_group`）
- 15 秒后自动强制退出（符合 AI 运行规范）

**运行时间**：约 15 秒

## 规范说明

按照 `funboost/md_for_ai/` 目录下的 AI 编程指南编写：
- 脚本开头设置 `LOG_PATH`、`PRINT_WRTIE_FILE_NAME`、`SYS_STD_FILE_NAME` 环境变量
- 使用 `BoosterParams` 传参（禁止老式写法）
- 脚本末尾使用 `time.sleep(15) + os._exit(66)` 强制退出
- 运行前必须设置 `PYTHONPATH=项目根目录`
