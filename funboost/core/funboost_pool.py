"""
写一个 Funboost 通用任务池，支持 submit 任意函数，并返回 Future。
除了实例化入参，最常用的submit方法和 concurrent.futures.ThreadPoolExecutor 一样。例如submit和返回future。
所以用户可以使用 MemoryFunboostPool 或者 FunboostPool 的实例化对象替代之前的 ThreadPoolExecutor的对象。一般用户只用到pool.submit，基本完美平替，只需要修改一行代码。

funboostpool 比 ThreadPoolExecutor更强的在于，可以内存存储任务，也可以分布式消息队列存任务。
funboostpool 有几十种任务控制功能，例如重试策略，超时策略，任务优先级。
funboostpool 能支持asyncio任务和同步任务，ThreadPoolExecutor 没这个能力
funboostpool 的池子可以自动扩大和自动缩小，ThreadPoolExecutor 不能自动缩小。
FunboostPool 拥有funboost的所有能力

api用法和普通线程池一样，用法详见教程4.38章节。
"""

import typing
import threading
from typing import Optional
import concurrent.futures
from funboost import (
    BoosterParams,
    BrokerEnum,
    Booster,
    FunctionResultStatus,
    AsyncResult,
)
from funboost.core.exceptions import FunboostTaskExecutionError
from funboost.concurrent_pool.flexible_thread_pool import (
    _new_anyio_fun,
)
import importlib


class FunboostFuture(concurrent.futures.Future):
    """
    继承 concurrent.futures.Future，统一处理 FunctionResultStatus → 业务结果的转换。

    惰性模式：只在用户调用 .result() 时才真正获取结果，
    如果用户不调用 result()，不会触发 Redis blpop 等网络操作，零额外开销。
    注意：惰性模式下 done() / add_done_callback() / as_completed() 需要先调用 result() 才能生效。
    """

    def __init__(self, is_future_direct_ret_result: bool = True, has_result_source: bool = True):
        super().__init__()
        self._is_direct = is_future_direct_ret_result
        self._has_result_source = has_result_source
        self._async_result: typing.Optional[AsyncResult] = None
        self._raw_future: typing.Optional[concurrent.futures.Future] = None
        self._is_memory_mode = False
        self._resolve_lock = threading.Lock()
        self._resolved = False

    def result(self, timeout=None):
        if not self._has_result_source:
            raise RuntimeError(
                "当前 FunboostPool 未启用结果获取（is_need_result=False）。\n"
                "要获取 future.result()，请在初始化时设置 is_need_result=True"
            )
        self._ensure_resolved(timeout)
        return super().result(timeout=timeout)

    def _ensure_resolved(self, timeout=None):
        """
        线程安全的惰性解析，使用 double-check locking 避免重复获取。
        关键设计：
        1. 在调用 set_result/set_exception 之前先设置 _resolved=True 并释放引用，
           防止回调中再次调用 result() 时产生死锁或重复解析。
        2. 内存模式的 TimeoutError 直接 re-raise 不标记 resolved，
           因为任务仍在后台执行，用户可用更长的 timeout 重试。
        """
        if self._resolved:
            return
        with self._resolve_lock:
            if self._resolved:
                return
            status_to_resolve = None
            try:
                if self._is_memory_mode and self._raw_future is not None:
                    status_to_resolve = self._raw_future.result(timeout=timeout)
                elif self._async_result is not None:
                    if timeout is not None:
                        self._async_result.set_timeout(timeout)
                    status_to_resolve = self._async_result.status_and_result_obj
                    if status_to_resolve is None:
                        from funboost.core.exceptions import FunboostWaitRpcResultTimeout
                        raise FunboostWaitRpcResultTimeout(
                            f'wait rpc data timeout for task_id:{self._async_result.task_id}'
                        )
            except concurrent.futures.TimeoutError:
                raise
            except Exception as e:
                self._resolved = True
                self._async_result = None
                self._raw_future = None
                if not self.done():
                    self.set_exception(e)
                return
            self._resolved = True
            self._async_result = None
            self._raw_future = None
            self._resolve_status(status_to_resolve)

    def _resolve_status(self, status: FunctionResultStatus):
        if self._is_direct:
            if status.success:
                self.set_result(status.result)
            else:
                self.set_exception(FunboostTaskExecutionError(
                    exception_type=status.exception_type or 'UnknownError',
                    exception_msg=status.exception,
                ))
        else:
            self.set_result(status)

    def bind_raw_future(self, raw_future: concurrent.futures.Future):
        """内存队列模式：保存 raw_future 引用，延迟到 result() 时才获取"""
        self._is_memory_mode = True
        self._raw_future = raw_future

    def bind_async_result(self, async_result: AsyncResult):
        """分布式队列模式：保存 AsyncResult 引用，延迟到 result() 时才获取"""
        self._async_result = async_result


