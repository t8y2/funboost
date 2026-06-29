# -*- coding: utf-8 -*-
"""
AI 运行测试模板 - 多 Broker 任务调度演示
按照 funboost md_for_ai 规范编写，供 AI Agent 自动运行测试使用。

本演示包含：
1. SQLITE_QUEUE 快速任务（无需外部中间件）
2. SQLITE_QUEUE 慢速 IO 任务（无需外部中间件）
3. 多队列分组消费

运行方式：
    python tests/ai_codes/ai_demos/new_feature_demo/multi_broker_task_demo.py

AI 检查输出：
    - 检查 PRINT_WRTIE_FILE_NAME 对应的文件获取纯 print 输出
    - 检查 SYS_STD_FILE_NAME 对应的文件获取全量日志
"""

# ============================================
# 第一部分：AI 环境变量设置（必须放在最开头）
# ============================================
import os

# 设置 nb_log 的黑科技环境变量，方便 AI 从文件检查运行输出
os.environ["LOG_PATH"] = "d:/pythonlogs/ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = "multi_broker_demo.print"
os.environ["SYS_STD_FILE_NAME"] = "multi_broker_demo.std"

# ============================================
# 第二部分：导入依赖
# ============================================
import time
import random

from funboost import (
    boost, BoosterParams, BrokerEnum,
    BoostersManager, enable_ctrl_c_quit_on_windows
)


# ============================================
# 第三部分：定义任务函数
# ============================================

# ---------- 任务1：SQLite 队列快速计算任务 ----------
@boost(BoosterParams(
    queue_name="demo_sqlite_queue_fast",
    broker_kind=BrokerEnum.SQLITE_QUEUE,  # 纯 SQLite 队列，零外部依赖
    concurrent_num=20,
    qps=50,
    max_retry_times=2,
    function_timeout=10,
    booster_group="group_a",  # 分组消费用
))
def fast_calc_task(x: int, y: int):
    """快速计算任务：模拟耗时 0.05s 的计算"""
    result = x * y + random.randint(1, 100)
    time.sleep(0.05)
    print(f"[fast_calc_task] 计算: {x} * {y} + rand = {result}")
    return result


# ---------- 任务2：SQLite 队列慢速 IO 任务 ----------
@boost(BoosterParams(
    queue_name="demo_sqlite_queue_slow",
    broker_kind=BrokerEnum.SQLITE_QUEUE,
    concurrent_num=5,
    qps=2,  # 限流 2/s
    max_retry_times=3,
    function_timeout=30,
    booster_group="group_a",
))
def slow_io_task(task_name: str, duration: float = 1.0):
    """慢速 IO 任务：模拟耗时操作"""
    print(f"[slow_io_task] 开始执行任务: {task_name}, 预计耗时 {duration}s")
    time.sleep(duration)
    print(f"[slow_io_task] 任务完成: {task_name}")
    return f"{task_name}_done"


# ---------- 任务3：SQLite 队列用户行为处理任务 ----------
@boost(BoosterParams(
    queue_name="demo_sqlite_queue_user",
    broker_kind=BrokerEnum.SQLITE_QUEUE,
    concurrent_num=10,
    qps=10,
    max_retry_times=2,
    function_timeout=15,
    booster_group="group_b",
))
def user_action_task(user_id: int, action: str):
    """用户行为处理任务"""
    print(f"[user_action_task] 处理用户 {user_id} 的 {action} 行为")
    time.sleep(0.2)
    print(f"[user_action_task] 用户 {user_id} {action} 处理完成")
    return {"user_id": user_id, "action": action, "status": "success"}


# ============================================
# 第四部分：主程序
# ============================================
if __name__ == "__main__":
    print("=" * 60)
    print("Funboost 多队列分组消费演示")
    print("=" * 60)

    # ---- 4.1 发布快速计算任务（发布 30 条） ----
    print("\n[1/4] 发布 fast_calc_task 任务 30 条到 SQLITE_QUEUE...")
    for i in range(30):
        fast_calc_task.push(x=i, y=i + 1)
    print("fast_calc_task 发布完成\n")

    # ---- 4.2 发布慢速 IO 任务（发布 5 条） ----
    print("[2/4] 发布 slow_io_task 任务 5 条到 SQLITE_QUEUE...")
    for i in range(5):
        slow_io_task.push(task_name=f"slow_job_{i}", duration=0.5)
    print("slow_io_task 发布完成\n")

    # ---- 4.3 发布用户行为任务（发布 10 条） ----
    print("[3/4] 发布 user_action_task 任务 10 条到 SQLITE_QUEUE...")
    for i in range(10):
        user_action_task.push(user_id=1000 + i, action=f"click_{i}")
    print("user_action_task 发布完成\n")

    # ---- 4.4 启动消费 ----
    print("[4/4] 启动消费...")
    print("-" * 60)

    # 方式1：单独启动消费
    fast_calc_task.consume()
    slow_io_task.consume()
    user_action_task.consume()

    # 方式2：也可以按分组启动消费（group_a 和 group_b）
    # BoostersManager.consume_group("group_a")
    # BoostersManager.consume_group("group_b")

    print("-" * 60)
    print("消费已启动，等待任务处理完成...")

    # ============================================
    # 第五部分：AI 强制退出（防止消费循环阻塞）
    # ============================================
    # 评估：30 条 fast(0.05s) + 5 条 slow(0.5s) + 10 条 user(0.2s) ≈ 6s 处理完
    # 加上框架启动时间，给 15 秒足够
    wait_seconds = 15
    print(f"\n将在 {wait_seconds} 秒后自动强制退出程序...")
    time.sleep(wait_seconds)

    print(f"\n{'=' * 60}")
    print(f"{wait_seconds} 秒到了，自动强制退出程序")
    print(f"{'=' * 60}")
    os._exit(66)  # 强制退出，防止 AI Agent 一直等待
