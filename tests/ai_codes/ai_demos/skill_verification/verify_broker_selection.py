"""验证 funboost-broker-selection skill 中的代码示例 — 多种 broker"""
import os
import time

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"verify_broker_{int(time.time())}"
os.environ["SYS_STD_FILE_NAME"] = f"verify_broker_std_{int(time.time())}"

from funboost import boost, BoosterParams, BrokerEnum


# 验证1: MEMORY_QUEUE（零序列化开销，速度最快）
@boost(BoosterParams(
    queue_name="verify_mem_queue",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    concurrent_num=3,
    qps=10,
))
def mem_task(msg: str):
    print(f"[OK] mem_task msg={msg}")
    return msg


# 验证2: SQLITE_QUEUE（本地持久化）
@boost(BoosterParams(
    queue_name="verify_sqlite_queue",
    broker_kind=BrokerEnum.SQLITE_QUEUE,
    concurrent_num=3,
    qps=10,
))
def sqlite_task(x: int, y: int):
    result = x + y
    print(f"[OK] sqlite_task x={x}, y={y}, result={result}")
    return result


# 验证3: TXT_FILE（文本文件队列）
@boost(BoosterParams(
    queue_name="verify_txt_queue",
    broker_kind=BrokerEnum.TXT_FILE,
    concurrent_num=2,
    qps=5,
))
def txt_task(name: str, age: int):
    print(f"[OK] txt_task name={name}, age={age}")
    return f"{name}_{age}"


if __name__ == "__main__":
    # 先发布消息
    for i in range(3):
        mem_task.push(f"memory_msg_{i}")
        sqlite_task.push(i, i * 10)
        txt_task.push(f"user_{i}", age=20 + i)

    # 启动消费
    mem_task.consume()
    sqlite_task.consume()
    txt_task.consume()

    time.sleep(10)
    print("[DONE] verify_broker_selection 完成")
    os._exit(66)
