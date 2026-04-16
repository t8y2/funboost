import sys

import atexit
import asyncio
import concurrent.futures
from concurrent.futures import Executor
import functools
import threading
import time
import traceback
from threading import Thread
import traceback

from funboost.concurrent_pool.base_pool_type import FunboostBaseConcurrentPool
from funboost.core.loggers import FunboostFileLoggerMixin

# if os.name == 'posix':
#     import uvloop
#
#     asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())  # 打猴子补丁最好放在代码顶层，否则很大机会出问题。

"""
# 也可以采用 janus 的 线程安全的queue方式来实现异步池，此queue性能和本模块实现的生产 消费相比，性能并没有提高，所以就不重新用这这个包来实现一次了。
import janus
import asyncio
import time
import threading
import nb_log
queue = janus.Queue(maxsize=6000)

async def consume():
    while 1:
        # time.sleep(1)
        val = await queue.async_q.get() # 这是async，不要看错了
        print(val)

def push():
    for i in range(50000):
        # time.sleep(0.2)
        # print(i)
        queue.sync_q.put(i)  # 这是sync。不要看错了。


if __name__ == '__main__':
    threading.Thread(target=push).start()
    loop = asyncio.get_event_loop()
    loop.create_task(consume())
    loop.run_forever()
"""

if sys.platform == "darwin":  # mac 上会出错
      import selectors
      selectors.DefaultSelector = selectors.PollSelector



class AsyncPoolExecutor(FunboostFileLoggerMixin,FunboostBaseConcurrentPool):
    """
    使api和线程池一样，最好的性能做法是submit也弄成 async def，生产和消费在同一个线程同一个loop一起运行，但会对调用链路的兼容性产生破坏，从而调用方式不兼容线程池。
    
    AsyncPoolExecutor 是真asyncio并发池，是在一个loop跑多个协程任务，而非是 伪线程池里面每个线程都单独用一个新的临时的loop.run_until_complete去运行一个协程任务。

    AsyncPoolExecutor 支持异步函数运行，也支持同步函数运行。
    AsyncPoolExecutor 支持submit 和 map方法，并能返回 concurrent.futures.Future 对象。
    AsyncPoolExecutor 支持aio_submit方法，并能返回 asyncio.Future 对象。
    """

    def __init__(self, size, specify_async_loop=None,
                 is_auto_start_specify_async_loop_in_child_thread=True):
        """

        :param size: 同时并发运行的协程任务数量。
        :param specify_loop: 可以指定loop,很多异步三方包的连接池发请求和类实例化，不能处在不同的loop中。也就是臭名昭著的 `attached to a different loop`
        """
        self._size = size
        self._specify_async_loop = specify_async_loop
        self._is_auto_start_specify_async_loop_in_child_thread = is_auto_start_specify_async_loop_in_child_thread
        self.loop = specify_async_loop or asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self._diff_init()
        # self._lock = threading.Lock()
        t = Thread(target=self._start_loop_in_new_thread, daemon=False)
        # t.setDaemon(True)  # 设置守护线程是为了有机会触发atexit，使程序自动结束，不用手动调用shutdown
        t.start()
        from funboost.concurrent_pool.custom_threadpool_executor import ThreadPoolExecutorShrinkAble
        self._thread_pool = ThreadPoolExecutorShrinkAble(self._size) # 留个线程池，方便执行同步函数
     

    # def submit000(self, func, *args, **kwargs):
    #     # 这个性能比下面的采用 run_coroutine_threadsafe + result返回快了3倍多。
    #     with self._lock:
    #         while 1:
    #             if not self._queue.full():
    #                 self.loop.call_soon_threadsafe(self._queue.put_nowait, (func, args, kwargs))
    #                 break
    #             else:
    #                 time.sleep(0.01)

    def _diff_init(self):
        if sys.version_info.minor < 10:
            # self._sem = asyncio.Semaphore(self._size, loop=self.loop)
            self._queue = asyncio.Queue(maxsize=self._size, loop=self.loop)
        else:
            # self._sem = asyncio.Semaphore(self._size) # python3.10后，很多类和方法都删除了loop传参
            self._queue = asyncio.Queue(maxsize=self._size)


    def submit(self, func, *args, **kwargs):
        """
        从非事件循环线程提交任务，返回 concurrent.futures.Future，可通过 .result() 获取执行结果。
        队列满时会阻塞（背压），防止迅速掏空消息队列几千万消息到内存。
        """
        result_future = concurrent.futures.Future()
        produce_future = asyncio.run_coroutine_threadsafe(self._produce(func, args, kwargs, result_future), self.loop)
        produce_future.result()  # 阻止过快放入，放入超过队列大小后，使submit阻塞。
        return result_future
    
    map = Executor.map # 神级别方式，直接使用 concurrent.futures.Executor.map 方法。

    async def aio_submit(self, func, *args, **kwargs):
        """
        从事件循环内部提交任务，返回 asyncio.Future，可 await 获取执行结果。
        队列满时 await 会挂起当前协程（背压）。
        """
        result_future = self.loop.create_future()
        await self._produce(func, args, kwargs, result_future)
        return result_future

    async def _produce(self, func, args, kwargs, result_future=None):
        await self._queue.put((func, args, kwargs, result_future))

    async def _consume(self):
        while True:
            func, args, kwargs, result_future = await self._queue.get()
            if isinstance(func, str) and func.startswith('stop'):
                # self.logger.debug(func)
                break
            # noinspection PyBroadException,PyUnusedLocal
            try:
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = await self.loop.run_in_executor(
                        self._thread_pool, functools.partial(func, *args, **kwargs)
                    )
                if result_future is not None:
                    result_future.set_result(result)
            except BaseException as e:
                self.logger.exception(f'func:{func}, args:{args}, kwargs:{kwargs} exc_type:{type(e)}  traceback_exc:{traceback.format_exc()}')
                if result_future is not None:
                    result_future.set_exception(e)
            # self._queue.task_done()

    async def __run(self):
        for _ in range(self._size):
            asyncio.ensure_future(self._consume())

    def _start_loop_in_new_thread(self, ):
        # self._loop.run_until_complete(self.__run())  # 这种也可以。
        # self._loop.run_forever()

        # asyncio.set_event_loop(self.loop)
        # self.loop.run_until_complete(asyncio.wait([self._consume() for _ in range(self._size)], loop=self.loop))
        # self._can_be_closed_flag = True
        if self._specify_async_loop is None:
            for _ in range(self._size):
                self.loop.create_task(self._consume())
        else:
            for _ in range(self._size):
                asyncio.run_coroutine_threadsafe(self._consume(),self.loop) # 这是 asyncio 专门提供的用于从其他线程向事件循环安全提交任务的函数。
        if self._specify_async_loop is None:
            self.loop.run_forever()
        else:
            if self._is_auto_start_specify_async_loop_in_child_thread:
                try:
                    self.loop.run_forever() #如果是指定的loop不能多次启动一个loop.
                except Exception as e:
                    self.logger.warning(f'{e} {traceback.format_exc()}')   # 如果多个线程使用一个loop，不能重复启动loop，否则会报错。
            else:
                pass # 用户需要自己在自己的业务代码中去手动启动loop.run_forever() 


    # def shutdown(self):
    #     if self.loop.is_running():  # 这个可能是atregster触发，也可能是用户手动调用，需要判断一下，不能关闭两次。
    #         for i in range(self._size):
    #             self.submit(f'stop{i}', )
    #         while not self._can_be_closed_flag:
    #             time.sleep(0.1)
    #         self.loop.stop()
    #         self.loop.close()
    #         print('关闭循环')



