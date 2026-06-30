"""round3b: using-funboost-basics — MEMORY_QUEUE push/consume 运行时验证"""
import os
import time

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
_ts = int(time.time())
os.environ["PRINT_WRTIE_FILE_NAME"] = f"r3b_basics_02_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"r3b_basics_02_std_{_ts}"

from funboost import boost, BoosterParams, BrokerEnum

RESULTS = []


@boost(BoosterParams(
    queue_name="hello_funboost_r3b",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
))
def add(a, b):
    msg = f"计算: {a} + {b} = {a + b}"
    print(f"[OK] {msg}")
    RESULTS.append(a + b)
    return a + b


if __name__ == "__main__":
    r1 = add(3, 4)
    print(f"[OK] 直接调用 add(3,4)={r1}")
    add.push(1, 2)
    add.push(10, 20)
    add.consume()
    time.sleep(12)
    ok = r1 == 7 and 1 + 2 in RESULTS and 10 + 20 in RESULTS
    print(f"[{'PASS' if ok else 'FAIL'}] push/consume 结果: direct=7, consumed={RESULTS}")
    import os
    os._exit(66 if ok else 1)
