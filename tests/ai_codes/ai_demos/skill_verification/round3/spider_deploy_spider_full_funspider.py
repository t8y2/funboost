"""round3 验证 funboost-spider-crawling SKILL — 完整 funspider 示例（结构/导入/参数，不发网络请求）"""
import os
import re
import sys
import time
from typing import ClassVar, Optional

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
_ts = int(time.time())
os.environ["PRINT_WRTIE_FILE_NAME"] = f"r3_spider_full_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"r3_spider_full_std_{_ts}"

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
    from funboost import (
        boost, BoosterParams, BoostersManager, BrokerEnum,
        enable_ctrl_c_quit_on_windows, ConcurrentModeEnum,
    )
    from funboost.contrib.funspider import (
        SimpleSpiderClient, AsyncSpiderClient, SpiderItem,
        create_engine, Field,
    )
    report("完整 funspider 示例全部 import", True)
except Exception as e:
    report("完整 funspider 示例 import", False, str(e))
    time.sleep(12)
    os._exit(66)

NEWS_GROUP = "r3_news_crawler_full"


class NewsCrawlerParams(BoosterParams):
    broker_kind: str = BrokerEnum.MEMORY_QUEUE
    booster_group: str = NEWS_GROUP


SQLITE_ENGINE = create_engine(f"sqlite:///r3_spider_full_{_ts}.db")


class NewsItem(SpiderItem, table=True):
    __tablename__: ClassVar[str] = "news"
    __engine__ = SQLITE_ENGINE
    __default_upsert_unique_fields__ = ["news_id"]

    id: Optional[int] = Field(default=None, primary_key=True)
    news_id: int = Field(unique=True)
    title: str
    content: str
    url: str


class CommentItem(SpiderItem, table=True):
    __tablename__: ClassVar[str] = "comments"
    __engine__ = SQLITE_ENGINE
    __default_upsert_unique_fields__ = ["comment_id"]

    id: Optional[int] = Field(default=None, primary_key=True)
    comment_id: int = Field(unique=True)
    news_id: int
    user: str
    content: str


NewsItem.create_table()
CommentItem.create_table()

sync_client = SimpleSpiderClient(retry_times=3)
async_client = AsyncSpiderClient(retry_times=3)
BASE_URL = "https://news.example.com"


@boost(NewsCrawlerParams(queue_name="r3_full_news_list", qps=2))
def crawl_list(page: int):
    return page


@boost(NewsCrawlerParams(
    queue_name="r3_full_news_detail", qps=5, max_retry_times=5,
    do_task_filtering=True, task_filtering_expire_seconds=3600 * 24 * 7,
))
def crawl_detail(detail_url: str):
    news_id = int(re.search(r"/news/(\d+)", detail_url).group(1))
    return news_id


@boost(NewsCrawlerParams(
    queue_name="r3_full_news_comments", qps=10,
    concurrent_mode=ConcurrentModeEnum.ASYNC,
    do_task_filtering=True, task_filtering_expire_seconds=3600,
))
async def crawl_comments(news_id: int):
    return news_id


if __name__ == "__main__":
    try:
        report("NewsItem/CommentItem 建表", True)
        report("SimpleSpiderClient retry_times=3", sync_client.retry_times == 3)
        report("AsyncSpiderClient retry_times=3", async_client.retry_times == 3)
        report("crawl_detail do_task_filtering", crawl_detail.boost_params.do_task_filtering is True)
        report("crawl_comments ASYNC 模式", crawl_comments.boost_params.concurrent_mode == ConcurrentModeEnum.ASYNC)
        report("re.search 解析 news_id", crawl_detail("/news/42") == 42)
        report("BoostersManager.consume_group", callable(BoostersManager.consume_group))
        report("enable_ctrl_c_quit_on_windows", callable(enable_ctrl_c_quit_on_windows))
    except Exception as e:
        report("完整 funspider 示例", False, str(e))

    print(f"\n=== 最终结果: {'PASS' if PASS else 'FAIL'} ===")
    sys.stdout.flush()
    time.sleep(12)
    os._exit(66)
