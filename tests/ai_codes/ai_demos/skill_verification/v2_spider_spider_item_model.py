"""验证 funboost-spider-crawling SKILL — SpiderItem 数据模型与 upsert"""
import os
import sys
import time
from typing import ClassVar, Optional

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
_ts = int(time.time())
os.environ["PRINT_WRTIE_FILE_NAME"] = f"v2_spider_item_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"v2_spider_item_std_{_ts}"

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
    from funboost.contrib.funspider import SpiderItem, Field, create_engine
    report("import SpiderItem, Field, create_engine", True)
except Exception as e:
    report("import SpiderItem, Field, create_engine", False, str(e))
    time.sleep(15)
    os._exit(66)

# SKILL 示例用 MySQL；验证时用 SQLite 避免外部依赖
SQLITE_ENGINE = create_engine(f"sqlite:///v2_spider_item_{_ts}.db")


class NewsItem(SpiderItem, table=True):
    __tablename__: ClassVar[str] = "news"
    __engine__ = SQLITE_ENGINE
    __default_upsert_unique_fields__ = ["news_id"]

    id: Optional[int] = Field(default=None, primary_key=True)
    news_id: int = Field(unique=True)
    title: str = Field(max_length=200)
    url: str = Field(max_length=500)
    content: str


if __name__ == "__main__":
    try:
        NewsItem.create_table()
        report("NewsItem.create_table()", True)

        item = NewsItem(
            news_id=123,
            title="标题",
            url="https://example.com/123",
            content="正文",
        )
        saved = item.upsert()
        report("NewsItem(...).upsert()", saved.news_id == 123)

        item2 = NewsItem(
            news_id=123,
            title="新标题",
            url="https://example.com/123",
            content="更新正文",
        )
        updated = item2.upsert()
        report("upsert 去重更新", updated.title == "新标题", updated.title)

        report("upsert/insert 方法存在", all(
            hasattr(NewsItem, m) for m in ("insert", "upsert", "bulk_upsert")
        ))
    except Exception as e:
        report("SpiderItem 数据模型示例", False, str(e))

    print(f"\n=== 最终结果: {'PASS' if PASS else 'FAIL'} ===")
    sys.stdout.flush()
    time.sleep(15)
    os._exit(66)
