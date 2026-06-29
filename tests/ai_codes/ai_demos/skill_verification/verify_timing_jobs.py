"""验证 funboost-timing-jobs skill 中的代码示例"""
import os
import time

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"verify_timing_{int(time.time())}"
os.environ["SYS_STD_FILE_NAME"] = f"verify_timing_std_{int(time.time())}"

from funboost import boost, BoosterParams, BrokerEnum, ApsJobAdder

@boost(BoosterParams(
    queue_name="verify_timing_task",
    broker_kind=BrokerEnum.SQLITE_QUEUE,
    concurrent_num=3,
    qps=5,
))
def scheduled_task(action: str, count: int = 1):
    print(f"[OK] scheduled_task action={action}, count={count}, time={time.strftime('%H:%M:%S')}")
    return f"{action}_{count}"


if __name__ == "__main__":
    scheduled_task.consume()

    # 验证1: ApsJobAdder 构造 + interval 触发
    adder = ApsJobAdder(scheduled_task)
    adder.add_push_job(
        trigger="interval",
        seconds=3,
        kwargs={"action": "interval_test", "count": 1},
        id="verify_interval_job",
        replace_existing=True,
    )
    print(f"[OK] ApsJobAdder 创建成功，interval job 注册")

    # 验证2: job_store_kind 默认值
    adder2 = ApsJobAdder(scheduled_task, job_store_kind="memory")
    adder2.add_push_job(
        trigger="interval",
        seconds=4,
        kwargs={"action": "memory_store_test", "count": 2},
        id="verify_memory_job",
        replace_existing=True,
    )
    print(f"[OK] job_store_kind='memory' 正常工作")

    # 验证3: 直接 push 一些消息确认 consume 正常
    scheduled_task.push("direct_push", count=99)

    time.sleep(12)
    print("[DONE] verify_timing_jobs 完成")
    os._exit(66)
