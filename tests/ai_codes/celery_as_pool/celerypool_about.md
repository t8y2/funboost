# CeleryPool vs 原生 Celery 用法对比

## 一、CeleryPool 做同样的事情，代码量差几倍

### 原生 Celery：实现加法和乘法消费

需要 **4 个文件**，严格的目录结构：

```
my_celery_project/
├── celery_config.py      # 配置文件
├── celery_app.py         # App 实例
├── tasks.py              # 任务定义
└── run_tasks.py           # 发布任务
```

**celery_config.py：**
```python
from kombu import Queue

broker_url = 'redis://localhost:6379/0'
result_backend = 'redis://localhost:6379/0'
task_serializer = 'json'
accept_content = ['json']
result_serializer = 'json'

task_queues = (
    Queue('add_queue'),
    Queue('multiply_queue'),
)

task_routes = {
    'tasks.add': {'queue': 'add_queue'},
    'tasks.multiply': {'queue': 'multiply_queue'},
}
```

**celery_app.py：**
```python
from celery import Celery

app = Celery('my_project')
app.config_from_object('celery_config')
app.conf.include = ['tasks']
```

**tasks.py：**
```python
from celery_app import app

@app.task(name='tasks.add')
def add(a, b):
    return a + b

@app.task(name='tasks.multiply')
def multiply(x, y):
    return x * y
```

**run_tasks.py（发布任务）：**
```python
from tasks import add, multiply

result1 = add.delay(5, 3)
result2 = multiply.delay(4, 7)

print(result1.get(timeout=10))  # 8
print(result2.get(timeout=10))  # 28
```

**启动 worker（必须用命令行）：**
```bash
celery -A celery_app worker --queues=add_queue,multiply_queue --pool=threads --concurrency=4 --loglevel=INFO
```

**容易踩的坑：**
- `celery_config.py` 中 `task_routes` 的 key 必须与 `@app.task(name=...)` 一致，写错不报错，静默路由到默认队列
- `celery_app.py` 的 `app.conf.include` 必须用字符串模块路径
- tasks.py 必须 `from celery_app import app`，形成**循环依赖**风险
- 启动命令的 `--queues` 必须和配置中的队列名一致
- 如果用 `autodiscover_tasks`，目录结构必须满足 Celery 的约定
- Windows 上 `--pool=prefork` 可能出错

---

### CeleryPool：实现同样的事情

**1 个文件，不到 20 行：**

```python
from celery_pool import CeleryPool

def add(a, b):
    return a + b

def multiply(x, y):
    return x * y

pool = CeleryPool(
    broker_url='redis://localhost:6379/0',
    result_backend='redis://localhost:6379/0',
    concurrent_num=4,
    queue_name='my_pool',
)

print(pool.submit(add, 5, 3).result(timeout=10))       # 8
print(pool.submit(multiply, 4, 7).result(timeout=10))   # 28
```

**不需要：**
- ❌ 不需要 `celery_config.py`
- ❌ 不需要 `celery_app.py`
- ❌ 不需要 `@app.task` 装饰器
- ❌ 不需要 `task_routes` / `task_queues` / `include` 配置
- ❌ 不需要命令行启动 worker
- ❌ 不需要担心循环导入

---

## 二、核心差异对比表

| 维度 | 原生 Celery | CeleryPool |
|:---|:---|:---|
| **文件数量** | 至少 4 个（config/app/tasks/run） | 1 个即可 |
| **任务注册** | `@app.task(name='...')` + `include` | 不需要，任意函数直接 submit |
| **队列路由** | `task_routes` + `Queue()` + `--queues` 三处对齐 | 构造函数一个 `queue_name` 搞定 |
| **Worker 启动** | 命令行 `celery -A ... worker ...` | 自动启动，无需命令行 |
| **获取结果** | `result.get()` (Celery AsyncResult) | `future.result()` (标准 Future) |
| **目录结构** | 必须规范（避免循环导入） | 完全自由 |
| **函数要求** | 必须加 `@app.task` 装饰器 | 任意顶层可导入函数 |
| **IDE 补全** | 弱（字符串配置多） | 强（Celery app 配置由代码传入） |
| **Windows** | 多进程模式常出问题 | threads 模式稳定 |
| **API 兼容** | Celery 专有 API | `concurrent.futures.Future` 标准 |

---

## 三、API 用法对比

### 提交任务

```python
# 原生 Celery
result = add.delay(5, 3)            # 必须用 @app.task 装饰过的函数
result = add.apply_async(args=[5, 3], queue='add_queue')

# CeleryPool
future = pool.submit(add, 5, 3)     # 任意函数，和 ThreadPoolExecutor 一样
```

### 获取结果

```python
# 原生 Celery
value = result.get(timeout=10)      # Celery 的 AsyncResult.get()

# CeleryPool
value = future.result(timeout=10)   # 标准 concurrent.futures.Future.result()
```

### 批量提交

```python
# 原生 Celery
from celery import group
results = group(add.s(i, i) for i in range(10))()
values = results.get()

# CeleryPool
values = list(pool.map(add, range(10), range(10), timeout=30))
```

### 多队列

```python
# 原生 Celery：需要 task_routes + task_queues + --queues 三处配置
# celery_config.py
task_routes = {
    'tasks.add': {'queue': 'q1'},
    'tasks.multiply': {'queue': 'q2'},
}
# 启动时
# celery -A app worker --queues=q1,q2

# CeleryPool：实例化两个 pool 即可
pool_add = CeleryPool(queue_name='q1', ...)
pool_mul = CeleryPool(queue_name='q2', ...)
pool_add.submit(add, 1, 2)
pool_mul.submit(multiply, 3, 4)
```

---

## 四、CeleryPool 适合什么场景

### 适合用 CeleryPool 的场景

1. **快速原型 / 小型项目**：不想写 4 个文件 + 配置 + 命令行，只想 `pool.submit(fn, args)` 开箱即用
2. **从 ThreadPoolExecutor 迁移**：API 完全兼容，改一行代码就能获得分布式能力
3. **同一脚本中多队列**：实例化多个 pool 即可，不需要路由配置
4. **Windows 开发环境**：threads 模式稳定
5. **不想学 Celery 的配置体系**：避免 `task_routes` / `include` / `autodiscover` / `Queue` 等概念

### 仍然建议用原生 Celery 的场景

1. **大型分布式系统**：多机器、多 worker 独立部署，需要细粒度的路由、优先级、Canvas 工作流
2. **与 Django/Flask 深度集成**：需要 `django-celery-beat` 管理定时任务、Admin 查看结果
3. **需要 Canvas 编排**：chain / group / chord / starmap 等复杂工作流
4. **需要 Flower 监控**：生产环境的实时监控面板
5. **团队已熟悉 Celery**：不需要迁移成本

---

## 五、结论

**CeleryPool 不是要取代 Celery，而是给 Celery 套了一层更友好的 API。**

底层仍然是 Celery worker 在消费，仍然用 Redis/RabbitMQ 做 broker。但用户面对的 API 从 Celery 的 `@app.task` / `delay` / `apply_async` / `AsyncResult.get()` 简化为了标准的 `pool.submit(fn, *args)` / `future.result()`。

如果你觉得 CeleryPool 还不够强，可以试试 `funboost` 的 `FunboostPool` 和 `MemoryFunboostPool`——同样的 Pool API，但额外提供：
- 弹性线程池自动伸缩
- asyncio 原生支持
- QPS 分布式控频
- 40+ 种消息中间件
- 内存队列模式（零外部依赖）
- 重试策略、超时、死信等 30+ 种任务控制
