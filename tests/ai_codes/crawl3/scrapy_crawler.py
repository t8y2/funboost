"""
Scrapy 版新闻爬虫 —— 按 Scrapy 官方最佳实践（Item + Pipeline）
与 funspider / feapder / boost_spider 相同爬取逻辑
目标: http://127.0.0.1:8765
结构: 分类列表 → 新闻列表(翻页) → 新闻详情

运行方式: python scrapy_crawler.py
（依赖: pip install scrapy）
"""
import os
import re
import sqlite3
import random

import scrapy
from scrapy.http import HtmlResponse
from scrapy import Item, Field
from user_agents import USER_AGENTS

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(_BASE_DIR, "scrapy_news.db")
BASE_URL = "http://127.0.0.1:8765"

CAT_ID_MAP = {
    1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1,
    7: 2, 8: 2, 9: 2, 10: 2, 11: 2, 12: 2,
    13: 3, 14: 3, 15: 3, 16: 3, 17: 3, 18: 3,
    19: 4, 20: 4, 21: 4, 22: 4, 23: 4, 24: 4,
}


# ==================== Scrapy Item ====================
class NewsItem(Item):
    """新闻数据模型（字段定义，没有类型注解，没有自动建表）"""
    news_id = Field()
    title = Field()
    summary = Field()
    content = Field()
    author = Field()
    category_id = Field()
    category_name = Field()
    publish_time = Field()
    url = Field()


# ==================== Scrapy Pipeline ====================
class SqlitePipeline:
    """Pipeline：负责将 Item 存入 SQLite"""

    def open_spider(self, spider):
        """爬虫启动时初始化数据库"""
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS news (
                news_id INTEGER UNIQUE,
                title TEXT, summary TEXT, content TEXT,
                author TEXT, category_id INTEGER,
                category_name TEXT, publish_time TEXT, url TEXT
            )
        """)
        self.conn.commit()

    def process_item(self, item, spider):
        """将单个 Item 写入数据库"""
        self.conn.execute("""
            INSERT OR REPLACE INTO news
            (news_id, title, summary, content, author, category_id, category_name, publish_time, url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            item["news_id"], item["title"], item["summary"], item["content"],
            item["author"], item["category_id"], item["category_name"],
            item["publish_time"], item["url"],
        ))
        self.conn.commit()
        print(f"scrapy 已保存: {item['title']}")
        return item

    def close_spider(self, spider):
        """爬虫结束时关闭数据库连接"""
        self.conn.close()


# ★ Scrapy 最佳实践：写一个 Downloader Middleware 来换 UA
class RandomUserAgentMiddleware:
    """下载中间件：每次请求随机切换 User-Agent"""
    def process_request(self, request, spider):
        request.headers["User-Agent"] = random.choice(USER_AGENTS)
        return None  # 继续处理

    def process_response(self, request, response, spider):
        return response


# ==================== Scrapy Spider ====================
class NewsSpider(scrapy.Spider):
    name = "news_spider"

    custom_settings = {
        # 注册 Pipeline（必须用字符串路径，IDE 无法补全）
        "ITEM_PIPELINES": {"scrapy_crawler.SqlitePipeline": 300},
        # ★ 注册 Downloader Middleware（又得字符串路径）
        "DOWNLOADER_MIDDLEWARES": {"scrapy_crawler.RandomUserAgentMiddleware": 400},
        # 不让scrapy自动去重
        "DUPEFILTER_CLASS": "scrapy.dupefilters.BaseDupeFilter",
        "DOWNLOAD_DELAY": 0,
        "CONCURRENT_REQUESTS": 32,
        "LOG_LEVEL": "INFO",
        "ROBOTSTXT_OBEY": False,
    }

    def start_requests(self):
        """第1层：爬取分类列表"""
        yield scrapy.Request(f"{BASE_URL}/categories", callback=self.parse_categories)

    def parse_categories(self, response: HtmlResponse):
        """解析分类列表，推送所有分类的新闻列表任务"""
        for a_tag in response.css("ul li a"):
            href = a_tag.attrib.get("href", "")
            if "/category/" in href:
                yield scrapy.Request(
                    url=response.urljoin(href),
                    callback=self.parse_news_list,
                )

    def parse_news_list(self, response: HtmlResponse):
        """解析分类新闻列表页，推送详情页任务 + 翻页"""
        for a_tag in response.css("table a"):
            href = a_tag.attrib.get("href", "")
            if href and "/news/" in href and "/categories" not in href:
                yield scrapy.Request(
                    url=response.urljoin(href),
                    callback=self.parse_news_detail,
                )
        # 翻页
        next_href = response.css("a.next-page::attr(href)").get("")
        if next_href:
            yield scrapy.Request(
                url=response.urljoin(next_href),
                callback=self.parse_news_list,
            )

    def parse_news_detail(self, response: HtmlResponse):
        """解析新闻详情，yield Item 给 Pipeline 处理"""
        title = response.css("h1::text").get("").strip()

        author = ""
        category_name = ""
        publish_time = ""
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
        news_id = int(re.search(r"/news/(\d+)", response.url).group(1))

        # yield Item → Pipeline 自动处理入库
        yield NewsItem({
            "news_id": news_id,
            "title": title,
            "summary": summary,
            "content": content,
            "author": author,
            "category_id": CAT_ID_MAP.get(news_id, 0),
            "category_name": category_name,
            "publish_time": publish_time,
            "url": response.url,
        })


if __name__ == "__main__":
    from twisted.internet import reactor
    reactor._handleSignals = lambda: None
    from scrapy.crawler import CrawlerRunner
    runner = CrawlerRunner()
    d = runner.crawl(NewsSpider)
    d.addBoth(lambda _: reactor.stop())
    reactor.run()
