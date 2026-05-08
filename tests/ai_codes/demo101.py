"""
fct (funboost current task) 用法 demo

核心用法：from funboost import fct
fct 自动线程/协程隔离，类似 flask 的 request 对象，不需要改函数签名
"""
import time
from funboost import boost, BoosterParams, BrokerEnum, fct

# ============================================================
# 1. 基本用法：在消费函数中通过 fct 获取任务信息
# ============================================================
@boost(BoosterParams(
    queue_name='demo_fct_basic',
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    concurrent_num=2,
))
def task_basic(x: int, y: int):
    """最基础的 fct 用法 —— 函数签名保持纯净，不需要额外入参"""
    print(f"--- basic task ---")
    print(f"task_id  : {fct.task_id}")
    print(f"queue    : {fct.queue_name}")
    print(f"params   : {fct.function_params}")          # {'x': x, 'y': y}
    print(f"full_msg : {fct.full_msg}")                  # 原始消息 dict
    print(f"status   : {fct.function_result_status}")    # FunctionResultStatus 对象
    print(f"str(fct) : {fct}")                           # 自动打印 status dict
    return x + y


# ============================================================
# 2. 重试任务：通过 fct 获取重试次数
# ============================================================
@boost(BoosterParams(
    queue_name='demo_fct_retry',
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    max_retry_times=3,
    is_print_detail_exception=False,
))
def task_retry(n: int):
    """演示 fct.function_result_status.run_times 获取重试次数"""
    if n <= 8:
        print(f"[重试任务] 输入 {n} 模拟失败，当前是第 {fct.function_result_status.run_times} 次运行...")
        raise ValueError("模拟出错啦")
    print(f"[重试任务] 输入 {n} 成功处理！task_id={fct.task_id}, "
          f"发布时间={fct.function_result_status.publish_time_format}")


# ============================================================
# 3. FctContextThread：自动传递上下文到子线程
# ============================================================
from funboost.core.current_task import FctContextThread

def _sub_thread_worker():
    """子线程中仍然能拿到父线程的 fct 上下文"""
    print(f"  [子线程] task_id = {fct.task_id}, queue = {fct.queue_name}")


@boost(BoosterParams(
    queue_name='demo_fct_thread',
    broker_kind=BrokerEnum.MEMORY_QUEUE,
))
def task_context_thread(msg: str):
    """使用 FctContextThread 让子线程自动继承 fct 上下文"""
    _ = msg  # 参数已通过 fct.function_params 间接展示
    print(f"--- context_thread task ---")
    print(f"  [父线程] task_id = {fct.task_id}")
    t = FctContextThread(target=_sub_thread_worker)
    t.start()
    t.join()


# ============================================================
# 4. 在消费函数外使用 fct（无上下文场景）
# ============================================================
from funboost.core.current_task import get_current_taskid

def demo_outside_context():
    """演示不在消费函数中调用 fct 的行为"""
    taskid = get_current_taskid()
    print(f"outside context task_id = '{taskid}'")  # 输出 'no_task_id'


# ============================================================
# 运行 demo
# ============================================================
if __name__ == '__main__':
    # 1. 启动消费者
    task_basic.consume()
    task_retry.consume()
    task_context_thread.consume()

    time.sleep(0.5)
    print("=== 消费者已启动，开始发布任务 ===\n")

    # 2. 发布基础任务
    print("--- 发布基础任务 ---")
    task_basic.push(10, y=20)
    task_basic.push(100, y=200)

    time.sleep(1)

    # 3. 发布重试任务
    print("\n--- 发布重试任务 ---")
    task_retry.push(5)       # 会失败并重试 3 次
    task_retry.push(6666)    # 直接成功

    time.sleep(2)

    # 4. 发布子线程上下文传递任务
    print("\n--- 发布子线程上下文传递任务 ---")
    task_context_thread.push("hello funboost")

    time.sleep(1)

    # 5. 消费函数外部使用
    print("\n--- 消费函数外部使用 fct ---")
    demo_outside_context()
