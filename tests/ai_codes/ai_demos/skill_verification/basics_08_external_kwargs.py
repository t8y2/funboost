"""验证 using-funboost-basics: 消费外部系统消息 should_check_publish_func_params=False"""
import os
import time

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
_ts = int(time.time())
os.environ["PRINT_WRTIE_FILE_NAME"] = f"basics_08_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"basics_08_std_{_ts}"

from funboost import boost, BoosterParams, BrokerEnum


@boost(BoosterParams(
    queue_name="external_queue",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    should_check_publish_func_params=False,
))
def handle_external(**kwargs):
    """使用 **kwargs 接收任意 JSON 结构"""
    print(kwargs)


if __name__ == "__main__":
    handle_external.push(name="from_java", value=99)
    handle_external.consume()
    time.sleep(15)
    os._exit(66)
