import re
import os
from boost_spider import boost, BoosterParams, BrokerEnum, RequestClient, BoostersManager, enable_ctrl_c_quit_on_windows
from boost_spider.sink.dataset_sink import DatasetSink

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sink = DatasetSink(f"sqlite:///{os.path.join(_BASE_DIR, 'boost_spider_news.db')}")

CAT_ID_MAP = {
    1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1,
    7: 2, 8: 2, 9: 2, 10: 2, 11: 2, 12: 2,
    13: 3, 14: 3, 15: 3, 16: 3, 17: 3, 18: 3,
    19: 4, 20: 4, 21: 4, 22: 4, 23: 4, 24: 4,
}

from user_agents import USER_AGENTS

BASE_URL = "http://127.0.0.1:8765"
# ★ boost_spider 最佳实践：RequestClient 内置 UA 随机轮换
client = RequestClient(
    request_retry_times=3,
    is_change_ua_every_request=True,  # ★ 开启自动随机 UA
    user_agent_list=USER_AGENTS,      # ★ 传入自定义 UA 池
)


@boost(BoosterParams(queue_name="bspider_categories", broker_kind=BrokerEnum.REDIS_ACK_ABLE, qps=1, booster_group="bspider_group"))
def crawl_categories():
    sel = client.get(f"{BASE_URL}/categories").selector
    for a in sel.css("ul li a"):
        href = a.attrib.get("href", "")
        if "/category/" in href:
            cat_id = int(re.search(r"/category/(\d+)/news", href).group(1))
            crawl_news_list.push(cat_id, 1)


@boost(BoosterParams(queue_name="bspider_news_list", broker_kind=BrokerEnum.REDIS_ACK_ABLE, qps=3, booster_group="bspider_group"))
def crawl_news_list(cat_id: int, page: int):
    sel = client.get(f"{BASE_URL}/category/{cat_id}/news?page={page}").selector
    for a in sel.css("table a"):
        href = a.attrib.get("href", "")
        if href and "/news/" in href and "/categories" not in href:
            news_url = f"{BASE_URL}{href}" if href.startswith("/") else href
            crawl_news_detail.push(news_url)
    next_href = sel.css("a.next-page::attr(href)").get("")
    if next_href:
        crawl_news_list.push(cat_id, page + 1)


@boost(BoosterParams(
    queue_name="bspider_news_detail", broker_kind=BrokerEnum.REDIS_ACK_ABLE, qps=5,
    max_retry_times=3, do_task_filtering=True, booster_group="bspider_group",
))
def crawl_news_detail(news_url: str):
    sel = client.get(news_url).selector
    title = sel.css("h1::text").get("").strip()

    author = category_name = publish_time = ""
    summary = ""
    content_parts = []

    for p in sel.css("div.content p"):
        full_text = "".join(p.css("::text").getall()).strip()
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

    news_id = int(re.search(r"/news/(\d+)", news_url).group(1))
    content = "\n".join(content_parts)

    sink.save("news", {
        "news_id": news_id,
        "title": title,
        "summary": summary,
        "content": content,
        "author": author,
        "category_id": CAT_ID_MAP.get(news_id, 0),
        "category_name": category_name,
        "publish_time": publish_time,
        "url": news_url,
    })
    print(f"boost_spider 已保存: {title}")


if __name__ == "__main__":
    BoostersManager.consume_group("bspider_group", block=False)
    crawl_categories.push()
    enable_ctrl_c_quit_on_windows()
