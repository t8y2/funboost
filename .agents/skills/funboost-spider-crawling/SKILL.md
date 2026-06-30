---
name: funboost-spider-crawling
description: 当需要用 funboost 进行 Web 爬虫或数据采集时使用。触发场景：分布式爬虫、URL 调度、funspider、boost_spider、httpx 爬虫。关键词：爬虫, spider, crawl, funspider, SimpleSpiderClient, AsyncSpiderClient, URL 调度, 分布式采集。
compatibility: Python 3.7+, funboost
---

# Funboost 爬虫 / 数据采集

## 概述

Funboost 是**函数调度器**，Scrapy 是 **URL 调度器**——这是二者最本质的差异。

- **Scrapy**：调度 `Request` 对象，框架替你发请求、走 callback 链、Pipeline 存储，用户被框架生命周期束缚。
- **Funboost**：调度**完整的 Python 函数**。框架只负责：何时调用、并发几个、失败怎么办。函数内部写什么代码完全自由。

**核心结论**：Funboost 写爬虫就是「写函数就能爬虫」。加一个 `@boost(BoosterParams(...))` 装饰器，函数自动获得分布式、并发、重试、控频、断点续爬、去重等 30+ 种能力。

**核心原则**：框架只管调度，不插手你怎么发请求、怎么解析、怎么存储。整个 PyPI 都是天然生态，无需 scrapy-xxx 插件。

## 适用场景

- 分布式 Web 爬虫 / 数据采集
- 列表页 → 详情页 → 子任务链式派发
- 需要精准 QPS 控频、多进程/多机器横向扩展
- 短时效 Token、浏览器多轮交互（Playwright/Selenium）
- 外部系统（Java/Go）通过 Redis/HTTP 实时触发爬取
- 函数级重试（HTTP 200 但内容异常也重试）

## 三种爬虫模式

| 模式 | 组成 | 适合场景 |
|------|------|----------|
| **纯 @boost** | `@boost` + 任意 HTTP 库（requests/httpx/playwright）+ 任意存储 | 最大自由，复用现有 `utils/` 工具 |
| **funspider** | `SimpleSpiderClient` / `AsyncSpiderClient` + `SpiderResponse` + `SpiderItem` | ORM 模型驱动、强类型、同步/异步混用 |
| **boost_spider** | `RequestClient` + `SpiderResponse` + `DatasetSink`（独立包 `pip install boost_spider`） | 极简字典流、多代理商容灾 |

三者**都不是必须的**，可自由混搭：`funboost + funspider(SpiderItem) + boost_spider(RequestClient) + your_utils`。

### 模式 1：纯 @boost 函数调度

```python
from funboost import boost, BoosterParams, BrokerEnum

@boost(BoosterParams(
    queue_name='crawl_detail',
    broker_kind=BrokerEnum.REDIS_ACK_ABLE,
    qps=5,
    max_retry_times=3,
))
def crawl_detail(url: str):
    import requests
    resp = requests.get(url, proxies=get_my_proxy(), headers=get_my_headers())
    data = parse_detail(resp.text)
    save_to_mysql(data)

crawl_detail.push(url='https://example.com/article/123')
crawl_detail.consume()
```

### 模式 2：funspider（内置于 funboost）

位于 `funboost/contrib/funspider/`，依赖：`pip install httpx parsel sqlmodel`（及数据库驱动）。

| 组件 | 说明 |
|------|------|
| `SimpleSpiderClient` | 同步 httpx 客户端：自动重试、随机 UA、代理轮换 |
| `AsyncSpiderClient` | 异步 httpx 客户端：适配 `ConcurrentModeEnum.ASYNC` |
| `SpiderResponse` | 响应封装：`.xpath()` / `.css()` / `.re()` / `.re_first()` / `.resp_dict` |
| `SpiderItem` | SQLModel ORM 基类：`upsert()` / `aio_upsert()` / `mongo_upsert()` / `bulk_upsert()` |

### 模式 3：boost_spider（独立三方包）

```bash
pip install boost_spider
```

