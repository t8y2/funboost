import re
from typing import ClassVar, Optional
from funboost import boost, BoosterParams, BoostersManager, BrokerEnum, enable_ctrl_c_quit_on_windows
from funboost.contrib.funspider import SimpleSpiderClient, SpiderItem, create_engine, Field

NEWS_GROUP = "funspider_news_crawler"


class SpiderCrawlerParams(BoosterParams):
    broker_kind: str = BrokerEnum.REDIS_ACK_ABLE
    booster_group: str = NEWS_GROUP


SQLITE_ENGINE = create_engine("sqlite:///funspider_news.db")


class NewsItem(SpiderItem, table=True):
    __tablename__: ClassVar[str] = "news"
    __engine__ = SQLITE_ENGINE
    __default_upsert_unique_fields__ = ["news_id"]

    id: Optional[int] = Field(default=None, primary_key=True)
    news_id: int = Field(unique=True)
    title: str
    summary: str
    content: str
    author: str
    category_id: int
    category_name: str
    publish_time: str
    url: str


NewsItem.create_table()

from user_agents import USER_AGENTS

# ★ funspider 最佳实践：SimpleSpiderClient 内置 UA 随机轮换，一行配置搞定
# ★ funspider 最佳实践：SimpleSpiderClient 内置 UA 随机轮换，一行配置搞定
sync_client = SimpleSpiderClient(
    user_agents=USER_AGENTS,   # ★ 传入 UA 列表，框架自动每次请求随机切换
    retry_times=3,             # ★ 请求失败自动重试
)
BASE_URL = "http://127.0.0.1:8765"


@boost(SpiderCrawlerParams(queue_name="news_categories", qps=1))
def crawl_categories():
    """第1层：爬取分类列表，获取所有分类ID"""
    resp = sync_client.get(f"{BASE_URL}/categories")
    links = resp.css("ul li a::attr(href)").getall()
    for href in links:
        if href and "/category/" in href:
            cat_id = int(re.search(r"/category/(\d+)/news", href).group(1))
            crawl_news_list.push(cat_id=cat_id, page=1)


@boost(SpiderCrawlerParams(queue_name="news_list", qps=3))
def crawl_news_list(cat_id: int, page: int):
    """第2层：爬取分类下的新闻列表，推送详情页任务"""
    resp = sync_client.get(f"{BASE_URL}/category/{cat_id}/news?page={page}")
    links = resp.css("table a::attr(href)").getall()
    for href in links:
        if href and "/news/" in href and href != "/categories":
            news_url = f"{BASE_URL}{href}" if href.startswith("/") else href
            crawl_news_detail.push(news_url=news_url)
    next_href = resp.css("a.next-page::attr(href)").get("")
    if next_href:
        crawl_news_list.push(cat_id=cat_id, page=page + 1)


@boost(SpiderCrawlerParams(queue_name="news_detail", qps=5))
def crawl_news_detail(news_url: str):
    """第3层：爬取新闻详情，解析并保存到SQLite"""
    resp = sync_client.get(news_url)
    title = resp.css("h1::text").get("").strip()

    author = ""
    category_name = ""
    publish_time = ""
    summary = ""
    content_parts = []

    for p_elem in resp.css("div.content p"):
        full_text = "".join(p_elem.css("::text").getall()).strip()
        if not full_text:
            continue
        if full_text.startswith("作者："):
            author = full_text.replace("作者：", "").strip()
        elif full_text.startswith("分类："):
            category_name = full_text.replace("分类：", "").strip()
        elif full_text.startswith("发布时间："):
            publish_time = full_text.replace("发布时间：", "").strip()
        else:
            if not summary:
                summary = full_text
            content_parts.append(full_text)
    content = "\n".join(content_parts)

    news_id = int(re.search(r"/news/(\d+)", news_url).group(1))
    category_id = _CAT_ID_MAP.get(news_id, 0)

    NewsItem(
        news_id=news_id, title=title, summary=summary,
        content=content, author=author, category_name=category_name,
        category_id=category_id,
        publish_time=publish_time, url=news_url,
    ).upsert()
    print(f"funspider 已保存: {title}")


_CAT_ID_MAP = {
    1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1,
    7: 2, 8: 2, 9: 2, 10: 2, 11: 2, 12: 2,
    13: 3, 14: 3, 15: 3, 16: 3, 17: 3, 18: 3,
    19: 4, 20: 4, 21: 4, 22: 4, 23: 4, 24: 4,
}


if __name__ == "__main__":
    BoostersManager.consume_group(NEWS_GROUP)
    crawl_categories.push()
    print("正在启动 funspider 爬虫...")
    enable_ctrl_c_quit_on_windows()
