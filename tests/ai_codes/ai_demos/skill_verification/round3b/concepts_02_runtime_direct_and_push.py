"""round3b: understanding-funboost-concepts — 反框架 direct call + push 运行时验证"""
import os
import time

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
_ts = int(time.time())
os.environ["PRINT_WRTIE_FILE_NAME"] = f"r3b_concepts_02_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"r3b_concepts_02_std_{_ts}"

from funboost import boost, BoosterParams, BrokerEnum

PUSH_DONE = False


def download(url):
    return f"content-of-{url}"


@boost(BoosterParams(queue_name="spider_r3b", broker_kind=BrokerEnum.MEMORY_QUEUE))
def process(url, depth=1):
    global PUSH_DONE
    result = download(url)
    print(f"[OK] process depth={depth} -> {result}")
    PUSH_DONE = True
    return result


if __name__ == "__main__":
    direct = process("http://example.com")
    print(f"[OK] 直接调用: {direct}")
    process.push("http://example.com")
    process.consume()
    time.sleep(12)
    ok = direct == "content-of-http://example.com" and PUSH_DONE
    print(f"[{'PASS' if ok else 'FAIL'}] direct+c push: direct_ok={direct!r}, push_consumed={PUSH_DONE}")
    import os
    os._exit(66 if ok else 1)
