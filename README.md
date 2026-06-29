

# 1. Python 分布式函数调度平台 Funboost 简介

[![pZf68L6.png](https://s41.ax1x.com/2026/01/30/pZf68L6.png)](https://imgchr.com/i/pZf68L6)

**Funboost** — 一行 `@boost` 装饰器，让 Python 函数获得 40+ 种消息队列 + 分布式调度 + FaaS 微服务的能力。以下是您的核心学习资源导航：

| 资源类型 | 链接地址 | 说明 |
| :--- | :--- | :--- |
| ⚡ **快速预览** | [👉 点击查看演示](https://ydf0509.github.io/funboost_git_pages/funboost_promo.html) | 直观感受框架运行效果 |
| 📖 **完全教程** | [👉 ReadTheDocs](https://funboost.readthedocs.io/zh-cn/latest/index.html) | 包含原理、API 与进阶用法 |
| 🤖 **AI 助教** | [👉 AI 学习指南](https://funboost.readthedocs.io/zh-cn/latest/articles/c14.html) | **[必读]** 利用 AI 掌握框架的最佳捷径 |
| 📄 **超级 AI 上下文文档** | [👉 funboost_all_docs_and_codes.md](https://github.com/ydf0509/funboost/blob/master/funboost_all_docs_and_codes.md) | 约 900K 上下文，包含 Rules、Skills、完整教程、源码和使用 Demo，直接投喂给 AI 即可让它帮你写代码 |

## 1.0 funboost 框架说明介绍

**Funboost** 用一行 `@boost` 即可为项目中任意函数接入分布式调度、队列与 FaaS 等能力；宏观定位与典型场景见下文 **1.0.4**。

**Funboost 的核心价值主张：把复杂留给框架，把简单留给用户。**

<iframe src="https://ydf0509.github.io/funboost_git_pages/index2.html" width="100%" height="2400" style="border:none;"></iframe>

<h4>📹 观看 funboost 视频</h4>
<video controls width="800" 
      src="https://ydf0509.github.io/funboost_git_pages/%E8%A7%86%E9%A2%91-Funboost_%E8%A7%86%E9%A2%91.mp4">
   您的浏览器不支持视频播放。
</video>

<h4>🎧 收听 funboost 音频</h4>
<audio controls 
      src="https://ydf0509.github.io/funboost_git_pages/%E9%9F%B3%E9%A2%91-funboost_%E9%9F%B3%E9%A2%91.mp4">
   您的浏览器不支持音频播放。
</audio>

### 1.0.1 funboost 示意图

#### 1.0.1.1 funboost 运行流程图

funboost 采用经典的 **生产者 → Broker → 消费者** 架构模型，并支持可选的 RPC 模式（消费者 → 生产者）。

虽然 funboost 的功能丰富度远超 scrapy 等专业框架，但其架构设计却保持了极致的简洁性，核心流程一目了然。

![funboost 运行流程图](img_95.png)

#### 1.0.1.2 funboost 功能思维导图

funboost使用极其简单，只有一行@boost，但是用户能想得到的功能全都有。良好的软件设计架构，以致funboost框架可以扩展无限可能。

从funboost 思维导图来看，funboost支持 40+ 种消息队列支持、30+ 种任务控制功能、所有python并发模式、rpc、微批消费、cdc事件驱动、 funboost管理可视化、分布式定时任务、faas 热加载、workflow任务编排、funspider和boost_spider爬虫、promethus指标监控、opentelemetry全链路任务追踪等， 适用范围顶python编程半边天。

思维导图图片分辨率大，建议下载保存，用本地图片软件查看。
<!-- ![funboost 功能思维导图](img_94.png) -->
![funboost 功能思维导图](mermaid-diagram0311e.png)

### 1.0.2 快速了解和上手funboost，直接看 1.3 章节例子

### 1.0.3 funboost 框架安装方式  

```shell
pip install funboost --upgrade  

或 pip install funboost[all]  #一次性安装所有小众三方中间件  
```  

### 1.0.4 funboost 核心能力与适用场景

`funboost` 通过一行 `@boost` 装饰器，将普通函数升级为分布式计算单元。功能是**重量级**的，使用方式却是**极致轻量级**的——只有 `@boost` 一行代码需要写。99% 用过 funboost 的用户核心感受是：**方便、高速、强大、自由**。

无论新老项目，Funboost 都能无缝融入，提供以下核心能力：

*   🌐 **需要分布式？**
    没问题！Funboost 支持 **40+种** 消息队列中间件。只要是叫得上名字的 MQ（甚至包括数据库、文件系统），它都能支持。

*   ⚡ **需要 FaaS (Function as a Service)？**
    **这是亮点！** 借助 `funboost.faas`，您可以一键将普通函数转化为 HTTP 微服务接口。函数自动发现，发布消息、获取结果、管理任务，瞬间完成 Serverless 般的体验。

*   🚀 **需要并发？**
    满足你！Python 所有的并发模式（**线程、协程、多进程**）任你选择，甚至支持它们**叠加使用**，榨干 CPU 性能。

*   🛡️ **需要可靠性？**
    稳如泰山！**消费确认 (ACK)**、自动重试、死信队列 (DLQ)、断点续爬... 即使服务器宕机，任务也绝不丢失。

*   🎛️ **需要控制力？**
    如臂使指！**精准 QPS 控频**、分布式限流、定时任务、延时任务、超时熔断、任务过滤... 给您三十多种控制武器。

*   📊 **需要监控？**
    一目了然！开箱即用的 **funweb (Funboost Web Manager)**，让您对任务状态、队列积压、消费者实例等信息了如指掌。

*   🦅 **需要自由？**
    零侵入！它不绑架您的代码，不强管您的项目结构。**随时能用，随时能走**，还您最纯粹的 Python 编程体验。

### 1.0.5 延伸阅读：如何理解 Funboost、是否值得投入

边界与定位难用一句话概括，**[发散性阐述见文档 6.0b 章节](https://funboost.readthedocs.io/zh-cn/latest/articles/c6.html#b-funboost)**；学习是否值得花时间，**[详见文档 6.0 章节评估](https://funboost.readthedocs.io/zh-cn/latest/articles/c6.html#funboost)**。


### 1.0.6 Funboost 与 Celery 的理念区别

> **核心比喻**：
> `funboost` 与 `celery` 的关系，如同 **iPhone** 与 **诺基亚塞班**。
> 它们的核心功能虽都是通讯（任务调度），但不能因为功能重叠就判定为重复造轮子。正如 iPhone 重新定义了手机，**Funboost 正在重新定义分布式任务调度，让“框架奴役”成为历史。**

**1. 共同点**
两者本质上都是基于分布式消息队列的异步任务调度框架，遵循经典的编程思想：
*   `生产者 (Producer)` -> `中间件 (Broker)` -> `消费者 (Consumer)`

**2. 核心区别**

| 维度 | **Celery (重型框架)** | **Funboost (函数增强器)** |
| :--- | :--- | :--- |
| **设计理念** | **框架奴役**：代码需围绕 Celery 的架构和 App 实例组织。 | **自由赋能**：非侵入式设计，为任意函数插上分布式的翅膀。 |
| **一等公民** | `Celery App` 实例 (Task 是二等公民) | **用户函数** (无需关注 App 实例) |
| **核心语法** | 需定义 App，使用 `@app.task` | 直接使用 **`@boost`** 装饰器 |
| **易用性** | 需规划特定的项目结构，上手门槛较高。 | 极简，任意位置的新旧函数加上装饰器即可用。 |
| **性能表现** | 传统性能基准。 | **断层式领先**：发布性能是 Celery 的 **22倍**，消费性能是 **46倍**。 |
| **功能广度** | 支持主流中间件。 | 支持 **40+** 种中间件，拥有更多精细的任务控制功能。 |
| **AI 辅助编程** | 官方文档需人工亲自阅读，学习成本高。 | **超级 AI 上下文文档**：`funboost_all_docs_and_codes.md`<br>（约 900K 上下文），可直接投喂给 AI，让 AI 帮你写代码、解答问题，无需吃苦看文档。 |


### 1.0.7 Funboost 支持的并发模式

`funboost` 全面覆盖 Python 生态下的并发执行方式，并支持灵活的组合叠加：

*   **基础并发模式**：支持 `threading` (多线程)、`asyncio` (异步IO)、`gevent` (协程)、`eventlet` (协程) 以及 `单线程` 模式。
*   **叠加增强模式**：支持 **多进程 (Multi-Processing)** 与上述任一细粒度并发模式（如多线程或协程）进行叠加，最大限度利用多核 CPU 资源。

### 1.0.8 Funboost 支持的消息队列中间件 (Broker)

得益于强大的架构设计，在 `funboost` 中 **“万物皆可为 Broker”**。不仅涵盖了传统 MQ，更拓展了数据库、网络协议及第三方框架。

*   **传统消息队列**：RabbitMQ, Kafka, NSQ, RocketMQ, MQTT, NATS, Pulsar 等。
*   **数据库作为 Broker**：
    *   **NoSQL**: Redis (支持 List, Pub/Sub, Stream 等多种模式), MongoDB.
    *   **SQL**: MySQL, PostgreSQL, Oracle, SQL Server, SQLite (通过 SQLAlchemy/Peewee 支持).
*   **网络协议直连**：TCP, UDP, HTTP, gRPC (无需部署 MQ 服务即可实现队列通信)。
*   **文件系统**：本地文件/文件夹, SQLite (适合单机或简单场景).
*   **事件驱动 (CDC)**：支持 **MySQL CDC** (基于 Binlog 变更捕获)，使 Funboost 具备了事件驱动能力，设计理念远超传统任务队列。
*   **第三方框架集成**：可直接将 Celery, Dramatiq, Huey, RQ, Nameko 等框架作为底层 Broker，利用 Funboost 的统一接口调度它们的核心。


### 1.0.9 **funboost 学习难吗?**

**答案是：极易上手。Funboost 是"反框架"的框架。**

*   🎯 **核心极简**
    整个框架只需要掌握 **`@boost`** 这一个装饰器及其入参（`BoosterParams`）。所有的用法几乎都遵循 **1.3 章节** 示例的模式，一通百通。

*   🔄 **进退自如（双模运行）**
    加上 `@boost` 装饰器后，你的函数依然保持纯洁：
    *   调用 `fun(x, y)`：**直接运行函数**（同步执行，不经过队列）。
    *   调用 `fun.push(x, y)`：**发送到消息队列**（分布式异步执行）。

*   🤖 **面向 AI 编程的超级 AI 上下文文档**
    Funboost 提供了 **`funboost_all_docs_and_codes.md`**（约 900K 上下文），可直接投喂给 AI（如 DeepSeek、Gemini 等百万上下文模型），实现极致的 AI 辅助编程体验。

👉 *关于"Funboost 学习和使用难吗？"的详细深度回答，请参阅文档 **`6.0.c`** 章节。*


### 1.0.10 📊 监控与口碑

**可视化管理**：Funboost 内置 **funweb (Funboost Web Manager)**，支持队列积压、消费者状态等核心指标监控，开箱即用。

**用户口碑**：**95% 的用户**初步使用后表示"相见恨晚"，核心评价：**极致自由、零侵入、简单强大**。

## 1.1 📚 核心资源与文档导航

### 1.1.1 📝 项目文档入口

> **🚀 快速上手指南**
>
> *   **文档说明**：文档篇幅较长，主要包含原理讲解与框架对比（`How` & `Why`）。
> *   **学习捷径**：**您只需要重点学习 [1.3 章节] 的这 1 个例子即可！** 其他例子仅是修改 `@boost` 装饰器中 `BoosterParams` 的入参配置。
> *   **核心要点**：`funboost` 极其易用，仅需掌握一行 `@boost` 代码。
> *   **🤖 AI 辅助**：强烈推荐阅读 **[第 14 章]**，学习如何利用 AI 大模型快速掌握 `funboost` 的用法。

**🔗 在线文档地址**：[ReadTheDocs - Funboost Latest](https://funboost.readthedocs.io/zh-cn/latest/index.html)
**超级 AI 上下文文档**：[funboost_all_docs_and_codes.md](https://github.com/ydf0509/funboost/blob/master/funboost_all_docs_and_codes.md)

#### 📖 文档章节速览

| 🔰 基础入门 & 核心概念 | 🚀 进阶功能 & 场景实战 | 🤖 AI & 参考资料 |
| :--- | :--- | :--- |
| [1. funboost 框架简介](https://funboost.readthedocs.io/zh-cn/latest/articles/c1.html) | [4b. 代码示例 (**高级进阶**)](https://funboost.readthedocs.io/zh-cn/latest/articles/c4b.html) | [**14. AI 辅助学习指南 (必读)**](https://funboost.readthedocs.io/zh-cn/latest/articles/c14.html) |
| [2. funboost 对比 Celery](https://funboost.readthedocs.io/zh-cn/latest/articles/c2.html) | [8. 爬虫实战：自由编程 vs 框架奴役](https://funboost.readthedocs.io/zh-cn/latest/articles/c8.html) | [6. 常见问题 Q&A](https://funboost.readthedocs.io/zh-cn/latest/articles/c6.html) |
| [3. 框架详细介绍](https://funboost.readthedocs.io/zh-cn/latest/articles/c3.html) | [9. 轻松远程服务器部署](https://funboost.readthedocs.io/zh-cn/latest/articles/c9.html) | [10. 常见报错与问题反馈](https://funboost.readthedocs.io/zh-cn/latest/articles/c10.html) |
| [4. **各种代码示例 (核心)**](https://funboost.readthedocs.io/zh-cn/latest/articles/c4.html) | [11. 集成第三方框架 (Celery/Kombu等)](https://funboost.readthedocs.io/zh-cn/latest/articles/c11.html) | [7. 更新记录](https://funboost.readthedocs.io/zh-cn/latest/articles/c7.html) |
| [5. 运行时截图展示](https://funboost.readthedocs.io/zh-cn/latest/articles/c5.html) | [12. 命令行控制台支持](https://funboost.readthedocs.io/zh-cn/latest/articles/c12.html) | [20. 框架中心思想](https://funboost.readthedocs.io/zh-cn/latest/articles/c20.html) |
| | [13. funweb 可视化管理](https://funboost.readthedocs.io/zh-cn/latest/articles/c13.html) | |
| | [⚡ **15. FaaS Serverless 微服务 (战略级核心)**](https://funboost.readthedocs.io/zh-cn/latest/articles/c15.html) | |

---

### 1.1.2 📦 源码与依赖

*   **GitHub 项目主页**：[ydf0509/funboost](https://github.com/ydf0509/funboost)
*   **nb_log 日志文档**：[NB-Log Documentation](https://nb-log-doc.readthedocs.io/zh_CN/latest/articles/c9.html#id2)
   
---

## 1.2 框架功能介绍  

本节用示意图、与线程池的对比以及 **1.2.2 任务控制功能矩阵** 展开能力细节；框架总体定位与适用场景已在上文 **1.0.4** 说明。

**funboost示图：**  
![funboost示图](https://s21.ax1x.com/2024/04/29/pkFFghj.png)

**也就是这种非常普通的流程图,一样的意思**  
![funboost示图](https://s21.ax1x.com/2024/04/29/pkFFcNQ.png)

### 1.2.1 🆚 对比：Funboost 取代传统线程池

以下两种方式均实现 **10并发** 运行函数 `f`。Funboost 更加简洁且具备扩展性。

#### ❌ 方式 A：手动开启线程池 (传统)
```python
import time
from concurrent.futures import ThreadPoolExecutor

def f(x):
    time.sleep(3)
    print(x)

pool = ThreadPoolExecutor(10)

if __name__ == '__main__':
    for i in range(100):
        pool.submit(f, i)
```

#### ✅ 方式 B：Funboost @boost 模式 (推荐)
```python
import time
from funboost import boost,BoosterParams, BrokerEnum

# 仅需一行装饰器，即可获得 10 线程并发 + 消息队列能力
@boost(BoosterParams(queue_name="test_insteda_thread_queue", 
               broker_kind=BrokerEnum.MEMORY_QUEUE, 
               concurrent_num=10, 
               is_auto_start_consuming_message=True))   
def f(x):
    time.sleep(3)
    print(x)

if __name__ == '__main__':
    for i in range(100):
        f.push(i)
```

####  ✅ 方式 C：FunboostPool 模式 

`FunboostPool` 完美平替 `concurrent.futures.ThreadPoolExecutor`，只需要替换一行实例化代码，无任何负担，兼容用户老项目到极致了。

详见教程 4.38章节 `## 4.38 MemoryFunboostPool 和 FunboostPool 的使用`

```python
from funboost import MemoryFunboostPool,FunboostPool
pool = MemoryFunboostPool(10,) # 完美支持submit 和map，入参和返回类型一致。
future = pool.submit(task_fun, 1, 2) # future类型是 concurrent.futures.Future 。
print(future.result()) # 一样能通过future获取结果
```

### 1.2.2 🚀 任务控制功能矩阵

Funboost 将分布式系统的复杂性封装于内核，向下屏蔽基础设施差异，向上提供标准化的调度原语。以下是框架核心能力的 **7 维全景视图**：

#### 🌌 维度一：连接与架构 (Connectivity & Architecture)

| 能力模块 | 技术特性说明 |
| :--- | :--- |
| **Broker 适配** | **40+ 协议支持**：RabbitMQ, Kafka, RocketMQ, Pulsar, NATS, Redis (List/Stream/PubSub), SQL/NoSQL, 文件系统, TCP/UDP/HTTP。 |
| **FaaS 微服务** | **自动路由**：通过 `funboost.faas`，消费函数自动注册为 FastAPI/Flask/Django 接口；支持 **服务发现** 与 **热更新**。 |
| **CDC 事件驱动** | **Binlog 监听**：支持 `MYSQL_CDC`，实现数据库变更实时触发函数执行，轻量级替代 Canal/Flink 组件。 |
| **框架托管** | **无缝兼容**：支持接管 Celery, Dramatiq, RQ, Huey 等框架作为底层驱动，统一上层 API。 |
| **异构通信** | **多协议支持**：支持 gRPC 双向通信与 MQTT 物联网协议集成。 |

#### ⚡ 维度二：并发与吞吐 (Concurrency & Throughput)

*   **混合并发模型**：原生支持 `Threading`、`Gevent`、`Eventlet`、`Asyncio` (原生事件循环)、`Single_thread` 五种模式。
*   **多进程叠加**：支持 `mp_consume(n)`，在上述并发模式之上叠加 **多进程**，突破 GIL 限制，充分利用多核 CPU。
*   **微批处理 (Micro-Batch)**：提供 `MicroBatchConsumerMixin`，支持自动缓冲聚合单条消息进行批量处理（如批量 DB 写入），显著提升 I/O 吞吐。
*   **零拷贝模式**：内存队列支持 `Ultra-Fast` 模式，跳过序列化开销，实现进程内微秒级通信。

#### 🛡️ 维度三：可靠性保障 (Reliability)

*   **心跳级 ACK**：基于消费者心跳检测的 ACK 机制。可识别进程僵死或崩溃，**秒级**回收并重发未确认任务，避免长耗时任务被误判。
*   **异常重试**：支持指数退避策略，支持针对特定异常类型的重试配置。
*   **死信队列 (DLQ)**：重试耗尽或捕获特定异常后，自动将消息移交死信队列，保障现场数据不丢失。
*   **全量持久化**：支持将函数入参、执行结果、耗时、异常堆栈自动持久化至 MongoDB/MySQL，实现数据可回溯。
*   **多维监控告警**：内置 **5 种告警方式**（告警 Mixin、熔断器钩子、Prometheus 指标、Mongo 轮询、ELK 日志），支持按连续失败次数或滑动窗口错误率触发告警。
    *   **告警通道**：钉钉、企业微信、飞书、Webhook 等；任务恢复后自动发送恢复通知，形成故障闭环。详见文档 **6.30 章节**。

#### 🕹️ 维度四：流量治理 (Traffic Governance)

*   **精准控频 (QPS)**：原生支持从极低频（0.00001次/秒）到高频（50000次/秒）的 **QPS 速率限制**，以**匀速间隔**的方式执行任务。
*   **周期额度 (Quota)**：支持在指定周期（如1分钟）内限制任务执行的**总次数**，任务可**随到随执行**（非匀速）。例如：设置"每分钟最多执行100次"，100次额度用完后将等待下一周期。此功能用法详见 **4b.12 章节**。
*   **分布式限流**：基于funboost的Redis 心跳信息协调，实现跨服务器、跨容器的 **全局流量控制**。
*   **分组消费**：支持 `consume_group`，按业务组别启动消费者，实现大单体应用的资源隔离。
*   **手动熔断管理**：支持运行时动态下发指令，实时 **暂停/恢复** 指定队列的消费。
*   **自动熔断管理**：使用CircuitBreakerConsumerMixin扩展，支持自动熔断、半开、恢复，支持阻塞模式和降级模式。
*   **批处理流控**：提供 `wait_for_possible_has_finish_all_tasks`，支持脚本级的**任务清空等待**。

#### 🎼 维度五：调度与编排 (Scheduling & Orchestration)

*   **Workflow 编排**：内置声明式编排原语，支持 **Chain (串行)**、**Group (并行)**、**Chord (回调)** 模式。
*   **分布式定时**：集成 `APScheduler`，支持 Crontab/Interval/Date 触发器，利用分布式锁防止多实例重复执行。
*   **延时任务**：原生支持 `countdown` (相对时间) 和 `eta` (绝对时间) 的延迟调度。
*   **任务去重**：基于函数入参指纹进行去重（支持 TTL 有效期），屏蔽 URL 随机参数干扰。

#### 🔭 维度六：可观测性 (Observability)

*   **链路追踪**：原生集成 **OpenTelemetry**，支持接入 Jaeger/SkyWalking，自动注入 Context 实现跨组件全链路追踪。
*   **指标监控**：内置 **Prometheus** Exporter，支持 Pull 和 PushGateway 模式，通过 Grafana 展示实时指标。
*   **Web 控制台**：自带可视化管理界面，支持查看积压量、QPS 曲线、消费者元数据
*   **远程运维**：支持 `RemoteTaskKiller` 终止执行中的任务；支持 `fabric_deploy` 代码热部署；funweb 支持脚本部署、进程监控、日志查看与检索。

#### 🧬 维度七：开发体验 (Developer Experience)

*   **FCT 上下文**：提供 `from funboost import fct` 全局对象，在函数调用链任意位置获取 TaskID、重试次数等元数据。
*   **全语法支持**：完整支持 **类方法 (classmethod)**、**实例方法 (instance method)**、**异步函数 (async def)** 作为消费主体。
*   **生命周期 Hook**：提供 `consumer_override_cls` 接口，支持重写消息清洗、结果回调等核心逻辑，兼容 **非标准格式消息**，**支持重写任何任意父类方法**。
*   **对象传输**：支持 Pickle 序列化选项，允许直接传递自定义 Python 对象作为任务参数。
*   **超级装饰器**： 即使用户不需要分布式和消息队列，也可以使用 `@boost` 装饰器配合 **MEMORY_QUEUE** 模式，一个@boost装饰器就能实现并发控制、QPS 限流、自动重试、任务去重等 10+ 种功能，抵得上 10 个常规装饰器叠加使用。

## 1.3 🚀 快速上手：你的第一个 Funboost 程序

> **⚠️ 环境准备 (重要)**
>
> 在运行代码前，请确保您了解 **`PYTHONPATH`** 的概念。
> Windows cmd 或 Linux 运行时，建议将 `PYTHONPATH` 设置为项目根目录，以便框架自动生成或读取配置。
> 👉 [点击学习 PYTHONPATH](https://github.com/ydf0509/pythonpathdemo)

### 1.3.1 ✨ Hello World：最简单的任务调度

这个例子演示了如何将一个普通的求和函数变成分布式任务。

**代码逻辑说明：**
1.  **定义任务**：使用 `@boost` 装饰器，指定队列名 `task_queue_name1` 和 QPS `5`。
2.  **发布任务**：调用 `task_fun.push(x, y)` 发送消息。
3.  **消费任务**：调用 `task_fun.consume()` 启动后台线程自动处理。

```python
import time
from funboost import boost, BrokerEnum, BoosterParams

# 核心配置：使用本地 SQLite 作为消息队列，QPS 限制为 5
@boost(BoosterParams(
    queue_name="task_queue_name1", 
    qps=5, 
    broker_kind=BrokerEnum.SQLITE_QUEUE
))
def task_fun(x, y):
    print(f'{x} + {y} = {x + y}')
    time.sleep(3)  # 模拟耗时，框架会自动并发绕过阻塞
    return x + y

if __name__ == "__main__":
    # 1. 生产者：发布 100 个任务
    print(task_fun(10,20)) # 即使task_fun加了@boost装饰器，task_fun函数仍能直接本地调用，函数入参不会发到消息队列。这就是双模运行。
    for i in range(100):
        task_fun.push(i, y=i * 2) # 发布消息 {"x":i,"y":i*2} 到消息队列task_queue_name1 中。
    
    # 2. 消费者：启动循环调度
    task_fun.consume()
```

> **💡 Tips**
> 如果在 Linux/Mac 上使用 `SQLITE_QUEUE` 报错 `read-only`，请在 `funboost_config.py` 中修改 `SQLLITE_QUEUES_PATH` 为有权限的目录（详见文档 10.3）。

**运行效果截图：**

**发布任务截图：**
![发布截图](https://s21.ax1x.com/2024/04/29/pkFkP4H.png) 

**消费任务截图：**
![消费截图](https://s21.ax1x.com/2024/04/29/pkFkCUe.png)



### 1.3.2 ⚡ 异步 (asyncio) 模式

如果你的消费函数是 `async def`，可以开启 `ConcurrentModeEnum.ASYNC` 并发模式，配合 `aio_push` 发布消息。

```python
import asyncio
from funboost import boost, BrokerEnum, BoosterParams, ConcurrentModeEnum,AioAsyncResult

@boost(BoosterParams(
    queue_name='async_demo_queue',
    qps=10,
    concurrent_mode=ConcurrentModeEnum.ASYNC,  # 切换为 asyncio 并发
    broker_kind=BrokerEnum.REDIS_ACK_ABLE,
    is_using_rpc_mode=True
))
async def async_task(x: int, y: int):
    await asyncio.sleep(0.5)  # 模拟异步 IO
    return x + y

async def main():
    # 异步发布，直接返回 AioAsyncResult
    aio_result:AioAsyncResult = await async_task.aio_push(10, 20)
    result = await aio_result.result  # await 获取 RPC 结果
    print(f'异步结果: {result}')

if __name__ == '__main__':
    async_task.consume()  # 非阻塞启动消费
    asyncio.run(main())
```

> **💡 要点**
> - 消费函数必须为 `async def`，且设置 `concurrent_mode=ConcurrentModeEnum.ASYNC`
> - 发布用 `await func.aio_push()`，获取结果用 `await aio_result.result`
> - 不需要 RPC 结果时，可去掉 `is_using_rpc_mode=True`，直接 `await func.aio_push()` 即可

### 1.3.3 🔥 进阶实战：RPC、定时任务与丝滑连招

这是一个集大成的例子，展示了 Funboost 的核心能力：
*   ✅ **参数复用**：继承 `BoosterParams` 减少重复代码。
*   ✅ **RPC 模式**：发布端同步获取消费结果。
*   ✅ **丝滑启动**：非阻塞连续启动多个消费者。
*   ✅ **定时任务**：基于 `APScheduler` 的强大定时能力。

```python
import time
from funboost import boost, BrokerEnum, BoosterParams, enable_ctrl_c_quit_on_windows, ConcurrentModeEnum, ApsJobAdder

# 1. 定义公共配置基类，减少重复代码
class MyBoosterParams(BoosterParams):
    broker_kind: str = BrokerEnum.REDIS_ACK_ABLE
    max_retry_times: int = 3
    concurrent_mode: str = ConcurrentModeEnum.THREADING 

# 2. 消费函数 step1：演示 RPC 模式
@boost(MyBoosterParams(
    queue_name='s1_queue', 
    qps=1,   
    is_using_rpc_mode=True  # 开启 RPC，支持获取结果
))
def step1(a: int, b: int):
    print(f'step1: a={a}, b={b}')
    time.sleep(0.7)
    # 函数内部可以继续发布任务给 step2
    for j in range(10):
        step2.push(c=a+b+j, d=a*b+j, e=a-b+j)
    return a + b

# 3. 消费函数 step2：演示参数覆盖
@boost(MyBoosterParams(
    queue_name='s2_queue', 
    qps=3, 
    max_retry_times=5  # 覆盖基类默认值
)) 
def step2(c: int, d: int, e: int=666):
    time.sleep(3)
    print(f'step2: c={c}, d={d}, e={e}')
    return c * d * e

if __name__ == '__main__':
    # --- 启动消费 ---
    step1.consume()  # 非阻塞启动
    step2.consume()
    step2.multi_process_consume(3) # 叠加 3 个进程并发

    # --- RPC 调用演示 ---
    async_result = step1.push(100, b=200)
    print('RPC 结果：', async_result.result)  # 阻塞等待结果

    # --- 批量发布演示 ---
    for i in range(100):
        step1.push(i, i*2)
        # publish 方法支持更多高级参数（如 task_id）
        step1.publish({'a':i, 'b':i*2}, task_id=f'task_{i}')

    # --- 定时任务演示 (APScheduler) ---
    # 方式1：指定日期执行
    ApsJobAdder(step2, job_store_kind='redis', is_auto_start=True).add_push_job(
        trigger='date', run_date='2025-06-30 16:25:40', args=(7, 8, 9), id='job1'
    )
    # 方式2：间隔执行
    ApsJobAdder(step2, job_store_kind='redis').add_push_job(
        trigger='interval', seconds=30, args=(4, 6, 10), id='job2'
    )

    # enable_ctrl_c_quit_on_windows使windows能ctrl+c退出，这是非必须的，不加也可以。
    enable_ctrl_c_quit_on_windows()
```

> **🧠 设计哲学**
> Funboost 提倡 **“反框架”** 思维：你才是主角，框架只是插件。
> `task_fun(1, 2)` 是直接运行函数，`task_fun.push(1, 2)` 才是发布到队列。
> 随时可以拿掉 `@boost`，代码依然是纯粹的 Python 函数。

---

### 1.3.4 ✂️ 极简写法：省略 `@boost`

如果你追求极致简洁，也可以直接使用 `@BoosterParams` 作为装饰器，效果等同于 `@boost(BoosterParams(...))`。

```python
# 极简写法
@BoosterParams(queue_name="task_queue_simple",qps=5)
def task_fun(a, b):
    return a + b
```

### 1.3.5 ❌ 过时写法： 直接在 @boost传各种配置入参，不推荐
这种直接在 `@boost`传参，而不使用 `BoosterParams`来传各种配置，是过气写法不推荐，因为不能代码补全了。   
```python
# ⚠️ 反例：过时写法，不推荐！
@boost(queue_name="task_queue_simple",qps=5)
def task_fun(a, b):
    return a + b
```



## 🖥️ funweb (Funboost Web Manager) 界面预览

可视化管理后台提供了强大的监控与运维能力，以下是核心功能截图：

函数消费结果：可查看和搜索函数实时消费状态和结果  
[![函数结果表](https://s41.ax1x.com/2025/12/19/pZ1L5h4.png)](https://imgchr.com/i/pZ1L5h4)

队列操作：查看和操作队列，包括清空、暂停消费、恢复消费
[![队列操作1](https://s41.ax1x.com/2025/12/17/pZlrYPH.png)](https://imgchr.com/i/pZlrYPH)
[![队列操作2](https://s41.ax1x.com/2025/12/17/pZlrUxI.png)](https://imgchr.com/i/pZlrUxI)

队列操作：查看消费曲线图，查看各种消费指标（历史运行次数、失败次数、近10秒完成/失败、平均耗时、剩余消息数量等）  
[![队列消费曲线](https://s41.ax1x.com/2025/12/19/pZ104HS.png)](https://imgchr.com/i/pZ104HS) 

RPC调用：在网页上对30种消息队列发布消息并获取函数执行结果；可根据task_id获取结果  
[![rpc调用成功-绿色](https://s41.ax1x.com/2025/12/19/pZ10RjP.png)](https://imgchr.com/i/pZ10RjP)

定时任务管理：列表页  
[![定时任务列表](https://s41.ax1x.com/2025/12/17/pZlrNRA.png)](https://imgchr.com/i/pZlrNRA)

## 1.4 💡 为什么 Python 极其需要分布式函数计算？

Python 受限于 **GIL（全局解释器锁）**，单进程无法利用多核 CPU；加上动态语言的原生性能瓶颈，**横向扩展**是提升吞吐量的必经之路。Funboost 让这一切变得简单——代码无需任何修改，即可从单机无缝扩展到多进程、Docker 容器或多台物理机。


## 1.5 🎓 最佳学习路径

以 **1.3 章节** 的求和代码为蓝本，修改 `@boost` 中的参数（如 `qps`、`concurrent_num`），添加 `time.sleep()` 模拟耗时，观察控制台输出即可体会分布式、并发和控频的实际效果。

> **🤖 AI 助教**：强烈推荐参考 **[文档第 14 章]**，利用 AI 大模型快速精通 funboost。

---

## 1.6 🥋 funboost 练就吸星大法神功，一招吸走 Celery 毕生内力

Funboost 自身性能与 Celery 相比已有数量级优势（见文档 **2.6**、**2.9**）。将 Celery 作为 **Broker**（`BrokerEnum.CELERY`），是在保留 Funboost 调度与开发体验的前提下，借 Celery 生态打消部分用户对“调度核心是否够稳”的顾虑——**底层仍是 Celery 队列与执行，上层由 Funboost 统一入口与配置**。

### ⚔️ 降维打击：化繁为简的绝世武功

| 🆚 招式对决 | 🛑 原生 Celery (旧派宗门的桎梏) | 🟢 Funboost 御剑术 (新派宗师的洒脱) |
| :--- | :--- | :--- |
| **启动法门**<br>(部署) | **念诵咒语**：需死记硬背 `worker/beat` 等冗长命令行，稍有错漏便走火入魔。 | **意念合一**：代码即启动，无需记忆任何咒语，`python xx.py` 一剑破万法。 |
| **门派规矩**<br>(结构) | **清规戒律**：强行规定目录结构，错置文件即被逐出师门，极其僵化。 | **无招胜有招**：飞花摘叶皆可伤人，任意目录、任意文件皆可为战场，毫无束缚。 |
| **心法运转**<br>(门槛) | **经脉逆行**：需手动修炼 `includes` 和 `task_routes`，极易气血翻涌（配置报错）。 | **浑然天成**：自动打通任督二脉，框架自动发现并注册任务，行云流水。 |
| **洞察天地**<br>(体验) | **盲人摸象**：`@app.task` 入参如雾里看花，IDE 无法感知，极易行差踏错。 | **天眼通**：`BoosterParams` 开启全知视角，代码补全如神助，所见即所得。 |

> **📜 藏经阁 (代码示例)**：完整示例见 **[11.1 章节](https://funboost.readthedocs.io/zh-cn/latest/articles/c11.html)**。


[查看 funboost 分布式函数调度平台 完整教程](https://funboost.readthedocs.io/)  

![](https://visitor-badge.glitch.me/badge?page_id=distributed_framework)  

<div> </div>  


