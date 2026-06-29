"""验证 using-funboost-basics skill 中的代码示例"""
import os
import time

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"verify_basics_{int(time.time())}"
os.environ["SYS_STD_FILE_NAME"] = f"verify_basics_std_{int(time.time())}"

from funboost import boost, BoosterParams, BrokerEnum, ConcurrentModeEnum, TaskOptions, fct, enable_ctrl_c_quit_on_windows

# 验证1: 基本 @boost + push + consume
@boost(BoosterParams(
    queue_name="verify_basics_task",
    broker_kind=BrokerEnum.SQLITE_QUEUE,
    concurrent_num=5,
    qps=10,
    max_retry_times=3,
    log_level=20,
))
def my_task(url: str, depth: int = 1):
    print(f"[OK] 处理 url={url}, depth={depth}")
    return f"done_{depth}"


# 验证2: publish + TaskOptions
@boost(BoosterParams(
    queue_name="verify_basics_publish",
    broker_kind=BrokerEnum.SQLITE_QUEUE,
    concurrent_num=3,
))
def publish_task(x: int, y: int):
    print(f"[OK] publish_task x={x}, y={y}, result={x+y}")
    return x + y


# 验证3: fct 上下文
@boost(BoosterParams(
    queue_name="verify_basics_fct",
    broker_kind=BrokerEnum.SQLITE_QUEUE,
    concurrent_num=2,
))
def fct_task(msg: str):
    print(f"[OK] fct.task_id={fct.task_id}")
    print(f"[OK] fct.queue_name={fct.queue_name}")
    print(f"[OK] fct.function_result_status.run_times={fct.function_result_status.run_times}")
    print(f"[OK] fct.full_msg keys={list(fct.full_msg.keys())}")
    return msg


# 验证4: 消费外部消息 (**kwargs)
@boost(BoosterParams(
    queue_name="verify_basics_external",
    broker_kind=BrokerEnum.SQLITE_QUEUE,
    should_check_publish_func_params=False,
))
def handle_external(**kwargs):
    print(f"[OK] external kwargs={kwargs}")


if __name__ == "__main__":
    # 发布消息
    for i in range(3):
        my_task.push(f"https://example.com/{i}", depth=i)

    # publish 方式
    publish_task.publish(
        {"x": 10, "y": 20},
        task_options=TaskOptions(countdown=0, task_id="custom-test-id")
    )

    # fct 上下文
    fct_task.push("hello_fct")

    # 外部消息
    handle_external.push(name="test", value=42)

    # 启动消费
    my_task.consume()
    publish_task.consume()
    fct_task.consume()
    handle_external.consume()

    time.sleep(15)
    print("[DONE] verify_basics 全部完成")
    os._exit(66)
