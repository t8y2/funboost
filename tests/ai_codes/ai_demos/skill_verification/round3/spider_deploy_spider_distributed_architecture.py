"""round3 验证 funboost-spider-crawling SKILL — 分布式爬虫架构（BoosterParams 继承 + consume_group）"""
import os
import sys
import time

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
_ts = int(time.time())
os.environ["PRINT_WRTIE_FILE_NAME"] = f"r3_spider_dist_arch_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"r3_spider_dist_arch_std_{_ts}"

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
    from funboost import boost, BoosterParams, BrokerEnum, BoostersManager, enable_ctrl_c_quit_on_windows
    report("import boost, BoosterParams, BrokerEnum, BoostersManager", True)
except Exception as e:
    report("import", False, str(e))
    time.sleep(12)
    os._exit(66)

CRAWLER_GROUP = "r3_news_crawler"


class NewsCrawlerParams(BoosterParams):
    broker_kind: str = BrokerEnum.MEMORY_QUEUE
    booster_group: str = CRAWLER_GROUP


@boost(NewsCrawlerParams(queue_name="r3_news_list", qps=2, do_task_filtering=False))
def crawl_list(page: int):
    return page


@boost(NewsCrawlerParams(queue_name="r3_news_detail", qps=5, max_retry_times=5))
def crawl_detail(detail_url: str):
    return detail_url


if __name__ == "__main__":
    try:
        report("NewsCrawlerParams.broker_kind", crawl_list.boost_params.broker_kind == BrokerEnum.MEMORY_QUEUE)
        report("NewsCrawlerParams.booster_group", crawl_list.boost_params.booster_group == CRAWLER_GROUP)
        report("crawl_list qps=2", crawl_list.boost_params.qps == 2)
        report("crawl_detail max_retry_times=5", crawl_detail.boost_params.max_retry_times == 5)
        report("BoostersManager.consume_group 可调用", callable(BoostersManager.consume_group))
        report("enable_ctrl_c_quit_on_windows 可调用", callable(enable_ctrl_c_quit_on_windows))
        BoostersManager.consume_group(CRAWLER_GROUP)
        crawl_list.push(page=1)
        report("crawl_list.push(page=1) 无异常", True)
    except Exception as e:
        report("分布式爬虫架构示例", False, str(e))

    print(f"\n=== 最终结果: {'PASS' if PASS else 'FAIL'} ===")
    sys.stdout.flush()
    time.sleep(12)
    os._exit(66)
