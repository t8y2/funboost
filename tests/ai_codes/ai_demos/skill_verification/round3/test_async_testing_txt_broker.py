"""验证 SKILL: developing-funboost-testing — 测试 TXT 文件 broker"""
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"test_txt_broker_run1_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"test_txt_broker_std1_{_ts}"

from funboost import boost, BoosterParams, BrokerEnum


@boost(
    BoosterParams(
        queue_name=f"test_txt_broker_{_ts}",
        broker_kind=BrokerEnum.TXT_FILE,
        concurrent_num=3,
        qps=5,
    )
)
def txt_task(name: str, value: int):
    result = f"{name}={value * 10}"
    print(f"[OK] {result}")
    return result


if __name__ == "__main__":
    for i in range(5):
        txt_task.push(f"item_{i}", value=i)
    print("已发布 5 条消息")

    txt_task.consume()

    time.sleep(15)
    print("测试完成")
    os._exit(66)
