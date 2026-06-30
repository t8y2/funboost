"""验证 funboost-spider-crawling SKILL — 模式1：纯 @boost 函数调度"""
import os
import sys
import time

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
_ts = int(time.time())
os.environ["PRINT_WRTIE_FILE_NAME"] = f"v2_spider_mode1_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"v2_spider_mode1_std_{_ts}"

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
    report("import boost, BoosterParams, BrokerEnum", True)
except Exception as e:
    report("import boost, BoosterParams, BrokerEnum", False, str(e))
    time.sleep(15)
    os._exit(66)


def get_my_proxy():
    return None


def get_my_headers():
    return {"User-Agent": "test-agent"}


def parse_detail(text: str):
    return {"text_len": len(text)}


def save_to_mysql(data):
    return data


@boost(BoosterParams(
    queue_name="v2_crawl_detail_mode1",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    qps=5,
    max_retry_times=3,
))
def crawl_detail(url: str):
    # 不发网络请求，只验证函数结构与参数
    data = parse_detail(f"<html>mock for {url}</html>")
    save_to_mysql(data)
    return data


if __name__ == "__main__":
    try:
        params = crawl_detail.boost_params
        report("BoosterParams.qps=5", params.qps == 5)
        report("BoosterParams.max_retry_times=3", params.max_retry_times == 3)
        report("BoosterParams.queue_name", params.queue_name == "v2_crawl_detail_mode1")
        result = crawl_detail.push(url="https://example.com/article/123")
        report("crawl_detail.push(url=...) 返回 AsyncResult", hasattr(result, "task_id"))
        crawl_detail.consume()
        report("crawl_detail.consume() 无异常", True)
    except Exception as e:
        report("模式1 纯 @boost 示例", False, str(e))

    print(f"\n=== 最终结果: {'PASS' if PASS else 'FAIL'} ===")
    sys.stdout.flush()
    time.sleep(15)
    os._exit(66)