| 组件 | 说明 |
|------|------|
| `RequestClient` | API 兼容 requests，多代理商容灾轮换、自动重试、Cookie 会话 |
| `SpiderResponse` | `.xpath()` / `.css()` / `.re_search()` |
| `DatasetSink` | 一行代码存 MySQL/PostgreSQL/SQLite/MongoDB，自动建表 |

**funspider vs boost_spider 选型**：

| 维度 | funspider | boost_spider |
|------|-----------|--------------|
| 设计理念 | ORM 辅助、强类型流 | 自由至上、极简字典流 |
| 数据模型 | SQLModel 类，IDE 自动补全 | 纯字典 + `DatasetSink` |
| HTTP 客户端 | httpx（同步+异步双引擎） | 兼容 requests，多代理商容灾 |
| 适合场景 | 大型团队、ORM 管理表结构 | 快速开发、极致简洁 |

## funspider 客户端用法

### SimpleSpiderClient（同步）

```python
from funboost.contrib.funspider import SimpleSpiderClient

def abuyun_proxy():
    return "http://user:pass@proxy.abuyun.com:9020"

def redis_pool_proxy():
    import redis
    r = redis.Redis(host="localhost", port=6379, db=0)
    proxy = r.srandmember("proxy_pool")
    return proxy.decode() if proxy else None

client = SimpleSpiderClient(
    proxy_getter_list=[abuyun_proxy, redis_pool_proxy],  # 轮换代理
    retry_times=3,      # 失败自动重试次数（默认 2）
    timeout=30,         # 超时秒数
    user_agents=None,   # 默认内置 UA 列表，可自定义
)

resp = client.get("https://example.com/page")
resp = client.post("https://api.example.com", json={"key": "val"})
resp = client.request("GET", url, headers={...}, params={...})
client.close()  # 程序结束时关闭连接
```

**SpiderResponse 解析**：

```python
title = resp.css("h1::text").get()
links = resp.css("a.title::attr(href)").getall()
news_id = resp.re_first(r'/news/(\d+)')
items = resp.xpath("//div[@class='item']//text()").getall()
data = resp.resp_dict  # JSON 响应自动解析为 dict
```

### AsyncSpiderClient（异步）

不绑定 Event Loop，可在 funboost `ASYNC` 并发模式自由使用：

```python
from funboost import ConcurrentModeEnum
from funboost.contrib.funspider import AsyncSpiderClient

async_client = AsyncSpiderClient(proxy_getter_list=[abuyun_proxy], retry_times=3)

@boost(BoosterParams(
    queue_name='async_crawl',
    concurrent_mode=ConcurrentModeEnum.ASYNC,
    qps=10,
))
async def crawl_api(news_id: int):
    resp = await async_client.get(f"https://api.example.com/comments/{news_id}")
    for c in resp.resp_dict["comments"]:
        await CommentItem(...).aio_upsert()

# 程序结束时：await async_client.aclose()
```

**注意**：异步任务必须用 `await func.aio_push(...)` 发布，消费函数必须 `async def`。

## SpiderItem 数据模型

继承 `SpiderItem` + `table=True`，绑定数据库引擎和 upsert 去重字段：

```python
from typing import ClassVar, Optional
from funboost.contrib.funspider import SpiderItem, Field, create_engine, create_async_engine

MYSQL_ENGINE = create_engine("mysql+pymysql://root:pass@127.0.0.1:3306/spider_db")
ASYNC_MYSQL_ENGINE = create_async_engine("mysql+aiomysql://root:pass@127.0.0.1:3306/spider_db")

class NewsItem(SpiderItem, table=True):
    __tablename__: ClassVar[str] = "news"
    __engine__ = MYSQL_ENGINE                          # 同步引擎
    __async_engine__ = ASYNC_MYSQL_ENGINE              # 异步引擎（用 aio_upsert 时需要）
    __default_upsert_unique_fields__ = ["news_id"]     # upsert 去重键

    id: Optional[int] = Field(default=None, primary_key=True)
    news_id: int = Field(unique=True)
    title: str = Field(max_length=200)
    url: str = Field(max_length=500)
    content: str

NewsItem.create_table()  # 自动建表，已存在则跳过
```

**入库方法**：

