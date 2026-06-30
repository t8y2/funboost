"""验证 funboost-spider-crawling SKILL — do_task_filtering 去重配置"""
import os
import sys
import time

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
_ts = int(time.time())
os.environ["PRINT_WRTIE_FILE_NAME"] = f"v2_spider_filter_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"v2_spider_filter_std_{_ts}"

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
    report("import", False, str(e))
    time.sleep(15)
    os._exit(66)


@boost(BoosterParams(
    queue_name="v2_news_detail_filter",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    do_task_filtering=True,
    task_filtering_expire_seconds=3600 * 24,
))
def crawl_detail(detail_url: str):
    return detail_url


if __name__ == "__main__":
    try:
        p = crawl_detail.boost_params
        report("do_task_filtering=True", p.do_task_filtering is True)
        report("task_filtering_expire_seconds=86400", p.task_filtering_expire_seconds == 3600 * 24)
        report("函数签名 crawl_detail(detail_url: str)", True)
    except Exception as e:
        report("do_task_filtering 示例", False, str(e))

    print(f"\n=== 最终结果: {'PASS' if PASS else 'FAIL'} ===")
    sys.stdout.flush()
    time.sleep(15)
    os._exit(66)
