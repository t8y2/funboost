"""round3 验证 funboost-spider-crawling SKILL — 函数级重试示例"""
import os
import sys
import time

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
_ts = int(time.time())
os.environ["PRINT_WRTIE_FILE_NAME"] = f"r3_spider_retry_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"r3_spider_retry_std_{_ts}"

PASS = True


def report(name: str, ok: bool, detail: str = ""):
    global PASS
    if not ok:
        PASS = False
    status = "PASS" if ok else "FAIL"
    msg = f"[{status}] {name}"
    if detail:
        msg += f" — {detail}"
    print(msg)


try:
    from funboost import boost, BoosterParams, BrokerEnum
    report("import boost, BoosterParams", True)
except Exception as e:
    report("import", False, str(e))
    time.sleep(12)
    os._exit(66)


def save(title):
    return title


@boost(BoosterParams(
    queue_name="r3_reliable_crawl",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    max_retry_times=5,
))
def crawl(url: str):
    # 模拟 SKILL 示例逻辑，不发网络请求
    data = {"code": "ok", "result": {"title": "mock title"}}
    if data.get("code") == "captcha_required":
        raise Exception("触发验证码")
    title = data["result"]["title"]
    return save(title)


if __name__ == "__main__":
    try:
        report("max_retry_times=5", crawl.boost_params.max_retry_times == 5)
        result = crawl("https://example.com")
        report("crawl() 正常返回", result == "mock title", repr(result))
    except Exception as e:
        report("函数级重试示例", False, str(e))

    print(f"\n=== 最终结果: {'PASS' if PASS else 'FAIL'} ===")
    sys.stdout.flush()
    time.sleep(12)
    os._exit(66)
