"""round3b: using-funboost-basics — publish/TaskOptions + fct 运行时验证"""
import os
import time

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
_ts = int(time.time())
os.environ["PRINT_WRTIE_FILE_NAME"] = f"r3b_basics_03_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"r3b_basics_03_std_{_ts}"

from funboost import boost, BoosterParams, BrokerEnum, TaskOptions, fct

CAPTURED = {}


@boost(BoosterParams(queue_name="ctx_demo_r3b", broker_kind=BrokerEnum.MEMORY_QUEUE))
def my_task(url: str, depth: int = 1):
    CAPTURED["task_id"] = fct.task_id
    CAPTURED["queue_name"] = fct.queue_name
    CAPTURED["run_times"] = fct.function_result_status.run_times
    CAPTURED["function_params"] = fct.function_params
    CAPTURED["full_msg"] = fct.full_msg
    fct.logger.info("当前任务 logger")
    print(f"[OK] fct task_id={fct.task_id}, queue={fct.queue_name}, params={fct.function_params}")
    return depth


if __name__ == "__main__":
    my_task.publish(
        {"url": "https://example.com", "depth": 3},
        task_options=TaskOptions(countdown=0, task_id="custom-id-r3b"),
    )
    my_task.consume()
    time.sleep(12)
    ok = (
        CAPTURED.get("queue_name") == "ctx_demo_r3b"
        and CAPTURED.get("function_params") == {"url": "https://example.com", "depth": 3}
        and CAPTURED.get("task_id") == "custom-id-r3b"
    )
    print(f"[{'PASS' if ok else 'FAIL'}] publish+fct: {CAPTURED}")
    import os
    os._exit(66 if ok else 1)