| 方法 | 说明 |
|------|------|
| `.insert()` | 同步插入 |
| `.upsert()` | 同步 upsert（按 `__default_upsert_unique_fields__` 去重，存在则更新） |
| `.bulk_upsert(items)` | 同步批量 upsert |
| `.aio_insert()` / `.aio_upsert()` | 异步版本 |
| `.mongo_upsert()` / `.aio_mongo_upsert()` | MongoDB upsert（需设置 `__mongo_collection__`） |
| `.ensure_mongo_indexes()` | 按去重字段创建 MongoDB 索引 |

```python
NewsItem(news_id=123, title="标题", url="https://...", content="正文").upsert()
await CommentItem(...).aio_upsert()
```

## 分布式爬虫架构

典型架构：**多队列 + Redis ACK 队列 + 多进程/多机器消费**。

```
种子推送 → [news_list 队列] → crawl_list 函数 → push 详情 URL
                                    ↓
              [news_detail 队列] → crawl_detail 函数 → upsert 入库 + push 子任务
                                    ↓
              [news_comments 队列] → crawl_comments 函数（异步）
```

**关键配置**：

```python
from funboost import boost, BoosterParams, BrokerEnum, BoostersManager, enable_ctrl_c_quit_on_windows

CRAWLER_GROUP = "news_crawler"

class NewsCrawlerParams(BoosterParams):
    broker_kind: str = BrokerEnum.REDIS_ACK_ABLE  # ACK 确认，崩溃不丢任务
    booster_group: str = CRAWLER_GROUP            # 消费分组，一键启动

@boost(NewsCrawlerParams(queue_name='news_list', qps=2, do_task_filtering=True))
def crawl_list(page: int): ...

@boost(NewsCrawlerParams(queue_name='news_detail', qps=5, max_retry_times=5))
def crawl_detail(detail_url: str): ...

if __name__ == '__main__':
    BoostersManager.consume_group(CRAWLER_GROUP)  # 一键启动全组消费
    crawl_list.push(page=1)
    # 极限性能：crawl_detail.multi_process_consume(8)  # 8 进程 × concurrent_num 线程
    enable_ctrl_c_quit_on_windows()
```

**横向扩展**：

- **多进程**：`func.multi_process_consume(8)` — 单机 8 核 × 50 线程 = 400 并发
- **多机器**：多台机器运行同一脚本、同一 `queue_name`、同一 Redis，自动竞争消费
- **分布式控频**：`is_using_distributed_frequency_control=True` — 多机器共享 QPS 上限
- **外部触发**：Java/Go 往 Redis 对应 queue 发 JSON（函数入参）即可；或用 `funboost.faas` 暴露 HTTP 接口

**Broker 推荐**：生产爬虫用 `BrokerEnum.REDIS_ACK_ABLE`（消费确认，断点续爬）；开发测试可用 `SQLITE_QUEUE`。

## 去重（do_task_filtering）

基于**函数入参**自动去重（非 URL 字符串指纹），可忽略 URL 中的噪音参数：

```python
@boost(BoosterParams(
    queue_name='news_detail',
    do_task_filtering=True,                   # 开启入参级去重
    task_filtering_expire_seconds=3600 * 24,  # 去重有效期 24 小时（过期后可再次爬取）
))
def crawl_detail(detail_url: str):
    ...
```

- 相同 `detail_url` 在有效期内不会重复执行
- 列表页和详情页可设不同去重有效期（列表 24h，详情 7 天）
- 需要 Redis 支持（框架自动使用 Redis 存储去重键）
- 与 Scrapy URL 指纹去重相比：基于结构化入参，不受 URL 参数顺序/噪音干扰

**链式派发 + 去重**：列表页 `crawl_detail.push(detail_url=url)` 时，若详情页已开启 `do_task_filtering`，重复 URL 自动跳过。

## 完整代码示例（funspider）

参考源码：`funboost/contrib/funspider/funspider_demos/funspider_demo1.py`

