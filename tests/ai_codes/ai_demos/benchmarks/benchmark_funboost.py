"""
Funboost 性能 Benchmark —— 消费 10 万条消息，每 1 万条打印时间
"""
import os
import time
import sys

# ========== 环境变量设置（方便 AI 读取日志文件） ==========
os.environ["LOG_PATH"] = 'd:/pythonlogs/ai_console_outs'
os.environ['PRINT_WRTIE_FILE_NAME'] = 'benchmark_funboost_print.print'
os.environ['SYS_STD_FILE_NAME'] = 'benchmark_funboost_std.std'

import nb_log  # noqa
from funboost import boost, BoosterParams, BrokerEnum, ctrl_c_recv

TOTAL_MSGS = 100000
BATCH_SIZE = 10000

# 全局计数器（使用可变对象实现跨线程共享）
import threading
counter = {'processed': 0}
lock = threading.Lock()
start_time = [None]  # 记录开始时间


@boost(BoosterParams(
    queue_name="benchmark_funboost_queue",
    broker_kind=BrokerEnum.REDIS,   # Redis 做中间件
    concurrent_num=200,              # 200 线程并发
    qps=None,                        # 不限制 QPS，追求最大吞吐量
    max_retry_times=0,               # 不重试
    is_using_rpc_mode=False,         # 不开启 RPC，追求最高性能
    create_logger_file=False,        # 不写框架日志文件
    log_level=30,                    # WARNING 级别，减少日志输出
))
def bench_task(msg_id: int):
    """简单的任务，每处理 10000 条打印一次时间"""
    with lock:
        counter['processed'] += 1
        count = counter['processed']
        if start_time[0] is None:
            start_time[0] = time.time()
        if count % BATCH_SIZE == 0:
            elapsed = time.time() - start_time[0]
            rate = count / elapsed if elapsed > 0 else 0
            print(f'[Funboost] 已处理 {count}/{TOTAL_MSGS} 条消息, 耗时 {elapsed:.2f}秒, 吞吐量 {rate:.0f} msg/s')


if __name__ == '__main__':
    # ========== 第一阶段：发布 10 万条消息 ==========
    print(f'[Funboost] 开始发布 {TOTAL_MSGS} 条消息到 Redis...')
    t0 = time.time()
    for i in range(TOTAL_MSGS):
        # 分段发布，避免一次全发布导致内存暴涨
        if i > 0 and i % 10000 == 0:
            print(f'  已发布 {i} 条...')
        bench_task.push(msg_id=i)
    publish_time = time.time() - t0
    print(f'[Funboost] 发布完成，耗时 {publish_time:.2f}秒, 平均 {TOTAL_MSGS/publish_time:.0f} msg/s')
    print()

    # ========== 第二阶段：开始消费 ==========
    print(f'[Funboost] 开始消费 {TOTAL_MSGS} 条消息...')
    bench_task.consume()

    # ========== 等待消费并超时退出 ==========
    # 预计：200并发 * 极轻量任务 ≈ 每秒几万到十几万，10万条预计 3-15 秒
    # 给 Buffer 30 秒
    sleep_time = 30
    print(f'\n[Funboost] 等待 {sleep_time} 秒后自动退出...')
    time.sleep(sleep_time)
    
    with lock:
        final_count = counter['processed']
    total_elapsed = time.time() - start_time[0] if start_time[0] else 0
    final_rate = final_count / total_elapsed if total_elapsed > 0 else 0
    print(f'\n===== Funboost Benchmark 结果 =====')
    print(f'总发布: {TOTAL_MSGS} 条 | 总消费: {final_count} 条')
    print(f'消费耗时: {total_elapsed:.2f}秒')
    print(f'平均吞吐量: {final_rate:.0f} msg/s')
    print(f'===================================\n')
    os._exit(66)
