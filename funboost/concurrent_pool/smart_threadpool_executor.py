"""
SmartThreadPoolExecutor —— 轻量级自适应线程池

核心特性：
    1. 动态扩缩容：线程按需创建，空闲超过 keep_alive 秒后自动退出，无需手动管理线程生命周期。
    2. 有界队列背压：使用有界 Queue，当队列满时 submit 调用阻塞，防止生产者过快导致内存溢出。
    3. 精确状态追踪：通过 _total_threads / _free_threads 两个计数器精确判断是否需要扩容，
       避免传统线程池"先入队再判断"导致的无效唤醒或过度创建。
    4. 兼容 concurrent.futures.Executor 接口：支持 submit / map / shutdown 标准方法，
       返回 Future 对象，可无缝替换 ThreadPoolExecutor。

扩容策略：
    submit 时，若当前无空闲线程（_free_threads == 0）且线程总数未达上限，则立即创建新线程。

缩容策略：
    工作线程在 keep_alive 时间内未获取到任务则尝试退出；
    退出前双重检查队列是否为空，防止在获取锁期间新任务入队导致的漏执行。

适用场景：
    - IO 密集型任务的并发执行
    - 任务提交速率波动较大、需要线程数自适应的场景
    - 需要背压控制防止内存膨胀的生产者-消费者模型

注意：
    - shutdown() 为空实现，线程依赖 keep_alive 超时自动退出，无需显式关闭
    - 线程设置为 daemon=False，确保进程退出前所有已提交任务执行完毕
"""
import threading
import queue
import time
import os
from concurrent.futures import Future, Executor
from typing import Callable, Optional


class SmartThreadPoolExecutor:


    def __init__(self, max_workers: Optional[int] = None, keep_alive: float = 2.0, max_queue_size: int = 10):
        self.max_workers = max_workers or (os.cpu_count() or 1) * 5
        self.keep_alive = keep_alive
        self.max_queue_size = max_queue_size

        # 使用有界队列，实现背压控制
        self._task_queue = queue.Queue(maxsize=max_queue_size)
        self._lock = threading.Lock()

        # 核心状态机变量（精确控制）
        self._total_threads = 0   # 当前存活的线程总数
        self._free_threads = 0    # 当前空闲（阻塞在 get 上）的线程数

    def _worker(self) -> None:
        """工作线程主循环，具备精准的扩缩容逻辑"""
        while True:
            # 每一轮先标记为空闲，再阻塞等待任务。
            with self._lock:
                self._free_threads += 1

            try:
                # 带空闲超时地获取任务
                task = self._task_queue.get(timeout=self.keep_alive)
            except queue.Empty:
                # 超时后进入缩容决策区
                with self._lock:
                    self._free_threads -= 1
                    # 【关键防御：双重检查】
                    # 如果在获取锁的瞬间，队列恰好有任务被塞入，则必须放弃自杀，继续工作
                    if not self._task_queue.empty():
                        continue

                    # 确保缩容后线程数不低于 0（防御性编程）
                    if self._total_threads > 0:
                        self._total_threads -= 1
                        # 退出循环，线程自然消亡
                        return
                    else:
                        # 理论上不会走到这里，但若出现异常状态，继续等待
                        continue

            # --- 成功获取到任务 ---
            # 执行任务前，线程不再空闲
            with self._lock:
                self._free_threads -= 1

            future, func, args, kwargs = task
            # 执行用户任务
            if future.set_running_or_notify_cancel():
                try:
                    result = func(*args, **kwargs)
                except BaseException as e:
                    future.set_exception(e)
                else:
                    future.set_result(result)

    def submit(self, func: Callable, *args, **kwargs) -> Future:
        """
        提交任务，返回 Future。
        严格遵循：先扩容（若需）并尽量锁内入队，再锁外阻塞背压。
        """
        future = Future()
        task = (future, func, args, kwargs)
        put_in_lock_success = False

        # 1. 扩容决策（仅依赖精确状态变量）
        with self._lock:
            # 扩容黄金法则：只有当没有空闲线程能立即接客，且总数未达上限时才创建新线程
            need_new_thread = (self._free_threads == 0 and self._total_threads < self.max_workers)
            if need_new_thread:
                t = threading.Thread(target=self._worker, daemon=False)
                t.start()
                self._total_threads += 1
                # 注意：_free_threads 会在新线程的 _worker 启动后自行 +1

            # 2. 优先锁内快速入队，避免 submit 与 worker 缩容之间出现竞态窗口。
            try:
                self._task_queue.put_nowait(task)
                put_in_lock_success = True
            except queue.Full:
                pass

        # 3. 若锁内入队失败，退到锁外阻塞背压。
        # 如果队列满，put 会阻塞，直到有线程取出任务。这正是有界队列的“背压”效果。
        if not put_in_lock_success:
            self._task_queue.put(task)
        return future

    # 兼容官方 Executor 接口
    map = Executor.map

    def shutdown(self, wait: bool = True) -> None:
        """线程池关闭接口（本实现依赖线程 keep_alive 超时自动退出，无需额外动作），无需queue.task_done() ,所以无需 queue.join(),无需人工shutdown，无需自动atexit判断"""
        pass


# ------------------- 测试代码 -------------------
if __name__ == "__main__":
    print("=== 优化版 SmartThreadPoolExecutor 测试 ===")
    pool = SmartThreadPoolExecutor(max_workers=4, keep_alive=2.0, max_queue_size=2)

    def job(n: int) -> str:
        tid = threading.current_thread().native_id
        print(f"[开始] 任务 {n:02d} | 线程 {tid}")
        time.sleep(1.5)  # 模拟 IO 操作
        print(f"[结束] 任务 {n:02d} | 线程 {tid}")
        return f"res_{n}"

    # 场景：密集提交任务，观察线程扩缩容及队列背压
    print("\n>>> 提交 10 个任务，每个耗时 1.5s，队列容量 2")
    futures = []
    for i in range(10):
        print(f"提交任务 {i:02d} ...")
        fut = pool.submit(job, i)
        futures.append(fut)
        time.sleep(0.3)  # 模拟间隔提交

    # 等待所有任务完成
    for fut in futures:
        fut.result()

    # 等待观察线程缩容
    print("\n>>> 所有任务完成，等待缩容...")
    # time.sleep(3)

    print("\n=== 测试 map 方法 ===")
    results = pool.map(lambda x: x * 10, [1, 2, 3])
    print("map 结果:", list(results))

    print("\n✅ 测试结束")