```python
import re
from typing import ClassVar, Optional
from funboost import (
    boost, BoosterParams, BoostersManager, BrokerEnum,
    enable_ctrl_c_quit_on_windows, ConcurrentModeEnum,
)
from funboost.contrib.funspider import (
    SimpleSpiderClient, AsyncSpiderClient, SpiderItem,
    create_engine, create_async_engine, Field,
)

NEWS_GROUP = "news_crawler"

class NewsCrawlerParams(BoosterParams):
    broker_kind: str = BrokerEnum.REDIS_ACK_ABLE
    booster_group: str = NEWS_GROUP

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
    content: str
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

NewsItem.create_table()
CommentItem.create_table()

sync_client = SimpleSpiderClient(retry_times=3)
async_client = AsyncSpiderClient(retry_times=3)
BASE_URL = "https://news.example.com"

@boost(NewsCrawlerParams(queue_name="news_list", qps=2))
def crawl_list(page: int):
    resp = sync_client.get(f"{BASE_URL}/list?page={page}")
    for href in resp.css("a.detail::attr(href)").getall():
        crawl_detail.push(detail_url=f"{BASE_URL}{href}")
    if resp.css("a.next-page::attr(href)").get():
        crawl_list.push(page=page + 1)

@boost(NewsCrawlerParams(
    queue_name="news_detail", qps=5, max_retry_times=5,
    do_task_filtering=True, task_filtering_expire_seconds=3600 * 24 * 7,
))
def crawl_detail(detail_url: str):
    resp = sync_client.get(detail_url)
    title = resp.css("h1::text").get("").strip()
    news_id = int(re.search(r"/news/(\d+)", detail_url).group(1))
    if not title:
        raise Exception("标题为空，可能触发反爬")  # 函数级重试
    NewsItem(news_id=news_id, title=title, content=resp.text[:500], url=detail_url).upsert()
    crawl_comments.push(news_id=news_id)

@boost(NewsCrawlerParams(
    queue_name="news_comments", qps=10,
    concurrent_mode=ConcurrentModeEnum.ASYNC,
    do_task_filtering=True, task_filtering_expire_seconds=3600,
))
async def crawl_comments(news_id: int):
    resp = await async_client.get(f"{BASE_URL}/comments/{news_id}")
    for c in resp.resp_dict.get("comments", []):
        await CommentItem(
            comment_id=c["id"], news_id=c["news_id"],
            user=c["user"], content=c["content"],
        ).aio_upsert()

if __name__ == '__main__':
    BoostersManager.consume_group(NEWS_GROUP)
    crawl_list.push(page=1)
    enable_ctrl_c_quit_on_windows()
```

## 铁律（绝对不可违反）

1. **必须使用 `BoosterParams` 对象** — 禁止 `@boost("queue_name", qps=5)` 老式写法
2. **禁止臆造参数名** — 超时用 `function_timeout`，重试用 `max_retry_times`，去重用 `do_task_filtering`
3. **禁止 Celery 思维** — 获取上下文用 `fct`，不用 `self` / `bind=True`
4. **异步模式** — `concurrent_mode=ConcurrentModeEnum.ASYNC` 时必须 `async def` + `await aio_push`
5. **连续启动消费** — `func1.consume(); func2.consume()`，不要用 `threading.Thread` 包装
6. **AI 运行脚本** — 必须设 `PYTHONPATH=项目根目录`，并用 timeout 或 `os._exit()` 终止（`consume()` 永不退出）
7. **禁止 flush Redis** — 去重依赖 Redis，不要清空

## 函数级重试 vs Scrapy URL 级重试

Funboost 函数内**任意位置抛异常**都会触发重试：

```python
@boost(BoosterParams(queue_name='reliable_crawl', max_retry_times=5))
def crawl(url: str):
    resp = requests.get(url)
    data = resp.json()
    if data.get('code') == 'captcha_required':  # HTTP 200 但业务反爬
        raise Exception("触发验证码")  # 自动重试，换 IP 再来
    title = data['result']['title']  # KeyError 也会触发重试
    save(title)
```

Scrapy 仅在 HTTP 请求失败（超时、5xx）时重试；HTTP 200 但内容是验证码或空数据，Scrapy 认为成功，**数据直接丢失**。

## 与 Scrapy 的对比优势

