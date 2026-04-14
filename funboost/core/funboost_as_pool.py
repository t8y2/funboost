"""
写一个 Funboost 通用任务池，支持 submit 任意函数，并返回 Future。
除了实例化入参，最常用的submit方法和 concurrent.futures.ThreadPoolExecutor 一样。例如submit和返回future。
"""

import typing
import concurrent.futures
import inspect
from funboost import BoosterParams, BrokerEnum, Booster, FunctionResultStatus
from funboost.concurrent_pool.flexible_thread_pool import _new_anyio_fun


class FunboostPool:
    """
    一个功能完整的 Funboost 通用任务池。
    支持 submit 任意函数，并返回 Future。
    """

    def __init__(
        self,
        max_workers: int = 4,
        qps: int = 100,
        is_future_direct_ret_result: bool = True,
    ):
        """
        创建一个通用任务池。
        :param max_workers: 最大线程数
        :param qps: 每秒处理消息数
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
    def __init__(
        self,
        booster_params,
        is_future_direct_ret_result: bool = True,
    ):  
        """
        创建一个通用任务池。
        :param booster_params: BoosterParams对象. NbFunboostPool相比FunboostPool有更多的控制入参。
        :param is_future_direct_ret_result: future中是的数据是最终result结果，还是 FunctionResultStatus 对象。
               如果返回FunctionResultStatus的信息更为丰富，包括重试了几次，耗时等等。
               如果返回result结果，那么只有结果，没有其他信息，但是更贴合原原生的 concurrent.futures.Future.result() 方法的返回值。
        :return:
        """
        self.booster_params = booster_params
        self.is_future_direct_ret_result = is_future_direct_ret_result
        self.booster: Booster = None
        self._create_booster()


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



    # 像原生线程池一样随意切换函数
    # pool = NbFunboostPool(
    #     BoosterParams(
    #         queue_name="universal_queue",
    #         broker_kind=BrokerEnum.MEMORY_QUEUE,
    #         concurrent_num=10,
    #     ),
    # )
    pool = FunboostPool(
        max_workers=10,
        qps=100,
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
