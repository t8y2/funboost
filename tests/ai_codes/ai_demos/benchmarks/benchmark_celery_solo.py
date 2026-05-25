import os, time, sys, threading

os.environ["LOG_PATH"] = 'd:/pythonlogs/ai_console_outs'
os.environ['PRINT_WRTIE_FILE_NAME'] = 'bm_celery_solo_print.print'
os.environ['SYS_STD_FILE_NAME'] = 'bm_celery_solo_std.std'
# 关键：关闭 stdout/stderr 重定向

from celery import Celery, Task as CeleryTask

TOTAL = 20000
counter = {'done': 0}
lock = threading.Lock()
start = [None]
results = {}

app = Celery('bm_celery', broker='redis://127.0.0.1:6379/12')
app.conf.task_acks_late = True
app.conf.worker_redirect_stdouts = False
app.conf.task_ignore_result = True




@app.task(bind=True, name='bm_celery_task', max_retries=0)
def bench_task(self, msg_id: int):
    with lock:
        counter['done'] += 1
        c = counter['done']
        if start[0] is None:
            start[0] = time.time()
        if c == TOTAL:
            elapsed = time.time() - start[0]
            results['consume'] = {'count': TOTAL, 'elapsed': elapsed, 'rate': TOTAL / elapsed}

if __name__ == '__main__':
    import redis
    rr = redis.Redis(host='127.0.0.1', port=6379, db=12)
    rr.delete('celery')

    t0 = time.time()
    for i in range(TOTAL):
        bench_task.delay(msg_id=i)
    pub_time = time.time() - t0
    results['publish'] = {'count': TOTAL, 'elapsed': pub_time, 'rate': TOTAL / pub_time}
    sys.stdout.write(f'CELERY_PUBLISH|{TOTAL}|{pub_time:.4f}|{TOTAL/pub_time:.0f}\n')
    sys.stdout.flush()

    worker = threading.Thread(
        target=app.worker_main,
        args=(['worker', '--pool=solo', '-n', 'bm_worker@%h',
               '--loglevel=CRITICAL', '--concurrency=1',
               '--queues=celery'],),
        daemon=True
    )
    worker.start()
    time.sleep(10)

    for _ in range(1800):
        time.sleep(0.5)
        if 'consume' in results:
            break
    r = results.get('consume', {})
    sys.stdout.write(f'CELERY_CONSUME|{r.get("count", 0)}|{r.get("elapsed", 0):.4f}|{r.get("rate", 0):.0f}\n')
    sys.stdout.flush()
    os._exit(66)