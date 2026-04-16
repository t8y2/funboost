"""
比 ThreadPoolExecutorShrinkAble 更简单的的弹性线程池。完全彻底从头手工开发

FlexibleThreadPool submit 返回标准的 concurrent.futures.Future 对象。
FlexibleThreadPool 的map 方法，虽然没继承concurrent.futures.Executor ，但能直接万能复用使用 concurrent.futures.Executor.map 方法。

此线程池性能比concurrent.futures.ThreadPoolExecutor高200%


"""
import typing
import asyncio
import inspect
import os
import queue
import threading
from functools import wraps
from concurrent.futures import Future, Executor

from funboost.concurrent_pool import FunboostBaseConcurrentPool
from funboost.core.loggers import FunboostFileLoggerMixin, LoggerLevelSetterMixin, FunboostMetaTypeFileLogger,flogger


class FlexibleThreadPool(FunboostFileLoggerMixin, LoggerLevelSetterMixin, FunboostBaseConcurrentPool):
    KEEP_ALIVE_TIME = 10
    MIN_WORKERS = 1

    def __init__(self, max_workers: typing.Optional[int] = None,work_queue_maxsize=10,
                 specify_async_loop=None,
                 is_auto_start_specify_async_loop_in_child_thread=True
                 ):
        self.work_queue = queue.Queue(work_queue_maxsize)
        self.max_workers = max_workers
        self._threads_num = 0
        self.threads_free_count = 0
        self._lock_compute_start_thread = threading.Lock()
        self._lock_compute_threads_free_count = threading.Lock()
        self._lock_for_adjust_thread = threading.Lock()
        self._lock_for_judge_threads_free_count = threading.Lock()
        self.pool_ident = id(self)
        self._specify_async_loop = specify_async_loop
        self._is_auto_start_specify_async_loop_in_child_thread = is_auto_start_specify_async_loop_in_child_thread
        # self.asyncio_loop = asyncio.new_event_loop()

    def _change_threads_free_count(self, change_num):
        with self._lock_compute_threads_free_count:
            self.threads_free_count += change_num

    def _change_threads_start_count(self, change_num):
        with self._lock_compute_start_thread:
            self._threads_num += change_num

    def submit(self, func, *args, **kwargs) -> Future:
        fut = Future()
        self.work_queue.put([func, args, kwargs,fut])
        with self._lock_for_adjust_thread:
            if self.threads_free_count <= self.MIN_WORKERS and self._threads_num < self.max_workers:
                _KeepAliveTimeThread(self).start()
                self._change_threads_free_count(1) 
                self._change_threads_start_count(1)
        return fut
    
    map = Executor.map # 神级别方式，直接使用 concurrent.futures.Executor.map 方法。


class FlexibleThreadPoolMinWorkers0(FlexibleThreadPool):
    MIN_WORKERS = 0


def run_sync_or_async_fun000(func, *args, **kwargs):
    """这种方式造成电脑很卡,不行"""
    fun_is_asyncio = inspect.iscoroutinefunction(func)
    if fun_is_asyncio:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(func(*args, **kwargs))
        finally:
            loop.close()
    else:
        return func(*args, **kwargs)


tl = threading.local()


def _get_thread_local_loop() -> asyncio.AbstractEventLoop:
    if not hasattr(tl, 'asyncio_loop'):
        tl.asyncio_loop = asyncio.new_event_loop()
    return tl.asyncio_loop


def run_sync_or_async_fun(func, *args, **kwargs):
    fun_is_asyncio = inspect.iscoroutinefunction(func)
    if fun_is_asyncio:
        loop = _get_thread_local_loop()
        try:
            return loop.run_until_complete(func(*args, **kwargs))
        finally:
            pass
            # loop.close()
    else:
        return func(*args, **kwargs)


def sync_or_async_fun_deco(func):
    @wraps(func)
    def _inner(*args, **kwargs):
        return run_sync_or_async_fun(func, *args, **kwargs)

    return _inner


