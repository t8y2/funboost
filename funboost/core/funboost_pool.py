"""
写一个 Funboost 通用任务池，支持 submit 任意函数，并返回 Future。
除了实例化入参，最常用的submit方法和 concurrent.futures.ThreadPoolExecutor 一样。例如submit和返回future。
所以用户可以使用 FunboostPool 或者 NbFunboostPool 的实例化对象替代之前的 ThreadPoolExecutor的对象。一般用户只用到pool.submit，基本完美平替，只需要修改一行代码。

funboostpool 比 ThreadPoolExecutor更强的在于，可以内存存储任务，也可以分布式消息队列存任务。
funboostpool 有几十种任务控制功能，例如重试策略，超时策略，任务优先级。
funboostpool 能支持asyncio任务和同步任务，ThreadPoolExecutor 没这个能力
funboostpool 的池子可以自动扩大和自动缩小，ThreadPoolExecutor 不能自动缩小。
NbFunboostPool 拥有funboost的所有能力
"""

import typing
import concurrent.futures
import inspect
from funboost import BoosterParams, BrokerEnum, Booster, FunctionResultStatus, AsyncResult
from funboost.concurrent_pool.flexible_thread_pool import _new_anyio_fun,FlexibleThreadPoolMinWorkers0



class FunboostPool:
    """
    一个功能完整的 Funboost 通用任务池。
    支持 submit 任意函数，并返回 Future。
    """

    def __init__(
        self,
        max_workers: int = 4,
        qps: int = 100,
        is_need_result : bool = False,
        is_future_direct_ret_result: bool = True,
    ):
        """
        创建一个通用任务池。
        :param max_workers: 最大线程数
        :param qps: 每秒处理消息数
        :param is_need_result: 是否需要返回执行结果,如果不关心结果只执行，可以减少性能损耗
        :param is_future_direct_ret_result: future中是的数据是最终result结果，还是 FunctionResultStatus 对象。
               如果返回FunctionResultStatus对象，那么信息更为丰富，包括重试了几次，耗时等等。
               如果返回result结果，那么只有结果，没有其他信息，但是更贴合原生的 concurrent.futures.Future.result() 方法的返回值。
        :return:
        """
        self.max_workers = max_workers
        self.qps = qps
        self.booster: Booster = None
        # self._pool_queue_name = f"universal_pool_{id(self)}"
        
        self.booster_params = BoosterParams(
            queue_name=f"universal_pool_{id(self)}",
            concurrent_num=self.max_workers,
            qps=self.qps,
            broker_kind=BrokerEnum.MEMORY_QUEUE,
        )
        self.is_need_result = is_need_result
        self.is_future_direct_ret_result = is_future_direct_ret_result
        self._create_booster()

    def _create_booster(self):
        # 核心：定义一个通用的消费函数，它不关心业务逻辑，只负责执行消息中携带的 "函数和参数"
        def universal_consumer(task_data: dict):
            func = task_data["func"]
            args = task_data.get("args", ())
            kwargs = task_data.get("kwargs", {})
            return _new_anyio_fun(func,args,kwargs,self.booster_params.specify_async_loop,self.booster_params.is_auto_start_specify_async_loop_in_child_thread)


        # 使用这个通用消费者创建 Booster，只创建一次！
        self.booster = Booster(self.booster_params)(universal_consumer)

        # 启动后台消费线程
        self.booster.consume()

    def submit(self, fn: typing.Callable, *args, **kwargs) -> concurrent.futures.Future:
        """
        提交任意函数 fn 到线程池执行。
        :param fn: 要执行的函数
        :param args: 位置参数
        :param kwargs: 关键字参数
        :return: concurrent.futures.Future 对象
        """
        # 将函数和参数打包成一个字典，直接放进消息队列
        # 因为用的是 MEMORY_QUEUE，函数对象不会被序列化，而是直接传递引用！
        task_data = {"func": fn, "args": args, "kwargs": kwargs}
        if self.is_need_result is False:
            self.booster.push(task_data)
            return None

        # 使用 publisher 的 get_future 方法，直接返回 Future 对象
        raw_future = self.booster.publisher.get_future(task_data)
        if self.is_future_direct_ret_result is False:
            return raw_future
        else:
            # 2. 创建一个新的 Future，用于承载真正的业务返回值
            final_future = concurrent.futures.Future()

            # 3. 当 raw_future 完成时，提取业务结果并设置到 final_future
            def on_raw_future_done(fut):
                try:
                    # raw_future.result() 返回的是 FunctionResultStatus 对象
                    status: FunctionResultStatus = fut.result()
                    if status.success:
                        # 关键：把真正的业务结果设置给 final_future
                        final_future.set_result(status.result)
                    else:
                        # 如果业务执行失败，抛出异常
                        final_future.set_exception(Exception(status.exception))
                except Exception as e:
                    final_future.set_exception(e)

            raw_future.add_done_callback(on_raw_future_done)
            return final_future

    def shutdown(self, wait: bool = True):
        """关闭线程池（内存队列无需特殊清理）"""
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()


