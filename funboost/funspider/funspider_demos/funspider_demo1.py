import re
from typing import ClassVar, Optional
from funboost import boost, BoosterParams, BoostersManager, BrokerEnum, ctrl_c_recv, ConcurrentModeEnum
from funboost.funspider import SimpleSpiderClient, AsyncSpiderClient, SpiderItem, create_engine, create_async_engine, Field

NEWS_GROUP = "news_crawler"


class NewsCrawlerParams(BoosterParams):
    broker_kind: str = BrokerEnum.REDIS_ACK_ABLE
    booster_group: str = NEWS_GROUP

# ---------- 数据库 ----------
MYSQL_ENGINE = create_engine("mysql+pymysql://root:123456@127.0.0.1:3306/testdb")
ASYNC_MYSQL_ENGINE = create_async_engine("mysql+aiomysql://root:123456@127.0.0.1:3306/testdb")


class NewsItem(SpiderItem, table=True):
    __tablename__: ClassVar[str] = "news"
    __engine__ = MYSQL_ENGINE
    __async_engine__ = ASYNC_MYSQL_ENGINE
    __default_upsert_unique_fields__ = ["news_id"]

    id: Optional[int] = Field(default=None, primary_key=True)
    news_id: int = Field(unique=True)
    title: str
    summary: str
    content: str
    author: str
    category: str
    publish_time: str
    url: str


class CommentItem(SpiderItem, table=True):
    __tablename__: ClassVar[str] = "comments"
    __engine__ = MYSQL_ENGINE
    __async_engine__ = ASYNC_MYSQL_ENGINE
    __default_upsert_unique_fields__ = ["comment_id"]

    id: Optional[int] = Field(default=None, primary_key=True)
    comment_id: int = Field(unique=True)
    news_id: int
    user: str
    content: str
    like_count: int


NewsItem.create_table()
CommentItem.create_table()

def get_proxy_abuyun():
    return "http://userxx:passwdxx@http-pro.abuyun.com:9000"

def get_proxy_none():
    return None

# ---------- 客户端 ----------
sync_client = SimpleSpiderClient(proxy_getter_list=[
    # get_proxy_abuyun,
 get_proxy_none
 ])
async_client = AsyncSpiderClient(proxy_getter_list=[
    # get_proxy_abuyun,
 get_proxy_none
 ])

BASE_URL = "http://127.0.0.1:8888"


# ---------- 列表页爬虫（同步）：解析列表页，推送详情页任务 ----------
@boost(NewsCrawlerParams(queue_name="news_list", qps=2))
def crawl_list(page: int):
    resp = sync_client.get(f"{BASE_URL}/news/list?page={page}")
    links = resp.css("table a::attr(href)").getall()
    for href in links:
        if href and "/news/detail/" in href:
            detail_url = f"{BASE_URL}{href}" if href.startswith("/") else href
            crawl_detail.push(detail_url=detail_url)
    next_href = resp.css("a.next-page::attr(href)").get("")
    if next_href:
        crawl_list.push(page=page + 1)


# ---------- 详情页爬虫（同步）：解析新闻详情，保存新闻 + 推送评论任务 ----------
@boost(NewsCrawlerParams(queue_name="news_detail", qps=5))
def crawl_detail(detail_url: str):
    resp = sync_client.get(detail_url)
    title = resp.css("h1::text").get("").strip()
    content_p = resp.css("div.content p::text").getall()
    content = "\n".join(content_p) if content_p else ""
    author = ""
    category = ""
    publish_time = ""
    for p_text in content_p:
        if p_text.startswith("作者："):
            author = p_text.replace("作者：", "").strip()
        elif p_text.startswith("分类："):
            category = p_text.replace("分类：", "").strip()
        elif p_text.startswith("发布时间："):
            publish_time = p_text.replace("发布时间：", "").strip()
    summary = content_p[0] if content_p else ""

    news_id = int(re.search(r"/news/detail/(\d+)", detail_url).group(1))

    NewsItem(
        news_id=news_id, title=title, summary=summary,
        content=content, author=author, category=category,
        publish_time=publish_time, url=detail_url,
    ).upsert()

    crawl_comments.push(news_id=news_id)


# ---------- 评论页爬虫（异步）：请求评论接口，保存评论 ----------
@boost(NewsCrawlerParams(queue_name="news_comments", qps=10, concurrent_mode=ConcurrentModeEnum.ASYNC,
                         do_task_filtering=True, task_filtering_expire_seconds=3600))
async def crawl_comments(news_id: int):
    resp = await async_client.get(f"{BASE_URL}/news/comments/{news_id}")
    data = resp.resp_dict
    for c in data.get("comments", []):
        item = CommentItem(
            comment_id=c["id"], news_id=c["news_id"],
            user=c["user"], content=c["content"],
            like_count=c["like_count"],
        )
        await item.aio_upsert()


if __name__ == '__main__':
    BoostersManager.consume_group(NEWS_GROUP)

    crawl_list.push(page=1)

    ctrl_c_recv()
