"""
Funboost 性能 Benchmark V2 —— 单线程模式（纯 CPU 任务）
消费 10 万条消息，每 1 万条打印时间
"""
import os
import time
import sys

os.environ["LOG_PATH"] = 'd:/pythonlogs/ai_console_outs'
os.environ['PRINT_WRTIE_FILE_NAME'] = 'benchmark_funboost_v2_print.print'
os.environ['SYS_STD_FILE_NAME'] = 'benchmark_funboost_v2_std.std'

import nb_log  # noqa
from funboost import boost, BoosterParams, BrokerEnum, ConcurrentModeEnum

TOTAL_MSGS = 100000
BATCH_SIZE = 10000

import threading
counter = {'processed': 0}
lock = threading.Lock()
start_time = [None]


@boost(BoosterParams(
    queue_name="benchmark_funboost_queue_v2",
    broker_kind=BrokerEnum.REDIS,
    concurrent_num=1,
    concurrent_mode=ConcurrentModeEnum.SINGLE_THREAD,
    qps=None,
    max_retry_times=0,
    is_using_rpc_mode=False,
    create_logger_file=False,
    log_level=30,
))
def bench_task(msg_id: int):
    with lock:
        counter['processed'] += 1
        count = counter['processed']
        if start_time[0] is None:
            start_time[0] = time.time()
        if count % BATCH_SIZE == 0:
            elapsed = time.time() - start_time[0]
            rate = count / elapsed if elapsed > 0 else 0
            print(f'[FunboostV2] 已处理 {count}/{TOTAL_MSGS} 条, 耗时 {elapsed:.2f}秒, {rate:.0f} msg/s')


if __name__ == '__main__':
    print(f'[FunboostV2] 开始发布 {TOTAL_MSGS} 条消息到 Redis...')
    t0 = time.time()
    for i in range(TOTAL_MSGS):
        if i > 0 and i % 10000 == 0:
            print(f'  已发布 {i} 条...')
        bench_task.push(msg_id=i)
    publish_time = time.time() - t0
    print(f'[FunboostV2] 发布完成，耗时 {publish_time:.2f}秒, 平均 {TOTAL_MSGS/publish_time:.0f} msg/s')
    print()

    print(f'[FunboostV2] 开始消费 {TOTAL_MSGS} 条消息...')
    bench_task.consume()

    sleep_time = 60  # 单线程较慢，给 60 秒
    print(f'\n[FunboostV2] 等待 {sleep_time} 秒后自动退出...')
    time.sleep(sleep_time)

    with lock:
        final_count = counter['processed']
    total_elapsed = time.time() - start_time[0] if start_time[0] else 0
    final_rate = final_count / total_elapsed if total_elapsed > 0 else 0
    print(f'\n===== FunboostV2(单线程) Benchmark 结果 =====')
    print(f'总发布: {TOTAL_MSGS} 条 | 总消费: {final_count} 条')
    print(f'消费耗时: {total_elapsed:.2f}秒')
    print(f'平均吞吐量: {final_rate:.0f} msg/s')
    print(f'============================================\n')
    os._exit(66)