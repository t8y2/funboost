"""round3 验证 understanding-funboost-concepts 示例4: Celery 反例（文档说明，验证 Funboost 正确写法）"""
import os
import time

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
_ts = int(time.time())
os.environ["PRINT_WRTIE_FILE_NAME"] = f"r3_concepts_04_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"r3_concepts_04_std_{_ts}"

# Celery 反例（skill 文档中的禁止写法，不可在 funboost 中运行）:
# @app.task(bind=True)
# def my_task(self, x):
#     self.request.id

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
    print("[OK] Celery bind=True 反例跳过；验证 Funboost fct 写法")
    my_task.push(42)
    my_task.consume()
    import time, os
    time.sleep(12)
    os._exit(66)