class MemoryFunboostPool:
    """
    一个基于内存队列的 Funboost 任务池。
    支持 submit 任意函数，并返回 Future。
    固定使用内存队列，固定不重试，以复刻原始线程池行为。
    """

    def __init__(
        self,
        concurrent_num: int = 4,
        *,
        qps: Optional[float] = None,
        is_future_direct_ret_result: bool = True,
        is_auto_start_consuming_message: bool = True,
    ):
        """
        创建一个通用任务池。 固定使用内存队列，固定不重试，以复刻原始线程池行为。
        :param concurrent_num: 最大线程数
        :param qps: 每秒处理消息数

        :param is_future_direct_ret_result: future中是的数据是最终result结果，还是 FunctionResultStatus 对象。
               如果返回FunctionResultStatus对象，那么信息更为丰富，包括重试了几次，耗时等等。
               如果返回result结果，那么只有结果，没有其他信息，但是更贴合原生的 concurrent.futures.Future.result() 方法的返回值。
        :return:
        """
        self.concurrent_num = concurrent_num
        self.qps = qps
        self.booster: Booster  # 用户仍然可以通过 pool.booster. 来操作booster其他方法和属性，booster是公有属性
        # self._pool_queue_name = f"universal_pool_{id(self)}"

        self.booster_params = BoosterParams(
            queue_name=f"universal_pool_{id(self)}",
            concurrent_num=self.concurrent_num,
            qps=self.qps,
            max_retry_times=0,
            broker_kind=BrokerEnum.MEMORY_QUEUE,
        )

        self.is_future_direct_ret_result = is_future_direct_ret_result
        self.is_auto_start_consuming_message = is_auto_start_consuming_message
        self._create_booster()
        self._start_consume()

    def _start_consume(self):
        if self.is_auto_start_consuming_message:
            self.booster.consume()

    def _create_booster(self):
        # 核心：定义一个通用的消费函数，它不关心业务逻辑，只负责执行消息中携带的 "函数和参数"
        def universal_consumer(func, args, kwargs):

            return _new_anyio_fun(
                func,
                args,
                kwargs,
                self.booster_params.specify_async_loop,
                self.booster_params.is_auto_start_specify_async_loop_in_child_thread,
            )

        # 使用这个通用消费者创建 Booster，只创建一次！
        self.booster = Booster(self.booster_params)(universal_consumer)

    def submit(self, fn: typing.Callable, *args, **kwargs) -> concurrent.futures.Future:
        """
        提交任意函数 fn 到线程池执行。
        :param fn: 要执行的函数
        :param args: 位置参数
        :param kwargs: 关键字参数
        :return: concurrent.futures.Future 对象
        """
        raw_future = self.booster.publisher.get_future(fn, args, kwargs)
        future = FunboostFuture(self.is_future_direct_ret_result)
        future.bind_raw_future(raw_future)
        return future

    map = concurrent.futures.Executor.map

    def shutdown(self, wait: bool = True):
        """关闭线程池（内存队列无需特殊清理）"""
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()


