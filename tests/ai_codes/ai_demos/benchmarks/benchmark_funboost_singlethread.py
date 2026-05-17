import os, time, sys, threading

os.environ["LOG_PATH"] = 'd:/pythonlogs/ai_console_outs'
os.environ['PRINT_WRTIE_FILE_NAME'] = 'bm_funboost_st_print.print'
os.environ['SYS_STD_FILE_NAME'] = 'bm_funboost_st_std.std'

import nb_log
from funboost import boost, BoosterParams, BrokerEnum, ConcurrentModeEnum

TOTAL = 100000
counter = {'done': 0}
lock = threading.Lock()
start = [None]
results = {}

@boost(BoosterParams(
    queue_name="bm_funboost_st",
    broker_kind=BrokerEnum.REDIS,
    concurrent_mode=ConcurrentModeEnum.SINGLE_THREAD,
    concurrent_num=1,
    qps=None, max_retry_times=0, is_using_rpc_mode=False,
    create_logger_file=False, log_level=30,
))
def task(msg_id: int):
    with lock:
        counter['done'] += 1
        c = counter['done']
        if start[0] is None:
            start[0] = time.time()
        if c == TOTAL:
            elapsed = time.time() - start[0]
            results['consume'] = {'count': TOTAL, 'elapsed': elapsed, 'rate': TOTAL / elapsed}

if __name__ == '__main__':
    t0 = time.time()
    for i in range(TOTAL):
        task.push(msg_id=i)
    pub_time = time.time() - t0
    results['publish'] = {'count': TOTAL, 'elapsed': pub_time, 'rate': TOTAL / pub_time}
    sys.stdout.write(f'FUNBOOST_PUBLISH|{TOTAL}|{pub_time:.4f}|{TOTAL/pub_time:.0f}\n')
    sys.stdout.flush()

    task.consume()
    for _ in range(600):
        time.sleep(0.5)
        if 'consume' in results:
            break
    r = results.get('consume', {})
    sys.stdout.write(f'FUNBOOST_CONSUME|{r.get("count", 0)}|{r.get("elapsed", 0):.4f}|{r.get("rate", 0):.0f}\n')
    sys.stdout.flush()
    os._exit(66)