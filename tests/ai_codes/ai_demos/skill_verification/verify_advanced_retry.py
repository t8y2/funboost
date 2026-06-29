"""验证 funboost-advanced-retry skill 中的代码示例"""
import os
import time

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"verify_retry_{int(time.time())}"
os.environ["SYS_STD_FILE_NAME"] = f"verify_retry_std_{int(time.time())}"

from funboost import boost, BoosterParams, BrokerEnum, fct

# 验证1: 基础重试
@boost(BoosterParams(
    queue_name="verify_retry_basic",
    broker_kind=BrokerEnum.SQLITE_QUEUE,
    max_retry_times=3,
    function_timeout=10,
    concurrent_num=2,
))
def basic_retry_task(x: int):
    run_times = fct.function_result_status.run_times
    print(f"[RETRY] basic_retry_task x={x}, run_times={run_times}")
    if run_times <= 2:
        raise ValueError(f"模拟失败 run_times={run_times}")
    print(f"[OK] basic_retry_task 第 {run_times} 次执行成功")
    return x * 2


# 验证2: 指数退避
@boost(BoosterParams(
    queue_name="verify_retry_backoff",
    broker_kind=BrokerEnum.SQLITE_QUEUE,
    max_retry_times=3,
    is_using_advanced_retry=True,
    concurrent_num=1,
))
def backoff_task(msg: str):
    run_times = fct.function_result_status.run_times
    print(f"[BACKOFF] msg={msg}, run_times={run_times}, time={time.strftime('%H:%M:%S')}")
    if run_times <= 2:
        raise Exception("模拟退避失败")
    print(f"[OK] backoff_task 成功")
    return msg


# 验证3: advanced_retry_config 自定义参数
@boost(BoosterParams(
    queue_name="verify_retry_custom_config",
    broker_kind=BrokerEnum.SQLITE_QUEUE,
    max_retry_times=3,
    is_using_advanced_retry=True,
    advanced_retry_config={
        "retry_mode": "sleep",
        "retry_base_interval": 1.0,
        "retry_multiplier": 2.0,
        "retry_max_interval": 10.0,
        "retry_jitter": False,
    },
    concurrent_num=1,
))
def custom_config_task(x: int):
    run_times = fct.function_result_status.run_times
    print(f"[CUSTOM_CFG] x={x}, run_times={run_times}, time={time.strftime('%H:%M:%S')}")
    if run_times <= 1:
        raise Exception("custom config 退避")
    print(f"[OK] custom_config_task 成功")
    return x


# 验证4: DLX 死信队列
@boost(BoosterParams(
    queue_name="verify_retry_dlx",
    broker_kind=BrokerEnum.SQLITE_QUEUE,
    max_retry_times=2,
    is_push_to_dlx_queue_when_retry_max_times=True,
    concurrent_num=1,
))
def dlx_task(job_id: str):
    run_times = fct.function_result_status.run_times
    print(f"[DLX] job_id={job_id}, run_times={run_times}")
    raise Exception(f"永远失败，测试 DLX")


if __name__ == "__main__":
    # 发布测试消息
    basic_retry_task.push(42)
    backoff_task.push("test_backoff")
    custom_config_task.push(99)
    dlx_task.push("dlx_test_job")

    # 启动消费
    basic_retry_task.consume()
    backoff_task.consume()
    custom_config_task.consume()
    dlx_task.consume()

    time.sleep(30)
    print("[DONE] verify_advanced_retry 完成")
    os._exit(66)