class FunboostPoolPickleFunc(MemoryFunboostPool):
    def __init__(
        self,
        booster_params,
        *,
        is_need_result=False,
        is_future_direct_ret_result: bool = True,
        is_auto_start_consuming_message: bool = True,
    ):
        """
        创建一个通用任务池。
        :param booster_params: BoosterParams 对象. FunboostPool相比MemoryFunboostPool有更多的控制入参。
        :param is_need_result: 是否需要返回执行结果,如果不关心结果只执行，可以不使用rpc模式，不依赖redis做rpc，节约redis空间和性能。
        :param is_future_direct_ret_result: future中是的数据是最终result结果，还是 FunctionResultStatus 对象。
               如果返回FunctionResultStatus的信息更为丰富，包括重试了几次，耗时等等。
               如果返回result结果，那么只有结果，没有其他信息，但是更贴合原原生的 concurrent.futures.Future.result() 方法的返回值。
        :return:
        """
        self.booster_params = booster_params
        if (
            self.booster_params.broker_kind != BrokerEnum.MEMORY_QUEUE
            and is_need_result is True
        ):
            self.booster_params.is_using_rpc_mode = True
        self.is_need_result = is_need_result
        self.is_future_direct_ret_result = is_future_direct_ret_result
        self.is_auto_start_consuming_message = is_auto_start_consuming_message
        self.booster: Booster  # 用户仍然可以通过 pool.booster. 来操作booster其他方法和属性，booster是公有属性
        self._create_booster()
        self._start_consume()
    
    @staticmethod
    def _get_fn_new( fn: typing.Callable):
        """
        FunboostPoolPickleFunc 模式，fn会被自动pickle序列化，再发到消息队列。
        """
        return fn

    def submit(self, fn: typing.Callable, *args, **kwargs) -> concurrent.futures.Future:
        if self.booster_params.broker_kind == BrokerEnum.MEMORY_QUEUE:
            return super().submit(fn, *args, **kwargs)

        fn_new = self._get_fn_new(fn)
        async_result: AsyncResult = self.booster.push(fn_new, args, kwargs)
        if self.is_need_result is False:
            return FunboostFuture(has_result_source=False)

        future = FunboostFuture(self.is_future_direct_ret_result)
        future.bind_async_result(async_result)
        return future

def get_fun_path(fn: typing.Callable):
    """
    获取函数的路径字符串，例如 "my_module.my_submodule.my_func"
    """
    return f"{fn.__module__}.{fn.__qualname__}"

class FunboostPool(FunboostPoolPickleFunc):

    @staticmethod
    def _get_fn_new( fn: typing.Callable):
        """
        FunboostPool 模式
        使用函数路径，它不再依赖 pickle 序列化函发到消息队列，而是把函数路径字符串发送到消息队列。
        消息更清晰，用户能通过查看消息，知道要运行的是什么函数
        """
        return get_fun_path(fn)

    def _create_booster(self):
        def universal_consumer(func_path, args: tuple, kwargs: dict):
            if callable(func_path):
                func = func_path
            else:
                try:
                    module_name, func_name = func_path.rsplit(".", 1)
                    module = importlib.import_module(module_name)
                    func = getattr(module, func_name)
                except (ImportError, AttributeError) as e:
                    raise ImportError(f"cant import function '{func_path}': {e}")

            return _new_anyio_fun(
                func,
                args,
                kwargs,
                self.booster_params.specify_async_loop,
                self.booster_params.is_auto_start_specify_async_loop_in_child_thread,
            )

        # 使用这个通用消费者创建 Booster，只创建一次！
        self.booster = Booster(self.booster_params)(universal_consumer)


if __name__ == "__main__":
    import asyncio

    class Obj:
        def __init__(self, x):
            self.x = x

    def add(a, b):
        # return a + b
        return Obj(a + b)

    def multiply(x, y):
        return x * y

    def greet(name):
        return f"Hello, {name}"

    # funboostpool能执行asyncio函数，而且能支持指定asyncio loop，能自动启动指定的asyncio loop，例如某些aio的连接池的包，需要实例化和发请求在同一个loop。
    async def aio_fun(x):
        await asyncio.sleep(1)
        return x * 10

    # pool = MemoryFunboostPool(
    #     10,
    #     qps=100,
    #     is_future_direct_ret_result=True,
    # )

    # 像原生线程池一样随意切换函数，
    pool = FunboostPool(
        BoosterParams(
            queue_name="universal_queue",
            broker_kind=BrokerEnum.REDIS,  # 不仅支持内存队列，也支持其他队列。
            concurrent_num=10,
            max_retry_times=5,
        ),
        is_need_result=False,
        is_future_direct_ret_result=True,
    )

    # 提交加法
    fut1 = pool.submit(add, 5, 3)
    # 提交乘法
    fut2 = pool.submit(multiply, 4, 7)
    # 提交带关键字参数的函数
    fut3 = pool.submit(greet, name="Funboost")

    fut4 = pool.submit(aio_fun, 5)

    # res1 = fut1.result()  # 8
    # print(type(res1), res1)

    # print(fut2.result())  # 28
    # print(fut3.result())  # Hello, Funboost
    # print(fut4.result())  # 50