def _new_anyio_fun(func,args:tuple,kwargs:dict,specify_async_loop,is_auto_start_specify_async_loop_in_child_thread):
    fun_is_asyncio = inspect.iscoroutinefunction(func)
    def _start_specify_async_loop():
        try:
            specify_async_loop.create_task(func(*args, **kwargs))
        except BaseException as exc:
            flogger.error(f'_start_specify_async_loop 启动指定的asyncio loop 时发生错误 {exc}') #is_running有竞争， 小概率重复启动。

    if fun_is_asyncio:
        try:
            if specify_async_loop is not None:
                if is_auto_start_specify_async_loop_in_child_thread:
                    if specify_async_loop.is_running():
                        pass
                    else:
                        threading.Thread(target=_start_specify_async_loop).start()
                return asyncio.run_coroutine_threadsafe(func(*args, **kwargs), specify_async_loop).result()
            else:
                loop = _get_thread_local_loop()
                return loop.run_until_complete(func(*args, **kwargs))
        finally:
            pass
            # loop.close()
    else:
        return func(*args, **kwargs)

# noinspection PyProtectedMember
class _KeepAliveTimeThread(threading.Thread, metaclass=FunboostMetaTypeFileLogger):
    def __init__(self, thread_pool: FlexibleThreadPool):
        super().__init__()
        self.pool = thread_pool

    def run(self) -> None:
        # self.pool._change_threads_free_count(1) # 放在submit里面加1
        # self.pool._change_threads_start_count(1)
        # 可以设置 LogManager('_KeepAliveTimeThread').preset_log_level(logging.INFO) 来屏蔽下面的话,见文档6.17.b
        self.logger.debug(f'新启动线程 {self.ident} ')
        while 1:
            try:
                func, args, kwargs,fut = self.pool.work_queue.get(block=True, timeout=self.pool.KEEP_ALIVE_TIME)
            except queue.Empty:
                with self.pool._lock_for_judge_threads_free_count:
                    # print(self.pool.threads_free_count)
                    if self.pool.threads_free_count > self.pool.MIN_WORKERS:
                  
                        # 你如果不喜欢这条日志，对funboost的自适应伸缩线程池没有兴趣，可以在你的 funboost_config.py 的 FunboostCommonConfig 设置 FUNBOOST_PROMPT_LOG_LEVEL = logging.INFO
                        self.logger.debug(f'停止线程 {self._ident}, 触发条件是 {self.pool.pool_ident} 线程池中的 {self.ident} 线程 超过 {self.pool.KEEP_ALIVE_TIME} 秒没有任务，线程池中不在工作状态中的线程数量是 {self.pool.threads_free_count}，超过了指定的最小核心数量 {self.pool.MIN_WORKERS}')  # noqa
                        self.pool._change_threads_free_count(-1)
                        self.pool._change_threads_start_count(-1)
                        break  # 退出while 1，即是结束。
                    else:
                        continue
            self.pool._change_threads_free_count(-1)
            try:
                # fun = sync_or_async_fun_deco(func)
                # fun(*args, **kwargs)
                res = _new_anyio_fun(func,args,kwargs,self.pool._specify_async_loop,self.pool._is_auto_start_specify_async_loop_in_child_thread)
                fut.set_result(res)
            except BaseException as exc:
                fut.set_exception(exc)
                self.logger.exception(f'函数 {func} 中发生错误，错误原因是 {type(exc)} {exc} ')
            self.pool._change_threads_free_count(1)





if __name__ == '__main__':
    import time
    from concurrent.futures import ThreadPoolExecutor
    from custom_threadpool_executor import ThreadPoolExecutorShrinkAble


    def testf(x):
        # time.sleep(10)
        if x % 10000 == 0:
            print(x)


    async def aiotestf(x):
        # await asyncio.sleep(1)
        if x % 10 == 0 or 1:
            print(x)
        return x * 2


    pool = FlexibleThreadPool(100)
    # pool = ThreadPoolExecutor(100)
    # pool = ThreadPoolExecutorShrinkAble(100)
    
    # 测试submit和 输出 future.result() 的结果
    # for i in range(20000):
    #     # time.sleep(2)
    #     futx:Future = pool.submit(aiotestf, i)
    #     print(futx.result())

    # 测试map用法
    results = pool.map(aiotestf, [1, 2, 3, 4], timeout=5)
    try:
        for res in results:
            print(res)
    except TimeoutError:
        print("有任务执行超时！")



    # for i in range(100000):
    #     pool.submit(testf, i)

    # while 1:
    #     time.sleep(1000)
    # loop.run_forever()


