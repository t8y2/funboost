"""验证 understanding-funboost-concepts: 反框架设计 process 示例"""
import os
import time

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
_ts = int(time.time())
os.environ["PRINT_WRTIE_FILE_NAME"] = f"concepts_01_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"concepts_01_std_{_ts}"

from funboost import boost, BoosterParams, BrokerEnum


def download(url):
    return f"content-of-{url}"


@boost(BoosterParams(queue_name="spider", broker_kind=BrokerEnum.MEMORY_QUEUE))
def process(url, depth=1):
    return download(url)


if __name__ == "__main__":
    direct = process("http://example.com")
    print(f"[OK] 直接调用: {direct}")
    process.push("http://example.com")
    process.consume()
    time.sleep(15)
    os._exit(66)
