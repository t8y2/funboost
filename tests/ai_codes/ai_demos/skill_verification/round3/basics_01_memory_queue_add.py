"""round3 验证 using-funboost-basics 示例1: 零依赖 MEMORY_QUEUE 最小示例"""
import os
import time

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
_ts = int(time.time())
os.environ["PRINT_WRTIE_FILE_NAME"] = f"r3_basics_01_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"r3_basics_01_std_{_ts}"

from funboost import boost, BoosterParams, BrokerEnum


@boost(BoosterParams(
    queue_name="hello_funboost",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
))
def add(a, b):
    print(f"计算: {a} + {b} = {a + b}")
    return a + b


if __name__ == "__main__":
    add.push(1, 2)
    add.push(10, 20)
    add.consume()
    import time, os
    time.sleep(12)
    os._exit(66)
