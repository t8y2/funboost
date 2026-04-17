"""
CeleryPool —— 将 Celery 封装为 concurrent.futures.Executor 兼容的通用任务池
==============================================================================

1. 设计背景
-----------

Celery 是 Python 生态中最流行的分布式任务队列框架，功能强大但上手门槛高。
使用原生 Celery 时，开发者需要：

  a) 为每个任务函数加 @app.task 装饰器，侵入业务代码
  b) 手动创建 Celery app 并管理配置
  c) 另起终端启动 worker 进程
  d) 通过 AsyncResult 获取结果，API 与 concurrent.futures 不兼容
  e) 理解 Celery 的序列化、路由、backend、ack 等概念

CeleryPool 的目标：把以上所有复杂度封装掉，让用户像使用
concurrent.futures.ThreadPoolExecutor 一样使用 Celery 分布式能力。


2. CeleryPool 相比原生 Celery 的核心优势
-----------------------------------------

┌─────────────────────┬───────────────────────────────┬─────────────────────────────────┐
│        维度          │       原生 Celery              │        CeleryPool               │
├─────────────────────┼───────────────────────────────┼─────────────────────────────────┤
│ 函数定义             │ 必须用 @app.task 装饰器标注     │ 任意普通函数，无需装饰器          │
│ Worker 启动          │ 需另开终端 celery -A ... worker │ 自动在线程中启动 worker          │
│ 返回值类型           │ celery.result.AsyncResult      │ concurrent.futures.Future        │
│ 获取结果方式         │ result.get(timeout=...)        │ future.result(timeout=...)       │
│ 多任务批量执行       │ group / chord / chain           │ pool.map(fn, iterable)           │
│ 超时处理             │ result.get(timeout) 抛 TimeoutError │ future.result(timeout) 同上  │
│ 异常传播             │ result.get() 重新抛出远端异常    │ future.result() 同上             │
│ 与标准库兼容性       │ 不兼容 concurrent.futures       │ 完全兼容                         │
│ 与 as_completed 兼容 │ 不支持                         │ 惰性模式下需先 result()           │
│ 资源消耗             │ result.get() 内部轮询消耗线程    │ 惰性模式：不调用 result() 零开销  │
│ 学习曲线             │ 需理解 task/app/worker/broker   │ 只需理解 submit/result           │
│ 代码侵入性           │ 业务函数必须注册为 task          │ 业务函数保持纯净                 │
└─────────────────────┴───────────────────────────────┴─────────────────────────────────┘


3. 用法示例
-----------

3.1 最简用法 —— 3 行代码替代原生 Celery 完整流程

    from funboost.assist.celery_pool import CeleryPool

    def add(a, b):
        return a + b

    pool = CeleryPool(
        broker_url='redis://localhost:6379/0',
        result_backend='redis://localhost:6379/0',
        queue_name='my_add_queue',
    )
    future = pool.submit(add, 1, 2)
    print(future.result())   # 输出: 3

  对比原生 Celery 需要的步骤:
    # 1) 创建 tasks.py
    from celery import Celery
    app = Celery('tasks', broker='redis://localhost:6379/0', backend='redis://localhost:6379/0')
    @app.task
    def add(a, b):
        return a + b

    # 2) 另起终端运行 worker
    #    celery -A tasks worker --loglevel=info

    # 3) 在主程序中调用
    result = add.delay(1, 2)
    print(result.get(timeout=10))   # 输出: 3


3.2 批量提交 —— pool.map 对齐 concurrent.futures.Executor.map

    results = list(pool.map(add, [(1, 2), (3, 4), (5, 6)]))
    # [3, 7, 11]


3.3 "发射后不管"模式 —— 不设置 result_backend

    pool = CeleryPool(broker_url='redis://localhost:6379/0', queue_name='fire_and_forget')
    pool.submit(send_email, to='user@example.com', body='hello')
    # 不需要结果，任务静默执行，零资源浪费


3.4 自定义并发与队列

    pool = CeleryPool(
        broker_url='redis://localhost:6379/0',
        result_backend='redis://localhost:6379/0',
        concurrent_num=8,          # 8 个并发 worker 线程
        pool_type='threads',       # 线程池模式（默认）
        queue_name='my_tasks',     # 队列名（必传）
        worker_loglevel='INFO',    # worker 日志级别
    )


3.5 注入额外 Celery 配置

    pool = CeleryPool(
        broker_url='redis://localhost:6379/0',
        result_backend='redis://localhost:6379/0',
        queue_name='advanced_queue',
        other_celery_app_conf={
            'task_acks_late': True,               # 任务完成后再 ack
            'worker_prefetch_multiplier': 1,       # 每次只预取 1 个任务
            'task_time_limit': 300,                # 单个任务最大执行时间 300s
            'task_soft_time_limit': 240,           # 软超时 240s（触发 SoftTimeLimitExceeded）
            'broker_connection_retry_on_startup': True,
        },
    )


3.6 与 concurrent.futures 工具函数配合

    from concurrent.futures import as_completed, wait

    futures = [pool.submit(add, i, i*10) for i in range(5)]

    # 注意：惰性模式下，需要先触发 result() 才能让 done() 返回 True
    for f in futures:
        print(f.result())

    # 或者使用 wait
    done, not_done = wait(futures, timeout=30)


3.7 异常处理

    def risky_task(x):
        if x < 0:
            raise ValueError(f"负数不允许: {x}")
        return x * 2

    future = pool.submit(risky_task, -1)
    try:
        future.result()
    except ValueError as e:
        print(f"捕获到远端异常: {e}")


3.8 同进程 vs 分布式

    CeleryPool 自动处理两种场景：

    同进程模式（默认 is_auto_start_worker=True）：
      - worker 在当前进程的线程中启动
      - 函数从 _FUNC_REGISTRY 直接引用，无需可导入
      - 适合开发、测试、单机部署

    分布式模式（is_auto_start_worker=False）：
      - 需要在远程机器上独立启动 worker
      - 函数必须是顶层可导入的（worker 通过 importlib 动态导入）
      - 适合生产环境多机部署


4. 架构概览
-----------

    ┌─────────────────┐
    │   用户代码        │
    │  pool.submit(fn) │
    └───────┬─────────┘
            │  fn → func_path (模块路径字符串)
            ▼
    ┌─────────────────┐
    │  universal_task   │  Celery 注册的唯一 task
    │  .apply_async()   │  将 (func_path, args, kwargs) 序列化到队列
    └───────┬─────────┘
            │  通过 Broker (Redis/RabbitMQ)
            ▼
    ┌─────────────────┐
    │  Celery Worker    │  消费消息
    │  _import_and_call │  还原函数引用并执行
    └───────┬─────────┘
            │  结果写入 Result Backend
            ▼
    ┌─────────────────┐
    │  CeleryFuture     │  惰性轮询 Backend 获取结果
    │  .result()        │  → 指数退避: 0.01s → 0.02s → 0.04s → ... → 5s
    └─────────────────┘

    关键设计决策:
    - 只注册一个 universal_task，通过 func_path 分发所有函数
    - CeleryFuture 继承 concurrent.futures.Future，惰性解析
    - 不调用 .result() = 不消耗任何轮询线程/资源


5. 惰性结果获取（Lazy Resolution）
----------------------------------

CeleryFuture 采用惰性解析策略：

  - 创建 future 时不会立刻去 Backend 拉取结果
  - 只在用户调用 future.result() 时才触发轮询
  - 轮询采用指数退避策略：初始 10ms，每次翻倍，上限 5s
  - 线程安全：使用 threading.Lock + double-check locking 保证并发安全
  - 幂等性：多次调用 result() 只在首次触发解析，后续直接返回缓存值

  惰性模式的代价：
    done() 在 result() 调用之前始终返回 False（因为结果尚未解析）。
    这意味着 concurrent.futures.as_completed() 和 add_done_callback()
    需要在调用 result() 之后才能正确工作。
    这是在"零资源浪费"和"API 完全兼容"之间的权衡选择。


6. 线程安全保证
---------------

CeleryFuture._ensure_resolved 使用 double-check locking：

    if self._resolved:       # 第一次检查（无锁，快速返回）
        return
    with self._resolve_lock: # 加锁
        if self._resolved:   # 第二次检查（防止并发重复解析）
            return
        ... 执行轮询和结果设置 ...

  这确保了：
    - 多个线程同时调用 result() 时只有一个线程执行实际解析
    - 解析完成后 self._resolved = True，后续调用零开销直接返回
    - self._cr（Celery AsyncResult 引用）在解析后设为 None，释放资源


7. 函数路由机制
---------------

CeleryPool 使用单一 universal_task + 函数路径字符串 实现任意函数路由：

    submit(add, 1, 2)
      → func_path = "mymodule.add"
      → universal_task.apply_async(args=["mymodule.add", [1, 2], {}])
      → Worker 端: _import_and_call("mymodule.add", [1, 2], {})
                    → 先查 _FUNC_REGISTRY（同进程直接引用）
                    → 再 importlib.import_module 动态导入（分布式模式）
                    → 调用 add(1, 2) 并返回结果

    优势：
    - 用户无需给每个函数加 @app.task 装饰器
    - 新增函数无需修改 Celery 配置
    - 同一个 worker 可执行任意函数


8. 适用场景
-----------

  适合：
    - 希望用最少代码获得分布式任务能力
    - 已有大量业务函数，不想逐一加 @app.task
    - 需要与 concurrent.futures 生态兼容（如 as_completed、wait）
    - 开发阶段快速验证、测试

  不适合：
    - 需要 Celery 高级特性（Canvas: chain / chord / group / starmap）
    - 需要精细的 task 级配置（rate_limit / retry / countdown 等）
    - 对 done() / as_completed() 的实时性有严格要求（惰性模式限制）
"""

