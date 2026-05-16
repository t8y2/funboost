
# 🕷️ funspider – Funboost 爬虫辅助扩展

funspider 不是爬虫框架——它是基于 funboost 分布式函数调度引擎的爬虫辅助层。funboost 有多强大，funspider 就有多强大。百分之百利用funboost的所有功能,例如50种消息队列 + 5种并发方式 + 30种任务控制功能 + funweb可视化管理 完全可以利用。

## 🧩 funspider + funboost + funweb 三件套

三件套合在一起，就是完整的 **爬虫开发 + 分布式运行 + 可视化管理** 闭环：

| 组件 | 角色 | 核心能力 |
|------|------|----------|
| **funboost** | 调度底座 | 40+消息队列、5种并发模式、QPS、去重、ACK、重试、定时任务（APScheduler） |
| **funspider** | 爬虫辅助 | HTTP客户端（同步+异步）、ORM Item、响应解析、数据入库 |
| **funweb** | 可视化管理 | 任务监控、队列状态、启停控制、告警 |

- **开发**：一行 `@boost` 写爬虫函数，`funspider` 提供 HTTP 客户端和 ORM 入库
- **运行**：`consume_group` 一键拉起，分布式部署，QPS 精确控频
- **管理**：funweb 看队列积压、成功率、失败任务告警
- **周期**：`ApsJobAdder` 定时 push 种子，几行代码搞定周期爬虫

> **基于 `Funboost` 的工程化爬虫辅助组件，提供 ORM 模型与双引擎客户端。**

**`funspider`** 是 `Funboost` 分布式函数调度框架的一个用户贡献扩展。如果说 `boost_spider` 代表着极致的**自由与简洁**，那么 `funspider` 则提供了一种**结构化与强类型**的辅助选择。

它不是 `boost_spider` 的替代品，而是为偏爱 **ORM 模型驱动** 和 **异步协程收发** 的开发者提供的另一种趁手工具。

---

## ✨ 核心定位

- ✅ **范式互补**：`boost_spider` 推崇纯字典流和极致自由；`funspider` 额外提供 SQLModel ORM 封装的选项，为复杂数据关系提供类型安全保障。
- ✅ **双引擎客户端**：基于 `httpx`，内置 `SimpleSpiderClient`（同步）与 `AsyncSpiderClient`（异步），可在同一个爬虫项目中按需混用。
- ✅ **强类型数据模型**：基于 `SQLModel`，支持 `VARCHAR(n)`、索引、外键等精确字段定义，享受 IDE 智能补全与静态检查。
- ✅ **增强响应解析**：`SpiderResponse` 对象内置 `.xpath()`、`.css()`、`.re()` 等方法，无需切换工具即可快速提取数据。
- ✅ **灵活代理接入**：支持传入自定义代理获取函数列表，轻松对接阿布云、快代理等任意商业代理服务。

---

## 📦 安装

`funspider` 代码随 `funboost` 一起发布，但默认不安装其依赖项。

**1. 安装 Funboost**
```bash
pip install funboost
```

**2. 按需安装相关依赖**
```bash
# 安装 funspider 所需的所有依赖
pip install sqlmodel httpx parsel

# 根据需求安装数据库驱动
pip install pymysql aiomysql        # MySQL
pip install psycopg2-binary         # PostgreSQL
```

---

## 🚀 快速上手

以下示例展示了 `funspider` 的核心用法：继承 `BoosterParams` 复用配置、使用强类型 `SpiderItem` 模型入库，以及混用同步和异步客户端。

### 1. 定义数据模型 (ORM)

```python
from funboost.contrib.funspider import SpiderItem, Field, create_engine, create_async_engine

class NewsItem(SpiderItem, table=True):
    __tablename__ = "news"
    __engine__ = create_engine("mysql+pymysql://user:pass@localhost/db")
    __async_engine__ = create_async_engine("mysql+aiomysql://user:pass@localhost/db")
    __default_upsert_unique_fields__ = ["news_id"]

    id: int | None = Field(default=None, primary_key=True)
    news_id: int = Field(unique=True)
    title: str = Field(max_length=200)   # 精确控制 VARCHAR(200)
    url: str = Field(max_length=500)
    content: str                         # TEXT
```

### 2. 编写爬虫函数 (同步 + 异步混用)

