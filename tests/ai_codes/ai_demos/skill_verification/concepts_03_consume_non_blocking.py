"""验证 understanding-funboost-concepts: consume() 非阻塞多消费者"""
import os
import time

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
_ts = int(time.time())
os.environ["PRINT_WRTIE_FILE_NAME"] = f"concepts_03_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"concepts_03_std_{_ts}"

from funboost import boost, BoosterParams, BrokerEnum, enable_ctrl_c_quit_on_windows


@boost(BoosterParams(queue_name="concepts_03_f1", broker_kind=BrokerEnum.MEMORY_QUEUE))
def func1(x):
    print(f"[OK] func1 {x}")
    return x


@boost(BoosterParams(queue_name="concepts_03_f2", broker_kind=BrokerEnum.MEMORY_QUEUE))
def func2(x):
    print(f"[OK] func2 {x}")
    return x


@boost(BoosterParams(queue_name="concepts_03_f3", broker_kind=BrokerEnum.MEMORY_QUEUE))
def func3(x):
    print(f"[OK] func3 {x}")
    return x


if __name__ == "__main__":
    func1.push(1)
    func2.push(2)
    func3.push(3)
    func1.consume()
    func2.consume()
    func3.consume()
    enable_ctrl_c_quit_on_windows()
    time.sleep(15)
    os._exit(66)
