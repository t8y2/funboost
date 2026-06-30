"""验证 understanding-funboost-concepts: fct 上下文（Funboost 正确做法）"""
import os
import time

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
_ts = int(time.time())
os.environ["PRINT_WRTIE_FILE_NAME"] = f"concepts_04_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"concepts_04_std_{_ts}"

from funboost import boost, BoosterParams, BrokerEnum, fct


@boost(BoosterParams(queue_name="xxx", broker_kind=BrokerEnum.MEMORY_QUEUE))
def my_task(x):
    print(f"fct.task_id={fct.task_id}")
    print(f"fct.queue_name={fct.queue_name}")
    print(f"fct.function_result_status.run_times={fct.function_result_status.run_times}")
    print(f"fct.full_msg type={type(fct.full_msg).__name__}")
    fct.logger.info("当前任务 logger")
    return x


if __name__ == "__main__":
    my_task.push(42)
    my_task.consume()
    time.sleep(15)
    os._exit(66)