import importlib
import threading
import time
import typing
from concurrent.futures import Future, Executor

try:
    from celery import Celery
    from celery.result import AsyncResult as CeleryAsyncResult
except ImportError:
    raise ImportError("请先安装 celery: pip install celery[redis]")


_FUNC_REGISTRY: typing.Dict[str, typing.Callable] = {}


def _get_func_path(fn: typing.Callable) -> str:
    path = f"{fn.__module__}.{fn.__qualname__}"
    _FUNC_REGISTRY[path] = fn
    return path


def _import_and_call(func_path: str, args: list, kwargs: dict):
    """
    同进程模式：优先从注册表取函数引用（解决 __main__ 不可导入的问题）。
    分布式模式：回退到 importlib 动态导入。
    """
    func = _FUNC_REGISTRY.get(func_path)
    if func is None:
        try:
            module_name, func_name = func_path.rsplit(".", 1)
            module = importlib.import_module(module_name)
            func = getattr(module, func_name)
        except (ImportError, AttributeError, ValueError) as e:
            raise ImportError(f"CeleryPool: cant import function '{func_path}': {e}")
    return func(*args, **kwargs)


class CeleryFuture(Future):
    """
    继承 concurrent.futures.Future，惰性解析 Celery 任务结果。

    与原生 Celery AsyncResult 的区别：
    ┌───────────────────┬────────────────────────┬───────────────────────┐
    │      行为          │  Celery AsyncResult     │   CeleryFuture        │
    ├───────────────────┼────────────────────────┼───────────────────────┤
    │ 获取结果           │ result.get(timeout)     │ future.result(timeout)│
    │ 类型继承           │ celery.result.AsyncResult│ concurrent.futures.Future│
    │ 结果获取时机       │ 调用 .get() 时轮询      │ 调用 .result() 时轮询 │
    │ 不取结果时开销      │ 无                      │ 无（惰性）            │
    │ 线程安全           │ 依赖 Celery 实现        │ double-check locking  │
    │ 与标准库工具兼容   │ 不兼容                  │ 兼容（有惰性限制）    │
    └───────────────────┴────────────────────────┴───────────────────────┘

    惰性模式注意事项：
        done() / add_done_callback() / as_completed() 需要先调用 result() 才能生效。
        这是"零资源浪费"和"API 完全兼容"之间的设计权衡。

    指数退避轮询策略：
        初始间隔 10ms → 20ms → 40ms → 80ms → ... → 最大 5s
        对于快速返回的任务，几乎无额外延迟；
        对于长耗时任务，逐步降低轮询频率以减少 Backend 压力。
    """

    def __init__(self, celery_async_result: CeleryAsyncResult, has_backend: bool):
        super().__init__()
        self._cr = celery_async_result
        self._has_backend = has_backend
        self._resolve_lock = threading.Lock()
        self._resolved = False

    def result(self, timeout: typing.Optional[float] = None) -> typing.Any:
        if not self._has_backend:
            raise RuntimeError(
                "要获取 future.result()，请在 CeleryPool 初始化时设置 result_backend 参数。\n"
                "例如: CeleryPool(broker_url='redis://...', result_backend='redis://...', queue_name='my_queue')"
            )
        self._ensure_resolved(timeout)
        return super().result(timeout=timeout)

    def _ensure_resolved(self, timeout=None):
        if self._resolved:
            return
        with self._resolve_lock:
            if self._resolved:
                return
            deadline = time.time() + timeout if timeout is not None else float('inf')
            interval = 0.01
            while True:
                try:
                    meta = self._cr.backend.get_task_meta(self._cr.id)
                except Exception as e:
                    self._resolved = True
                    self._cr = None
                    if not self.done():
                        self.set_exception(e)
                    return
                if meta['status'] in ('SUCCESS', 'FAILURE', 'REVOKED'):
                    break
                if time.time() > deadline:
                    raise TimeoutError(f"CeleryPool: 等待结果超时({timeout}s)")
                time.sleep(interval)
                interval = min(interval * 2, 5.0)
            self._resolved = True
            self._cr = None
            try:
                if meta['status'] == 'SUCCESS':
                    self.set_result(meta['result'])
                else:
                    exc = meta.get('result')
                    self.set_exception(
                        exc if isinstance(exc, Exception) else RuntimeError(str(exc))
                    )
            except Exception as e:
                if not self.done():
                    self.set_exception(e)


