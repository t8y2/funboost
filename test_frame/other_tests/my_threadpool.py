import threading
import queue
import time
import atexit


class DynamicThreadPool:
    """
    一个能根据负载自动伸缩线程数量的动态线程池。
    """

    def __init__(self, min_workers=2, max_workers=10, idle_timeout=60):
        if min_workers <= 0 or max_workers < min_workers:
            raise ValueError("不合理的线程数配置 (0 < min_workers <= max_workers)")

        self.min_workers = min_workers
        self.max_workers = max_workers
        self.idle_timeout = idle_timeout  # 秒

        self._task_queue = queue.Queue()
        self._workers = set()  # 使用集合以方便快速增删
        self._workers_lock = threading.Lock()

        self._is_shutdown = False
        self._shutdown_lock = threading.Lock()

        # 初始化核心线程
        for _ in range(self.min_workers):
            self._create_worker()

        # 创建“经理”线程，负责监控和扩容
        self._manager_thread = threading.Thread(target=self._manager_loop)
        self._manager_thread.daemon = True
        self._manager_thread.start()

        atexit.register(self.shutdown)

    def _create_worker(self):
        """安全地创建一个工作线程。"""
        with self._workers_lock:
            if len(self._workers) >= self.max_workers:
                return  # 已达到最大线程数

            worker = threading.Thread(target=self._worker_loop)
            worker.daemon = True
            worker.start()
            self._workers.add(worker)
            print(f"📈 池中线程数: {len(self._workers)}。创建了一个新线程: {worker.name}")

    def _remove_worker(self, worker):
        """安全地移除一个工作线程，并确保不会低于核心数。"""
        with self._workers_lock:
            # 增加安全检查，防止过度移除
            if len(self._workers) <= self.min_workers:
                return
            if worker in self._workers:
                self._workers.remove(worker)
                # 这行现在可以被触发了！
                print(f"📉 池中线程数: {len(self._workers)}。移除了一个空闲线程: {worker.name}")

    def _worker_loop(self):
        """
        工作线程的循环。
        核心线程会一直等待，临时线程在空闲超时后会退出。
        """
        while True:
            try:
                with self._workers_lock:
                    is_temporary_worker = len(self._workers) > self.min_workers

                timeout = self.idle_timeout if is_temporary_worker else None
                func, args, kwargs = self._task_queue.get(timeout=timeout)

                try:
                    func(*args, **kwargs)
                except Exception as e:
                    print(f"任务执行时发生错误: {e}")
                finally:
                    self._task_queue.task_done()

            except queue.Empty:
                # 只有临时线程在超时后才会到达这里。
                # 既然已经超时，就说明它应该被销毁。移除二次确认。
                self._remove_worker(threading.current_thread())
                return  # 线程自我终结

    def _manager_loop(self):
        """
        “经理”线程的循环，负责按需扩容。
        """
        while not self._is_shutdown:
            time.sleep(1)  # 每秒检查一次

            # 扩容策略：当等待的任务数 > 当前线程数时，且未达到最大线程数，就扩容
            if self._task_queue.qsize() > len(self._workers) and len(self._workers) < self.max_workers:
                print("🚀 任务积压，经理决定扩容...")
                self._create_worker()

    def submit(self, func, *args, **kwargs):
        """向任务队列中提交一个任务。"""
        with self._shutdown_lock:
            if self._is_shutdown:
                raise RuntimeError("线程池已关闭，无法提交新任务")
            self._task_queue.put((func, args, kwargs))

    def shutdown(self, wait=True):
        """
        优雅地关闭线程池，包括经理线程和所有工作线程。
        """
        with self._shutdown_lock:
            if self._is_shutdown:
                return
            print("\n--- atexit: 检测到程序退出，开始关闭线程池... ---")
            self._is_shutdown = True

        if wait:
            self._task_queue.join()
            # 等待经理线程退出
            # self._manager_thread.join() # 因为是守护线程，无需手动join

        print("--- atexit: 所有任务已完成，程序将干净地退出。 ---")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()
        return False


# --- 测试代码 ---
if __name__ == '__main__':
    import random


    def simple_task(task_id, duration):
        print(f"线程 {threading.current_thread().name} 开始执行任务 {task_id}...")
        time.sleep(duration)
        print(f"✅ 线程 {threading.current_thread().name} 完成了任务 {task_id}。")


    print("\n--- 测试动态线程池 DynamicThreadPool ---")

    # 创建一个核心2个，最多10个，空闲5秒就销毁的线程池
    pool = DynamicThreadPool(min_workers=1, max_workers=10, idle_timeout=5)

    # 第一波：瞬间提交大量任务，触发扩容
    print("\n>>> 第一波：提交15个任务，观察扩容...")
    for i in range(15):
        pool.submit(simple_task, task_id=f"B1-{i}", duration=2)

    # 等待一段时间，让任务被消耗，并观察线程因空闲而收缩
    print("\n>>> 等待20秒，观察临时线程是否会自动销毁...")
    time.sleep(20)

    # 第二波：再次提交少量任务
    print("\n>>> 第二波：提交3个任务...")
    for i in range(3):
        pool.submit(simple_task, task_id=f"B2-{i}", duration=1)

    print("\n所有任务已提交。主线程即将结束，等待atexit自动清理...")
    # 主线程结束后，atexit会调用shutdown，等待所有任务完成
    # 你会看到线程数先增加，然后在空闲时减少到min_workers