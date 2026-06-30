"""round3 验证 using-funboost-basics 示例6: 启动多个消费者"""
import os
import time

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
_ts = int(time.time())
os.environ["PRINT_WRTIE_FILE_NAME"] = f"r3_basics_06_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"r3_basics_06_std_{_ts}"

from funboost import boost, BoosterParams, BrokerEnum


@boost(BoosterParams(queue_name="r3_basics_06_a", broker_kind=BrokerEnum.MEMORY_QUEUE))
def task_a(x):
    print(f"[OK] task_a {x}")
    return x


@boost(BoosterParams(queue_name="r3_basics_06_b", broker_kind=BrokerEnum.MEMORY_QUEUE))
def task_b(x):
    print(f"[OK] task_b {x}")
    return x


@boost(BoosterParams(queue_name="r3_basics_06_c", broker_kind=BrokerEnum.MEMORY_QUEUE))
def task_c(x):
    print(f"[OK] task_c {x}")
    return x


if __name__ == "__main__":
    task_a.push(1)
    task_b.push(2)
    task_c.push(3)
    task_a.consume()
    task_b.consume()
    task_c.consume()
    import time, os
    time.sleep(12)
    os._exit(66)
