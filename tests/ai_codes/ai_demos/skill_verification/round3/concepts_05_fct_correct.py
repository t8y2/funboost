"""round3 验证 understanding-funboost-concepts 示例5: fct 上下文 Funboost 正确做法"""
import os
import time

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
_ts = int(time.time())
os.environ["PRINT_WRTIE_FILE_NAME"] = f"r3_concepts_05_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"r3_concepts_05_std_{_ts}"

from funboost import boost, BoosterParams, BrokerEnum, fct


@boost(BoosterParams(queue_name="xxx", broker_kind=BrokerEnum.MEMORY_QUEUE))
def my_task(x):
    fct.task_id
    fct.queue_name
    fct.function_result_status.run_times
    fct.full_msg
    fct.logger
    print(f"[OK] fct 属性访问正常 task_id={fct.task_id}")
    return x


if __name__ == "__main__":
    my_task.push(42)
    my_task.consume()
    import time, os
    time.sleep(12)
    os._exit(66)
