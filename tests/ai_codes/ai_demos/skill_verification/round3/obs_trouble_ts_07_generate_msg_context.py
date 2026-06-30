"""验证 round3 / funboost-troubleshooting SKILL §3 步骤5 预览消息格式 generate_msg_context"""
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"obs_trouble_ts_07_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"obs_trouble_ts_07_std_{_ts}"

from funboost import boost, BoosterParams, BrokerEnum

@boost(BoosterParams(
    queue_name=f"obs_trouble_ts_msg_ctx_{_ts}",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
))
def my_task(x, y):
    return x + y

if __name__ == "__main__":
    ctx_push = my_task.publisher.generate_msg_context_for_push(1, 2)
    ctx_publish = my_task.publisher.generate_msg_context_for_publish({"x": 1, "y": 2})
    print(ctx_push)
    print(ctx_publish)
    time.sleep(15)
    os._exit(66)
