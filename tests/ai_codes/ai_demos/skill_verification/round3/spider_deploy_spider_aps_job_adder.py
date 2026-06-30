"""round3 验证 funboost-spider-crawling SKILL — ApsJobAdder 定时爬取种子"""
import os
import sys
import time

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
_ts = int(time.time())
os.environ["PRINT_WRTIE_FILE_NAME"] = f"r3_spider_aps_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"r3_spider_aps_std_{_ts}"

PASS = True
CRAWLER_GROUP = "r3_seed_crawler"


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
    from funboost import boost, BoosterParams, BrokerEnum, ApsJobAdder
    report("import ApsJobAdder", True)
except Exception as e:
    report("import ApsJobAdder", False, str(e))
    time.sleep(12)
    os._exit(66)


@boost(BoosterParams(queue_name="r3_seed_scheduler", broker_kind=BrokerEnum.MEMORY_QUEUE, booster_group=CRAWLER_GROUP))
def push_daily_seeds():
    return list(range(1, 11))


@boost(BoosterParams(queue_name="r3_crawl_list_seed", broker_kind=BrokerEnum.MEMORY_QUEUE))
def crawl_list(cat_id: int):
    return cat_id


if __name__ == "__main__":
    try:
        # SKILL 示例用 redis job_store；验证时用 memory 避免 Redis 依赖
        adder = ApsJobAdder(push_daily_seeds, job_store_kind="memory", is_auto_start=False)
        report("ApsJobAdder 实例化", isinstance(adder, ApsJobAdder))
        report("add_push_job 方法存在", callable(adder.add_push_job))
        job = adder.add_push_job(
            trigger="cron",
            hour=0,
            minute=0,
            id="daily_seeds",
            replace_existing=True,
        )
        report("add_push_job(cron, hour=0, minute=0) 无异常", job is not None)
        report("push_daily_seeds.booster_group", push_daily_seeds.boost_params.booster_group == CRAWLER_GROUP)
    except Exception as e:
        report("ApsJobAdder 定时种子示例", False, str(e))

    print(f"\n=== 最终结果: {'PASS' if PASS else 'FAIL'} ===")
    sys.stdout.flush()
    time.sleep(12)
    os._exit(66)