_pool_cache: typing.Dict[str, 'CeleryPool'] = {}
_pool_cache_lock = threading.Lock()


class CeleryPool:
    """
    将 Celery 封装为 concurrent.futures.Executor 兼容的通用任务池。

    核心思路：
        一个 CeleryPool 实例 = 一个 Celery app + 一个 universal_task + 一个自动启动的 worker。
        用户只需 pool.submit(fn, *args, **kwargs) 即可将任意函数提交到 Celery 执行，
        无需给函数加 @app.task 装饰器、无需手动启动 worker、无需理解 Celery 配置。

    与 FunboostPool / ThreadPoolExecutor / ProcessPoolExecutor 对照：
        四者 submit / map 接口一致，均返回 concurrent.futures.Future。
        CeleryPool 额外提供了基于消息队列的分布式执行能力。

    与原生 Celery 对照：
        原生 Celery 需要：@app.task 装饰器 → 启动 worker → result.get()
        CeleryPool 只需：pool = CeleryPool(...) → pool.submit(fn, ...)  → future.result()

    工作模式：
        1) 同进程模式（默认 is_auto_start_worker=True）：
           - 自动在当前进程的后台线程中启动 Celery worker
           - 通过 _FUNC_REGISTRY 直接引用函数（无需函数可导入）
           - 适合开发、测试、快速验证
        2) 分布式模式（is_auto_start_worker=False）：
           - 由用户在远程机器上独立启动 Celery worker
           - 函数通过 importlib 动态导入（必须是顶层可导入函数）
           - 适合生产环境、多机部署

    局限：
        - fn 的参数和返回值必须是 JSON 可序列化的（Celery 序列化约束）
        - 分布式模式下 fn 必须是顶层可导入的函数
        - 需要 Redis / RabbitMQ 等外部 Broker 运行
        - 惰性模式下 done() / as_completed() 需先调 result() 触发

    单例语义：
        同一个 queue_name 只创建一次实例，后续 CeleryPool(queue_name='x') 返回缓存的实例。
        避免 for 循环实例化时重复创建 Celery app 和 worker。

    典型用法：
        pool = CeleryPool(
            broker_url='redis://localhost:6379/0',
            result_backend='redis://localhost:6379/0',
            queue_name='my_task_queue',
        )
        future = pool.submit(my_func, arg1, arg2)
        print(future.result())
    """

    def __new__(cls, *args, **kwargs):
        queue_name = kwargs.get('queue_name')
        if queue_name is not None:
            with _pool_cache_lock:
                if queue_name in _pool_cache:
                    return _pool_cache[queue_name]
                instance = super().__new__(cls)
                _pool_cache[queue_name] = instance
                return instance
        return super().__new__(cls)

    def __init__(
        self,
        broker_url: str = 'redis://localhost:6379/0',
        result_backend: typing.Optional[str] = None,
        concurrent_num: int = 4,
        pool_type: str = 'threads',
        *,
        queue_name: str,
        is_auto_start_worker: bool = True,
        worker_loglevel: str = 'WARNING',
        worker_startup_timeout: float = 1.0,
        other_celery_app_conf: typing.Optional[typing.Dict[str, typing.Any]] = None,
    ):
        """
        :param broker_url:      Celery broker 连接 URL
        :param result_backend:  Celery result backend URL。
                                设置后 submit 返回的 future 才能调用 .result() 获取结果。
                                不设置则为纯"发射后不管"模式。
        :param concurrent_num:  worker 并发数
        :param pool_type:       worker 并发池类型 (solo / threads / gevent / prefork)
        :param queue_name:      队列名称（必传），用于隔离不同 CeleryPool 实例的消息。
                                建议使用有业务含义的名称，如 'order_tasks'、'email_queue' 等。
        :param is_auto_start_worker:  是否自动启动 worker
        :param worker_loglevel: worker 日志级别
        :param worker_startup_timeout: 等待 worker 启动的秒数
        :param other_celery_app_conf:  额外 Celery app 配置字典，自动合并到 app.conf 中。
                                       可传入任何 Celery 支持的配置项，例如：
                                       {'task_acks_late': True, 'worker_prefetch_multiplier': 1}
        """
        if getattr(self, '_initialized', False):
            return

        self.broker_url = broker_url
        self.result_backend = result_backend
        self.concurrent_num = concurrent_num
        self.pool_type = pool_type
        self.queue_name = queue_name
        self.worker_loglevel = worker_loglevel
        self.worker_startup_timeout = worker_startup_timeout

        task_name = f'celery_pool_universal_{self.queue_name}'

        app_conf = dict(
            broker_url=self.broker_url,
            task_serializer='json',
            accept_content=['json'],
            result_serializer='json',
            task_track_started=True,
            worker_hijack_root_logger=False,
            task_default_queue=self.queue_name,
            task_routes={task_name: {'queue': self.queue_name}},
        )
        if self.result_backend:
            app_conf['result_backend'] = self.result_backend
        if other_celery_app_conf:
            app_conf.update(other_celery_app_conf)

        self.app = Celery(f'celery_pool_{self.queue_name}')
        self.app.conf.update(**app_conf)

        @self.app.task(name=task_name)
        def universal_task(func_path, args, kwargs):
            return _import_and_call(func_path, args, kwargs)

        self._universal_task = universal_task

        self._worker_thread = None
        if is_auto_start_worker:
            self.start_worker()

        self._initialized = True

    def start_worker(self):
        """在线程中启动 Celery worker，通过 sleep 等待其就绪。"""
        def _run():
            self.app.worker_main([
                'worker',
                f'--pool={self.pool_type}',
                f'--concurrency={self.concurrent_num}',
                '-Q', self.queue_name,
                f'--loglevel={self.worker_loglevel}',
                '--without-heartbeat',
                '--without-mingle',
                '--without-gossip',
            ])

        self._worker_thread = threading.Thread(
            target=_run, daemon=False, name='celery-pool-worker',
        )
        self._worker_thread.start()
        time.sleep(self.worker_startup_timeout)

        from celery._state import _set_task_join_will_block
        _set_task_join_will_block(False)

    def submit(self, fn: typing.Callable, *args, **kwargs) -> Future:
        """
        提交任意函数到 Celery 执行，返回 concurrent.futures.Future。
        惰性获取结果：不调用 .result() 不浪费任何线程。
        """
        func_path = _get_func_path(fn)

        celery_async_result = self._universal_task.apply_async(
            args=[func_path, list(args), kwargs],
            queue=self.queue_name,
        )

        return CeleryFuture(celery_async_result, has_backend=bool(self.result_backend))

    map = Executor.map

    def shutdown(self, wait: bool = True):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()

