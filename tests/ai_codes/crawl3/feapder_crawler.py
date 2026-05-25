import os
import re
import random
import sqlite3
from typing import List, Dict

import feapder
from feapder import Request, Item
from feapder.pipelines import BasePipeline
from user_agents import USER_AGENTS

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class SqlitePipeline(BasePipeline):
    """SQLite 持久化 Pipeline"""

    def __init__(self):
        db_path = os.path.join(_BASE_DIR, "feapder_news.db")
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS news (
                news_id INTEGER UNIQUE, title TEXT, summary TEXT,
                content TEXT, author TEXT, category_id INTEGER,
                category_name TEXT, publish_time TEXT, url TEXT
            )
        """)
        self.conn.commit()

    def save_items(self, table, items: List[Dict]) -> bool:
        for item in items:
            self.conn.execute("""
                INSERT OR REPLACE INTO news
                (news_id, title, summary, content, author, category_id, category_name, publish_time, url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                item.get("news_id"), item.get("title"), item.get("summary"),
                item.get("content"), item.get("author"), item.get("category_id"),
                item.get("category_name"), item.get("publish_time"), item.get("url"),
            ))
        self.conn.commit()
        print(f"feapder 已保存 {len(items)} 条: {items[0].get('title')} 等")
        return True

    def close(self):
        self.conn.close()


CAT_ID_MAP = {
    1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1,
    7: 2, 8: 2, 9: 2, 10: 2, 11: 2, 12: 2,
    13: 3, 14: 3, 15: 3, 16: 3, 17: 3, 18: 3,
    19: 4, 20: 4, 21: 4, 22: 4, 23: 4, 24: 4,
}


# ★ feapder 最佳实践：用 download_midware 统一设置自定义 UA
# 所有 Request 在下载前都会经过此方法，一次定义全局生效


class NewsItem(Item):
    def __init__(self, *args, **kwargs):
        self.news_id = None
        self.title = None
        self.summary = None
        self.content = None
        self.author = None
        self.category_id = None
        self.category_name = None
        self.publish_time = None
        self.url = None


class NewsSpider(feapder.AirSpider):
    __custom_setting__ = {
        "ITEM_PIPELINES": ["feapder_crawler.SqlitePipeline"],
    }

    # ★ feapder 最佳实践：download_midware 统一设置自定义 UA
    def download_midware(self, request):
        request.headers = {"User-Agent": random.choice(USER_AGENTS)}
        return request

    def start_requests(self):
        yield Request("http://127.0.0.1:8765/categories", callback=self.parse_categories)

    def parse_categories(self, request, response):
        for a_tag in response.css("ul li a"):
            href = a_tag.attrib.get("href", "")
            if "/category/" in href:
                yield Request(href, callback=self.parse_news_list)

    def parse_news_list(self, request, response):
        for a_tag in response.css("table a"):
            href = a_tag.attrib.get("href", "")
            if href and "/news/" in href and "/categories" not in href:
                yield Request(href, callback=self.parse_news_detail)
        next_href = response.css("a.next-page::attr(href)").get("")
        if next_href:
            yield Request(next_href, callback=self.parse_news_list)

    def parse_news_detail(self, request, response):
        title = response.css("h1::text").get("").strip()
        author = category_name = publish_time = ""
        summary = ""
        content_parts = []

        for p_elem in response.css("div.content p"):
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
        news_id = int(re.search(r"/news/(\d+)", request.url).group(1))

        item = NewsItem()
        item.table_name = "news"
        item.news_id = news_id
        item.title = title
        item.summary = summary
        item.content = content
        item.author = author
        item.category_id = CAT_ID_MAP.get(news_id, 0)
        item.category_name = category_name
        item.publish_time = publish_time
        item.url = request.url
        yield item


if __name__ == "__main__":
    spider = NewsSpider(thread_count=3)
    spider.start()
