"""验证 funboost-spider-crawling SKILL — 精准 QPS + 分布式控频"""
import os
import sys
import time

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
_ts = int(time.time())
os.environ["PRINT_WRTIE_FILE_NAME"] = f"v2_spider_qps_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"v2_spider_qps_std_{_ts}"

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
    time.sleep(15)
    os._exit(66)


@boost(BoosterParams(
    queue_name="v2_polite_crawl",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    qps=2,
    is_using_distributed_frequency_control=True,
))
def crawl(url: str):
    return url


if __name__ == "__main__":
    try:
        p = crawl.boost_params
        report("qps=2", p.qps == 2)
        report("is_using_distributed_frequency_control=True", p.is_using_distributed_frequency_control is True)
    except Exception as e:
        report("分布式控频示例", False, str(e))

    print(f"\n=== 最终结果: {'PASS' if PASS else 'FAIL'} ===")
    sys.stdout.flush()
    time.sleep(15)
    os._exit(66)