| 维度 | Funboost | Scrapy |
|------|----------|--------|
| 调度核心 | 调度函数（内部完全自由） | 调度 Request（框架控制） |
| 编程范式 | 平铺直叙线性代码 | yield Request + callback 回调链 |
| 项目结构 | 无要求，单文件即可 | 强制 7-8 个文件 |
| HTTP 库 | 任意（requests/httpx/playwright） | 强制 Twisted 下载器 |
| 反爬实现 | 普通 Python 函数，0 门槛 | Downloader Middleware |
| 并发 | 多进程 × 多线程/协程 × 多机器 | 单进程受限 |
| QPS 控频 | 精准 `qps=N`，分布式全局控频 | `DOWNLOAD_DELAY` 不精确 |
| 去重 | 函数入参级，支持有效期 | URL 指纹，噪音参数干扰 |
| 重试 | 函数级（内容异常也重试） | URL 级（仅网络错误） |
| 断点续爬 | ACK 确认，崩溃不丢消息 | scrapy-redis blpop 可能丢消息 |
| 短时效 Token | 函数内连续请求，时序确定 | 调度器排队，Token 易过期 |
| 浏览器交互 | 函数内自然编写，N 实例并发 | Selenium 阻塞 Twisted 事件循环 |
| 外部触发 | Redis JSON / FaaS HTTP | 封闭系统，难以对接 |
| 插件 | 无需，PyPI 所有包直接 import | 依赖 scrapy-xxx 专用插件 |
| Web 管理 | funweb 开箱即用 | 无官方工具 |

**选型建议**：

- 写函数就能爬虫、复用 utils、精准控频、分布式 ACK、外部系统触发 → **Funboost**
- 已有 Scrapy 大型项目且团队熟悉 callback 体系 → 可继续 Scrapy，但新爬虫优先考虑 Funboost

## 最佳实践

### 项目结构

Funboost 不强制目录。推荐**一个网站一个 py 文件**：

```
my_spider_project/
├── utils/my_request.py    # 可选：自封装请求
├── site_news.py           # 列表+详情，同文件
└── run_all.py             # 可选：BoostersManager.consume_group
```

### 精准 QPS + 分布式控频

```python
@boost(BoosterParams(
    queue_name='polite_crawl',
    qps=2,
    is_using_distributed_frequency_control=True,  # 多机器合计不超过 2 QPS
))
def crawl(url: str): ...
```

### 定时爬取种子

```python
from funboost import ApsJobAdder

@boost(BoosterParams(queue_name='seed_scheduler', booster_group=CRAWLER_GROUP))
def push_daily_seeds():
    for cat_id in range(1, 11):
        crawl_list.push(cat_id)

ApsJobAdder(push_daily_seeds, job_store_kind='redis').add_push_job(
    trigger='cron', hour=0, minute=0, id='daily_seeds', replace_existing=True,
)
```

### funweb 可视化管理

```bash
pip install funboost[flask]
python -m funboost.funweb.app  # 浏览器打开 127.0.0.1:27018
```

消费速率 = 爬取速率；支持暂停/恢复、失败重投、积压告警。

## 依赖安装

```bash
pip install funboost

# funspider 按需安装
pip install httpx parsel sqlmodel
pip install pymysql aiomysql        # MySQL
pip install psycopg2-binary         # PostgreSQL

# boost_spider（可选）
pip install boost_spider
```

## 参考资源

| 资源 | 路径 |
|------|------|
| funspider 源码 | `funboost/contrib/funspider/` |
| 完整 demo | `funboost/contrib/funspider/funspider_demos/funspider_demo1.py` |
| 模拟网站（本地测试） | `funboost/contrib/funspider/funspider_demos/fake_news_site.py` |
| 爬虫教程 | `funboost_docs/source/articles/c8.md` |
| 基础任务技能 | `.agents/skills/using-funboost-basics/SKILL.md` |
| Broker 选型 | `.agents/skills/funboost-broker-selection/SKILL.md` |
| 高级重试 | `.agents/skills/funboost-advanced-retry/SKILL.md` |

## 相关 Skill

- `funboost-async-programming` — async/await 异步编程
- `funboost-broker-selection` — Broker 中间件选型
