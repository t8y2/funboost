"""
Celery 性能 Benchmark（精简版）—— 消费 1 万条消息，每 1000 条打印时间
"""
import os
import time
import sys
import threading

os.environ["LOG_PATH"] = 'd:/pythonlogs/ai_console_outs'
os.environ['PRINT_WRTIE_FILE_NAME'] = 'benchmark_celery_v2_print.print'
os.environ['SYS_STD_FILE_NAME'] = 'benchmark_celery_v2_std.std'

import nb_log  # noqa

from celery import Celery, Task as CeleryTask

TOTAL_MSGS = 10000
BATCH_SIZE = 1000

counter = {'processed': 0}
lock = threading.Lock()
start_time = [None]

celery_app = Celery(
    'benchmark',
    broker='redis://127.0.0.1:6379/12',
    backend='redis://127.0.0.1:6379/13',
)
celery_app.conf.task_acks_late = True
celery_app.conf.worker_redirect_stdouts = False
celery_app.conf.update({
    'worker_concurrency': 200,
    'task_ignore_result': True,  # 不保存结果
})


@celery_app.task(bind=True, name='bench_task_v2', max_retries=0)
def bench_task(self: CeleryTask, msg_id: int):
    with lock:
        counter['processed'] += 1
        count = counter['processed']
        if start_time[0] is None:
            start_time[0] = time.time()
        if count % BATCH_SIZE == 0:
            elapsed = time.time() - start_time[0]
            rate = count / elapsed if elapsed > 0 else 0
            print(f'[Celery] 已处理 {count}/{TOTAL_MSGS} 条消息, 耗时 {elapsed:.2f}秒, 吞吐量 {rate:.0f} msg/s')


if __name__ == '__main__':
    # 预热发布连接
    print('[Celery] 预热发布连接...')
    bench_task.delay(msg_id=0)
    time.sleep(0.5)
    # 清理预热消息
    import redis
    rr = redis.Redis(host='127.0.0.1', port=6379, db=12)
    rr.delete('bench_task_v2')

    # ===== 发布 =====
    print(f'[Celery] 开始发布 {TOTAL_MSGS} 条消息到 Redis...')
    t0 = time.time()
    for i in range(TOTAL_MSGS):
        if i > 0 and i % 2000 == 0:
            print(f'  已发布 {i} 条...')
        bench_task.delay(msg_id=i)
    publish_time = time.time() - t0
    print(f'[Celery] 发布完成，耗时 {publish_time:.2f}秒, 平均 {TOTAL_MSGS/publish_time:.0f} msg/s')
    print()

    # ===== 消费 =====
    print(f'[Celery] 启动 Worker 开始消费...')
    worker_thread = threading.Thread(
        target=celery_app.worker_main,
        args=(['worker', '--pool=threads', '-n', 'worker_bm@%h',
               '--loglevel=WARNING', '--concurrency=200',
               '--queues=celery'],),
        daemon=True
    )
    worker_thread.start()
    time.sleep(8)  # 等待 Worker 就绪
    print('[Celery] Worker 已启动...')

    sleep_time = 60
    print(f'\n[Celery] 等待 {sleep_time} 秒后自动退出...')
    time.sleep(sleep_time)

    with lock:
        final_count = counter['processed']
    total_elapsed = time.time() - start_time[0] if start_time[0] else 0
    final_rate = final_count / total_elapsed if total_elapsed > 0 else 0
    print(f'\n===== Celery Benchmark 结果 =====')
    print(f'总发布: {TOTAL_MSGS} 条 | 总消费: {final_count} 条')
    print(f'消费耗时: {total_elapsed:.2f}秒')
    print(f'平均吞吐量: {final_rate:.0f} msg/s')
    print(f'=================================\n')
    os._exit(66)

