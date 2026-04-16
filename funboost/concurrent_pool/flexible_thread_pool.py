"""
比 ThreadPoolExecutorShrinkAble 更简单的的弹性线程池。完全彻底从头手工开发

FlexibleThreadPool submit 返回标准的 concurrent.futures.Future 对象。
FlexibleThreadPool 的map 方法，虽然没继承concurrent.futures.Executor ，但能直接万能复用使用 concurrent.futures.Executor.map 方法。

此线程池性能比官方 concurrent.futures.ThreadPoolExecutor 高出极多，且具备：
1. 精准的无竞态弹性缩容（Scale-down）能力。
2. 完美的 asyncio 混合并发兼容（自动调度 async def 函数）。
3. 严格的有界队列背压（Backpressure）控制，防止 OOM。
4. 自然优雅的生命周期：利用 daemon=False 与 MIN_WORKERS 实现自动退出。
5. 拒绝无脑扩容，如果函数执行很快 + submit 频率稀疏，FlexibleThreadPool 不仅拒绝无脑扩容到最大线程，而且会自动缩容。
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
from funboost.core.loggers import FunboostFileLoggerMixin, LoggerLevelSetterMixin, flogger,get_funboost_file_logger


# ------------------- 异步环境桥接逻辑 -------------------
tl = threading.local()

def _get_thread_local_loop() -> asyncio.AbstractEventLoop:
    if not hasattr(tl, 'asyncio_loop'):
        tl.asyncio_loop = asyncio.new_event_loop()
    return tl.asyncio_loop

def run_sync_or_async_fun(func, *args, **kwargs):
    fun_is_asyncio = inspect.iscoroutinefunction(func)
    if fun_is_asyncio:
        loop = _get_thread_local_loop()
        return loop.run_until_complete(func(*args, **kwargs))
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
            specify_async_loop.run_forever()
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

logger_keep_alive_thread = get_funboost_file_logger('_KeepAliveTimeThread')

# ------------------- 核心线程池实现 -------------------
class FlexibleThreadPool(FunboostFileLoggerMixin, LoggerLevelSetterMixin, FunboostBaseConcurrentPool):
    KEEP_ALIVE_TIME:float = 5.0
    MIN_WORKERS:int = 0  # 1

    def __init__(self, max_workers: typing.Optional[int] = None, work_queue_maxsize=10,
                 specify_async_loop=None,
                 is_auto_start_specify_async_loop_in_child_thread=True):
        """
        参数说明：
        max_workers: 最大线程数，默认是cpu核心数*5。
        work_queue_maxsize: 工作队列最大大小，默认是10。
        param specify_loop: 可以指定loop,很多异步三方包的连接池发请求和类实例化，不能处在不同的loop中。也就是臭名昭著的 `attached to a different loop`
        is_auto_start_specify_async_loop_in_child_thread: 是否自动启动指定的asyncio事件循环，默认是True。
        """
        self.max_workers = max_workers or (os.cpu_count() or 1) * 5
        self.work_queue = queue.Queue(work_queue_maxsize)
        
        self._state_lock = threading.Lock()
        self._total_threads = 0  
        self._free_threads = 0   
        
        self.pool_ident = id(self)
        self._specify_async_loop = specify_async_loop
        self._is_auto_start_specify_async_loop_in_child_thread = is_auto_start_specify_async_loop_in_child_thread

    def _worker(self):
        thread_id = threading.current_thread().ident
        logger_keep_alive_thread.debug(f'新启动线程 {thread_id}') # 用户如果不想看到这个日志，去你的funboost_config.py 的 KEEPALIVETIMETHREAD_LOG_LEVEL 设置为 logging.INFO

        while True:
            # 每轮阻塞等待前，先声明自己处于空闲态。
            with self._state_lock:
                self._free_threads += 1

            try:
                task_item = self.work_queue.get(block=True, timeout=self.KEEP_ALIVE_TIME)
            except queue.Empty:
                with self._state_lock:
                    # 结束等待（超时）后，先撤销本轮空闲计数。
                    self._free_threads -= 1
                    # 【承重墙 1：双重检查】
                    # 如果锁外刚好有线程 put 进来了任务，立刻放弃自杀，回去接客！
                    if not self.work_queue.empty():
                        continue
                        
                    if self._total_threads > self.MIN_WORKERS:
                        logger_keep_alive_thread.debug(f'停止线程 {thread_id}, 当前空闲: {self._free_threads}，总数: {self._total_threads}') # 用户如果不想看到这个日志，去你的funboost_config.py 的 KEEPALIVETIMETHREAD_LOG_LEVEL 设置为 logging.INFO
                        self._total_threads -= 1
                        return  # 退出循环，非守护线程自然死亡
                    else:
                        continue

            with self._state_lock:
                self._free_threads -= 1
            
            func, args, kwargs, fut = task_item
            # if not fut.set_running_or_notify_cancel(): # 不检查这个，funboost中不会被取消
            #     pass
            try:
                res = _new_anyio_fun(func, args, kwargs, 
                                        self._specify_async_loop, 
                                        self._is_auto_start_specify_async_loop_in_child_thread)
                fut.set_result(res)
            except BaseException as exc: 
                fut.set_exception(exc)
                self.logger.exception(f'函数 {func} 中发生错误: {type(exc)} {exc} ')

    def submit(self, func, *args, **kwargs) -> Future:
        fut = Future()
        task_item = (func, args, kwargs, fut) # 使用元组更轻量
        put_in_lock_success = False  # 💡 增加一个状态标记

        with self._state_lock:
            # 扩容判定
            need_new_thread = (self._free_threads == 0 and self._total_threads < self.max_workers)
            if need_new_thread:
                t = threading.Thread(target=self._worker, daemon=False)
                t.start()
                # 只有线程真正启动成功才增加总线程计数，避免异常路径统计泄漏。
                self._total_threads += 1

            # 【承重墙 2：尝试在锁内入队】
            # 必须在释放锁之前把任务塞进去，这样即将超时的 Worker 拿到锁时必定能看见它
            try:
                self.work_queue.put_nowait(task_item)
                put_in_lock_success = True  # 锁内放入成功！
            except queue.Full:
                pass # 队列满了，准备退到锁外阻塞等待
                
        # 💡 逻辑一目了然：如果锁内没放进去，就在锁外阻塞排队
        if not put_in_lock_success:
            self.work_queue.put(task_item)
            
        return fut

    map = Executor.map 
    
    def shutdown(self, wait: bool = True) -> None:
        """是依赖keep_alive_time 来自动结束pool的线程，无需主动清理"""
        pass


class FlexibleThreadPoolMinWorkers0(FlexibleThreadPool):
    """
    这个 FlexibleThreadPoolMinWorkers0 是为了脚本能自动结束
    因为pool里面的线程是daemon=False的，如果 MIN_WORKERS > 0 ,那么脚本就不能自动结束运行了。

    如果你的脚本需要能自动结束，那么选择这个类FlexibleThreadPoolMinWorkers0，
    或者你把你设置你的 FlexibleThreadPool 的对象的  pool.MIN_WORKERS = 0。
    如果你的脚本本来就是持续运行永不结束的， 压根不需要自动结束，就用 FlexibleThreadPool 类也可以。
    """
    MIN_WORKERS = 0 

class FlexibleThreadPoolMinWorkers1(FlexibleThreadPool):
    MIN_WORKERS = 1 # 如果设置为1，脚本永远不会自动结束。


if __name__ == '__main__':
    import time

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
    pool.KEEP_ALIVE_TIME=2
    pool.MIN_WORKERS=1
    
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

    def delay_add_task(y):
        time.sleep(10)
        pool.submit(aiotestf, y)

    threading.Thread(target=delay_add_task, args=(666,)).start()

    # for i in range(100000):
    #     pool.submit(testf, i)