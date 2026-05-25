"""
80% 的人手写爬虫的方式 —— 没有 @boost，没有框架，一切自己搓

目标: http://127.0.0.1:8765
结构: 分类列表 → 新闻列表(翻页) → 新闻详情

和 funspider / boost_spider / feapder / scrapy 完全相同的爬取逻辑。

运行方式: python handwritten_crawler.py
（需要先启动 fake_news_site.py，并确保 Redis 在运行）
"""
import os
import re
import json
import time
import sqlite3
import threading
import random
from typing import Optional

import redis as redis_module
import requests
from parsel import Selector
from user_agents import USER_AGENTS

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(_BASE_DIR, "handwritten_news.db")
BASE_URL = "http://127.0.0.1:8765"

# ---- Redis 连接（队列也是自己搓） ----
r = redis_module.Redis(host="localhost", port=6379, db=0)

# ---- 数据库也是自己初始化 ----
def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS news (
            news_id INTEGER UNIQUE,
            title TEXT,
            summary TEXT,
            content TEXT,
            author TEXT,
            category_id INTEGER,
            category_name TEXT,
            publish_time TEXT,
            url TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_news(item: dict):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        INSERT OR REPLACE INTO news
        (news_id, title, summary, content, author, category_id, category_name, publish_time, url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        item["news_id"], item["title"], item["summary"], item["content"],
        item["author"], item["category_id"], item["category_name"],
        item["publish_time"], item["url"],
    ))
    conn.commit()
    conn.close()

CAT_ID_MAP = {
    1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1,
    7: 2, 8: 2, 9: 2, 10: 2, 11: 2, 12: 2,
    13: 3, 14: 3, 15: 3, 16: 3, 17: 3, 18: 3,
    19: 4, 20: 4, 21: 4, 22: 4, 23: 4, 24: 4,
}


# ========== 核心爬虫函数（和 funspider 的完全一样） ==========

def _headers():
    """★ 手写换 UA 的最佳实践：每次请求前生成随机 headers"""
    return {"User-Agent": random.choice(USER_AGENTS)}


def crawl_categories():
    """第1层：爬取分类列表，推送所有分类ID到 list_queue"""
    resp = requests.get(f"{BASE_URL}/categories", headers=_headers())
    sel = Selector(resp.text)
    for a_tag in sel.css("ul li a"):
        href = a_tag.attrib.get("href", "")
        if "/category/" in href:
            cat_id = int(re.search(r"/category/(\d+)/news", href).group(1))
            # 手写 push 到 redis 队列（blpop 不安全！）
            r.lpush("queue_news_list", json.dumps({"cat_id": cat_id, "page": 1}))


def crawl_news_list(cat_id: int, page: int):
    """第2层：爬取分类下的新闻列表，推送详情页链接"""
    resp = requests.get(f"{BASE_URL}/category/{cat_id}/news?page={page}", headers=_headers())
    sel = Selector(resp.text)
    for a_tag in sel.css("table a"):
        href = a_tag.attrib.get("href", "")
        if href and "/news/" in href and "/categories" not in href:
            news_url = href if href.startswith("http") else f"{BASE_URL}{href}"
            r.lpush("queue_news_detail", json.dumps({"news_url": news_url}))
    # 翻页
    next_href = sel.css("a.next-page::attr(href)").get("")
    if next_href:
        next_url = next_href if next_href.startswith("http") else f"{BASE_URL}{next_href}"
        m = re.search(r"/category/(\d+)/news.*page=(\d+)", next_url)
        if m:
            r.lpush("queue_news_list", json.dumps({"cat_id": int(m.group(1)), "page": int(m.group(2))}))


def crawl_news_detail(news_url: str):
    """第3层：爬取新闻详情，保存到 SQLite"""
    resp = requests.get(news_url, headers=_headers())
    sel = Selector(resp.text)

    title = sel.css("h1::text").get("").strip()
    author = category_name = publish_time = ""
    summary = ""
    content_parts = []

    for p_elem in sel.css("div.content p"):
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

    save_news({
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
    print(f"handwritten 已保存: {title}")


# ========== 手写线程消费函数（手动维护 while 1 + blpop） ==========

def run_crawl_news_list():
    """从队列取 list 任务"""
    while True:
        try:
            _key, msg = r.blpop("queue_news_list", timeout=0)   # ← blpop 取出即删
            data = json.loads(msg)
            crawl_news_list(cat_id=data["cat_id"], page=data["page"])
        except Exception as e:
            print(f"[list] 出错: {e}")    # ← 报错了就打印一下，消息已经丢了


def run_crawl_news_detail():
    """从队列取 detail 任务"""
    while True:
        try:
            _key, msg = r.blpop("queue_news_detail", timeout=0)
            data = json.loads(msg)
            crawl_news_detail(news_url=data["news_url"])
        except Exception as e:
            print(f"[detail] 出错: {e}")   # ← 同上，消息丢了


if __name__ == "__main__":
    init_db()

    # ---- 手写线程池（凭感觉配置） ----
    # 分类：2个线程
    threading.Thread(target=crawl_categories, daemon=False).start()

    # 列表页：5个线程
    for _ in range(5):
        t = threading.Thread(target=run_crawl_news_list, daemon=True)
        t.start()

    # 详情页：20个线程
    for _ in range(20):
        t = threading.Thread(target=run_crawl_news_detail, daemon=True)
        t.start()

    # ---- 没有 Web 管理，没有优雅退出，没有监控 ----
    print("正在启动 handwritten 爬虫...")
    print("警告: 按 Ctrl+C 会丢失正在处理的消息！")
    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        print("程序退出，未确认的消息已丢失...")
