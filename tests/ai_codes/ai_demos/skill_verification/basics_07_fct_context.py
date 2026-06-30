"""验证 using-funboost-basics: 任务上下文 fct"""
import os
import time

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
_ts = int(time.time())
os.environ["PRINT_WRTIE_FILE_NAME"] = f"basics_07_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"basics_07_std_{_ts}"

from funboost import boost, BoosterParams, BrokerEnum, fct


@boost(BoosterParams(queue_name="ctx_demo", broker_kind=BrokerEnum.MEMORY_QUEUE))
def my_task(x):
    print(f"Task ID: {fct.task_id}")
    print(f"队列名: {fct.queue_name}")
    print(f"执行次数: {fct.function_result_status.run_times}")
    print(f"函数参数: {fct.function_result_status.function_params}")
    print(f"完整消息: {fct.full_msg}")
    fct.logger.info("当前任务 logger")
    return x


if __name__ == "__main__":
    my_task.push("hello")
    my_task.consume()
    time.sleep(15)
    os._exit(66)
