"""
将 Celery 封装为 concurrent.futures.Executor 兼容的 Pool API。

设计理念与 FunboostPool 一致：
- submit(fn, *args, **kwargs) 返回 concurrent.futures.Future（原生类型）
- map() 批量提交
- shutdown() / with 语句

用法：
    from celery_pool import CeleryPool

    def add(a, b):
        return a + b

    pool = CeleryPool(broker_url='redis://localhost:6379/0', result_backend='redis://localhost:6379/0')
    future = pool.submit(add, 1, 2)
    print(future.result())  # 3
"""

import concurrent.futures
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
        module_name, func_name = func_path.rsplit(".", 1)
        module = importlib.import_module(module_name)
        func = getattr(module, func_name)
    return func(*args, **kwargs)


class CeleryFuture(Future):
    """
    继承 concurrent.futures.Future，惰性解析 Celery 结果。
    不调用 .result() = 不浪费任何线程、不做任何轮询。
    """

    def __init__(self, celery_async_result: CeleryAsyncResult, has_backend: bool):
        super().__init__()
        self._cr = celery_async_result
        self._has_backend = has_backend

    def result(self, timeout: typing.Optional[float] = None) -> typing.Any:
        if self.done():
            return super().result(timeout=0)

        if not self._has_backend:
            raise RuntimeError(
                "要获取 future.result()，请在 CeleryPool 初始化时设置 result_backend 参数。\n"
                "例如: CeleryPool(broker_url='redis://...', result_backend='redis://...')"
            )

        deadline = time.time() + (timeout if timeout is not None else 300)
        interval = 0.1
        while not self._cr.ready():
            if time.time() > deadline:
                raise TimeoutError(f"CeleryPool: 等待结果超时({timeout}s)")
            time.sleep(interval)
            interval = min(interval * 2, 2.0)

        if not self.done():
            try:
                if self._cr.successful():
                    self.set_result(self._cr.result)
                else:
                    exc = self._cr.result
                    self.set_exception(
                        exc if isinstance(exc, Exception) else RuntimeError(str(exc))
                    )
            except concurrent.futures.InvalidStateError:
                pass

        return super().result(timeout=0)


class CeleryPool:
    """
    将 Celery 封装为 concurrent.futures.Executor 兼容的 Pool API。

    与 FunboostPool 对照：
      FunboostPool 用 funboost Booster 驱动，CeleryPool 用 Celery worker 驱动。
      二者 submit/map/shutdown 接口一致，均返回标准 concurrent.futures.Future。

    局限：
    - fn 必须是顶层可导入的函数（与 FunboostPool 的函数路径模式相同限制）
    - 返回值和参数必须是 JSON 可序列化的（Celery 序列化约束）
    - 需要 Redis/RabbitMQ 等外部 Broker 运行
    """

    def __init__(
        self,
        broker_url: str = 'redis://localhost:6379/0',
        result_backend: typing.Optional[str] = None,
        concurrent_num: int = 4,
        pool_type: str = 'threads',
        queue_name: typing.Optional[str] = None,
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
        :param queue_name:      队列名称（默认自动生成）
        :param is_auto_start_worker:  是否自动启动 worker
        :param worker_loglevel: worker 日志级别
        :param worker_startup_timeout: 等待 worker 启动的秒数
        :param other_celery_app_conf:  额外 Celery app 配置字典，自动合并到 app.conf 中。
                                       可传入任何 Celery 支持的配置项，例如：
                                       {'task_acks_late': True, 'worker_prefetch_multiplier': 1}
        """
        self.broker_url = broker_url
        self.result_backend = result_backend
        self.concurrent_num = concurrent_num
        self.pool_type = pool_type
        self.queue_name = queue_name or f'celery_pool_{id(self)}'
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

        self.app = Celery('celery_pool')
        self.app.conf.update(**app_conf)

        @self.app.task(name=task_name)
        def universal_task(func_path, args, kwargs):
            return _import_and_call(func_path, args, kwargs)

        self._universal_task = universal_task

        if is_auto_start_worker:
            self._start_worker()

    def _start_worker(self):
        """
        在 daemon=False 线程中调用 app.worker_main() 启动 Celery worker。
        daemon=False：主进程在 worker 存活期间不会退出。
        """
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