```python
from funboost import boost, BoosterParams, BoostersManager, BrokerEnum, ConcurrentModeEnum
from funboost.contrib.funspider import SimpleSpiderClient, AsyncSpiderClient

NEWS_GROUP = "news_crawler"

class NewsCrawlerParams(BoosterParams):
    broker_kind: str = BrokerEnum.REDIS_ACK_ABLE
    booster_group: str = NEWS_GROUP

base_url = "https://example.com"

def abuyun_proxy():
    return "http://user:pass@proxy.abuyun.com:9020"

def redis_pool_proxy():
    import redis
    r = redis.Redis(host="localhost", port=6379, db=0)
    return r.srandmember("proxy_pool")

sync_client = SimpleSpiderClient(proxy_getter_list=[abuyun_proxy, redis_pool_proxy], retry_times=3)
async_client = AsyncSpiderClient(proxy_getter_list=[abuyun_proxy, redis_pool_proxy], retry_times=3)

@boost(NewsCrawlerParams(queue_name="list", qps=2))
def crawl_list(page: int):
    resp = sync_client.get(f"{base_url}/list?page={page}")
    for url in resp.css("a.detail::attr(href)").getall():
        crawl_detail.push(detail_url=url)

@boost(NewsCrawlerParams(queue_name="detail", qps=5))
def crawl_detail(detail_url: str):
    resp = sync_client.get(detail_url)
    title = resp.xpath("//h1/text()").get()
    news_id = int(resp.re_first(r"news/(\d+)"))
    NewsItem(news_id=news_id, title=title, url=detail_url).upsert()
    crawl_comments.push(news_id=news_id)

@boost(NewsCrawlerParams(queue_name="comments", qps=10, concurrent_mode=ConcurrentModeEnum.ASYNC,
                         do_task_filtering=True, task_filtering_expire_seconds=3600))
async def crawl_comments(news_id: int):
    resp = await async_client.get(f"{base_url}/comments/{news_id}")
    for comment in resp.resp_dict["list"]:
        await CommentItem(...).aio_upsert()
```

### 3. 启动消费

```python
if __name__ == "__main__":
    BoostersManager.consume_group(NEWS_GROUP)
    crawl_list.push(page=1)
```

---

## 🔧 进阶配置

### 自定义代理

```python
def abuyun_proxy():
    return "http://user:pass@proxy.abuyun.com:9020"

client = SimpleSpiderClient(proxy_getter_list=[abuyun_proxy])
```

---

## 🆚 与 `boost_spider` 的风格对比

`funspider` 和 `boost_spider` 都是基于 `Funboost` 的生产级爬虫解决方案。核心差异在于**设计哲学和开发范式**，而非能力强弱：

| 特性 | `boost_spider` | `funspider` |
|------|----------------|------------|
| **设计理念** | **自由至上、极简字典流**。以最原生、最直接的方式让开发者掌控一切。 | **ORM 辅助、强类型流**。为习惯使用 ORM 模型管理数据的开发者提供便利封装。 |
| **数据模型** | 纯 Python 字典。开发者可完全自定义如何建表和校验（如手写 DDL 或结合 SQLAlchemy）。 | SQLModel 模型类。将数据定义、字段校验和数据库同步集成在类属性中。 |
| **字段控制** | 灵活。你完全控制建表语句，想约束什么字段长度和索引都行。 | 直观。在 ORM 模型中声明 `Field(max_length=200)`，IDE 自动补全。 |
| **HTTP 客户端** | 同步 `RequestClient`，内置丰富代理、重试功能。 | 同步 + 异步双客户端，基于 `httpx`。 |
| **代理配置** | 对象化配置，优雅简洁。 | 函数式注入，灵活自由。 |
| **开发偏好** | 喜欢直接、轻量、完全掌控的纯粹 Python 体验。 | 偏好在大型项目中通过 ORM 标准管理数据库结构和关系。 |
| **生产环境** | ✅ **完全胜任**，性能卓越，久经考验。 | ✅ **完全胜任**，结构清晰，便于团队协作。 |

**选型建议**：
-   如果你喜欢 `funboost` 那种“不加修饰、直接赋能”的爽快感，**`boost_spider`** 是无脑首选。
-   如果你所在团队重度使用 SQLAlchemy/SQLModel，且希望爬虫的数据模型也能无缝融入项目 ORM 体系，**`funspider`** 会是更顺手的选择。

---

## 📖 完整示例

参见源码目录下的演示文件：
- 入口文件：`funspider/funspider_demos/funspider_demo1.py`
- 模拟网站：`funspider/funspider_demos/fake_news_site.py`

演示内容：
- 新闻列表页（同步） → 详情页（同步） → 评论页（异步）
- 同步/异步客户端混用
- SQLModel 数据入库

---

## 🧠 设计哲学

`funspider` 提供的仅仅是 `SpiderItem`, `SpiderResponse`, `SimpleSpiderClient`, `AsyncSpiderClient` 这几个**辅助类**。

真正的核心竞争力——分布式调度、QPS 控频、自动重试、断点续传——完全由 **`Funboost`** 核心引擎驱动。

我们希望你的爬虫代码是平铺直叙的函数，而不是层层嵌套的回调。