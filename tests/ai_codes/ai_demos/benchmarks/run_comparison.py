"""
运行测试funboost 和celery的发布和消费吞吐速率对比，

测试用的几乎是没逻辑的空函数，这就是阿姆达尔定律——框架开销占业务耗时的比例趋近于零，所有框架看起来都一样。
所以测框架性能必须让业务函数尽量空，才能剥离出框架本身的调度开销差
"""

import subprocess, sys, os, time

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(SCRIPTS_DIR))))

env = os.environ.copy()
env['PYTHONPATH'] = ROOT

def run_bench(script_name, label, timeout):
    script = os.path.join(SCRIPTS_DIR, script_name)
    print(f'===== 运行 {label} Benchmark =====')
    sys.stdout.flush()
    t0 = time.time()
    proc = subprocess.run(
        ['python', script],
        cwd=ROOT,
        timeout=timeout,
        capture_output=True, text=True,
        env=env
    )
    elapsed = time.time() - t0
    lines = [l for l in proc.stdout.strip().split('\n') if '|' in l]
    result = {}
    for l in lines:
        parts = l.strip().split('|')
        if len(parts) == 4:
            key, n, t, r = parts
            result[key] = {'count': int(n), 'elapsed': float(t), 'rate': float(r)}
    return result, elapsed

fb_result, fb_total = run_bench('benchmark_funboost_singlethread.py', 'Funboost(单线程)', 600)
cl_result, cl_total = run_bench('benchmark_celery_solo.py', 'Celery(solo)', 1200)

print()
print('=' * 70)
print('               Funboost vs Celery 性能对比 (Redis, 单线程模式)')
print('=' * 70)
print(f'Funboost: 500,000 条 | Celery: 20,000 条')
print()

for label, r in [('Funboost SINGLE_THREAD', fb_result), ('Celery solo', cl_result)]:
    pub = r.get('FUNBOOST_PUBLISH') or r.get('CELERY_PUBLISH') or {}
    con = r.get('FUNBOOST_CONSUME') or r.get('CELERY_CONSUME') or {}
    print(f'--- {label} ---')
    print(f'  发布: {pub.get("count", "N/A")} 条 | {pub.get("elapsed", "N/A"):>8.2f}秒 | {pub.get("rate", "N/A"):>8.0f} msg/s')
    print(f'  消费: {con.get("count", "N/A")} 条 | {con.get("elapsed", "N/A"):>8.2f}秒 | {con.get("rate", "N/A"):>8.0f} msg/s')
    print()

fb_rate = fb_result.get('FUNBOOST_CONSUME', {}).get('rate', 0)
cl_rate = cl_result.get('CELERY_CONSUME', {}).get('rate', 0)
if fb_rate and cl_rate:
    ratio = fb_rate / cl_rate
    print(f'>>> 消费吞吐量倍数: Funboost 是 Celery 的 {ratio:.1f} 倍')
    if ratio > 1:
        print(f'>>> Funboost 快 {ratio:.1f} 倍')
    else:
        print(f'>>> Celery 快 {1/ratio:.1f} 倍')

fb_pub = fb_result.get('FUNBOOST_PUBLISH', {}).get('rate', 0)
cl_pub = cl_result.get('CELERY_PUBLISH', {}).get('rate', 0)
if fb_pub and cl_pub:
    pub_ratio = fb_pub / cl_pub
    print(f'>>> 发布吞吐量倍数: Funboost 是 Celery 的 {pub_ratio:.1f} 倍')

print('=' * 70)