class NbFunboostPool(FunboostPool):
    """
    NbFunboostPool 比 FunboostPool 能设置更多的控制参数，支持精细化设置 BoosterParams 所有控制入参，例如重试等。
    """

    def __init__(
        self,
        booster_params,
        is_need_result = False,
        is_future_direct_ret_result: bool = True,
    ):  
        """
        创建一个通用任务池。
        :param booster_params: BoosterParams 对象. NbFunboostPool相比FunboostPool有更多的控制入参。
        :param is_need_result: 是否需要返回执行结果,如果不关心结果只执行，可以不使用rpc模式，不依赖redis做rpc，节约redis空间和性能。
        :param is_future_direct_ret_result: future中是的数据是最终result结果，还是 FunctionResultStatus 对象。
               如果返回FunctionResultStatus的信息更为丰富，包括重试了几次，耗时等等。
               如果返回result结果，那么只有结果，没有其他信息，但是更贴合原原生的 concurrent.futures.Future.result() 方法的返回值。
        :return:
        """
        self.booster_params = booster_params
        if self.booster_params.broker_kind != BrokerEnum.MEMORY_QUEUE and is_need_result is True :
            self.booster_params.is_using_rpc_mode = True
            self._callback_run_executor = FlexibleThreadPoolMinWorkers0(self.booster_params.concurrent_num,)
        self.is_need_result = is_need_result
        self.is_future_direct_ret_result = is_future_direct_ret_result
        self.booster: Booster = None
        self._create_booster()
        
    def submit(self, fn: typing.Callable, *args, **kwargs) -> concurrent.futures.Future:
        # 1. 如果是内存队列，直接复用父类的高效实现（底层用 get_future）
        if self.booster_params.broker_kind == BrokerEnum.MEMORY_QUEUE:
            return super().submit(fn, *args, **kwargs)
        task_data = {"func": fn, "args": args, "kwargs": kwargs}
        if self.is_need_result is False:
            self.booster.push(task_data)
            return None

        # 2. 如果是分布式队列，走标准 RPC 回调封装
        
        async_result: AsyncResult = self.booster.push(task_data)
        async_result.callback_run_executor = self._callback_run_executor

        final_future = concurrent.futures.Future()

        def rpc_callback(status_and_result: dict):
            try:
                status = FunctionResultStatus.parse_status_and_result_to_obj(status_and_result)
                if self.is_future_direct_ret_result:
                    if status.success:
                        final_future.set_result(status.result)
                    else:
                        final_future.set_exception(Exception(f"Task failed: {status.exception}"))
                else:
                    final_future.set_result(status)
            except Exception as e:
                final_future.set_exception(e)

        async_result.set_callback(rpc_callback)
        return final_future


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
    
    # 能执行asyncio函数，而且能支持指定asyncio loop，能自动启动指定的asyncio loop，例如某些aio的连接池的包，需要实例化和发请求在同一个loop。
    async def aio_fun(x):
        await asyncio.sleep(1)
        return x * 10


    # pool = FunboostPool(
    #     max_workers=10,
    #     qps=100,
    #     is_future_direct_ret_result=True,
    # )

    # 像原生线程池一样随意切换函数， 
    pool = NbFunboostPool(
        BoosterParams(
            queue_name="universal_queue",
            broker_kind=BrokerEnum.REDIS,
            concurrent_num=10,
            
        ),
        is_need_result=True,
        is_future_direct_ret_result=True,
    )
    

    # 提交加法
    f1 = pool.submit(add, 5, 3)
    # 提交乘法
    f2 = pool.submit(multiply, 4, 7)
    # 提交带关键字参数的函数
    f3 = pool.submit(greet, name="Funboost")

    f4 = pool.submit(aio_fun, 5)

    res1 = f1.result()  # 8
    print(type(res1), res1)

    print(f2.result())  # 28
    print(f3.result())  # Hello, Funboost
    print(f4.result())  # 50