if __name__ == '__main__':
    
    def test_async_pool_executor():
        from funboost.concurrent_pool import CustomThreadPoolExecutor as ThreadPoolExecutor
        # from concurrent.futures.thread import ThreadPoolExecutor
        # noinspection PyUnusedLocal
        async def f(x):
            await asyncio.sleep(1)
            pass
            print('打印', x)

            # await asyncio.sleep(1)
            # raise Exception('aaa')
            return x * 2

        def f2(x):
            pass
            # time.sleep(0.001)
            print('打印', x)
            return x * 20

        print(1111)

        t1 = time.time()

        pool = AsyncPoolExecutor(20)
        # pool = ThreadPoolExecutor(200)  # 协程不能用线程池运行，否则压根不会执行print打印，对于一部函数 f(x)得到的是一个协程，必须进一步把协程编排成任务放在loop循环里面运行。
        
        # 测试submit方法
        # for i in range(1, 501):
        #     print('放入', i)
        #     fut = pool.submit(f, i)
        #     print(fut.result())

        # time.sleep(5)
        # pool.submit(f, 'hi')
        # pool.submit(f, 'hi2')
        # pool.submit(f, 'hi3')
        # print(2222)

         # 测试map方法
        results = pool.map(f2, [1, 2, 3, 4], timeout=5)
        try:
            for res in results:
                print(res)
        except TimeoutError:
            print("有任务执行超时！")
     
        print(time.time() - t1)


    test_async_pool_executor()
    # test_async_producer_consumer()

   


    print(sys.version_info)
