"""批量运行 using-funboost-basics + understanding-funboost-concepts 代码示例验证"""
import os
import subprocess
import sys
import time

PROJECT_ROOT = r"D:\codes\funboost"
DEMO_DIR = os.path.join(PROJECT_ROOT, "tests", "ai_codes", "ai_demos", "skill_verification")

DEMOS = [
    ("using-funboost-basics", "零依赖 MEMORY_QUEUE 最小示例", "basics_01_memory_queue_add.py"),
    ("using-funboost-basics", "Redis 任务配置示例", "basics_02_redis_task_config.py"),
    ("using-funboost-basics", "push 只传业务参数", "basics_03_push.py"),
    ("using-funboost-basics", "publish + TaskOptions", "basics_04_publish_task_options.py"),
    ("using-funboost-basics", "异步 aio_push/aio_publish", "basics_05_async_publish.py"),
    ("using-funboost-basics", "启动多个消费者", "basics_06_multiple_consumers.py"),
    ("using-funboost-basics", "任务上下文 fct", "basics_07_fct_context.py"),
    ("using-funboost-basics", "外部消息 **kwargs", "basics_08_external_kwargs.py"),
    ("understanding-funboost-concepts", "反框架设计 process", "concepts_01_anti_framework.py"),
    ("understanding-funboost-concepts", "BrokerConnConfig 配置类", "concepts_02_broker_conn_config.py"),
    ("understanding-funboost-concepts", "consume() 非阻塞", "concepts_03_consume_non_blocking.py"),
    ("understanding-funboost-concepts", "fct 上下文（禁止 Celery 思维）", "concepts_04_fct_no_celery.py"),
]

SKIP = [
    ("understanding-funboost-concepts", "Celery bind=True 反例", "文档反例，非 funboost 可运行代码"),
]


def run_demo(script_name):
    env = os.environ.copy()
    env["PYTHONPATH"] = PROJECT_ROOT
    script_path = os.path.join(DEMO_DIR, script_name)
    result = subprocess.run(
        [sys.executable, script_path],
        cwd=PROJECT_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=50,
    )
    return result


if __name__ == "__main__":
    results = []
    print("=" * 70)
    print("Skill 代码示例验证开始")
    print("=" * 70)

    for skill, example, script in DEMOS:
        print(f"\n>>> 运行 {script} ...")
        try:
            r = run_demo(script)
            ok = r.returncode == 66
            err_hint = ""
            if not ok:
                err_hint = (r.stderr or r.stdout)[-800:]
            status = "PASS" if ok else "FAIL"
            results.append((skill, example, script, status, err_hint))
            print(f"    {status} (exit={r.returncode})")
            if not ok:
                print(err_hint)
        except subprocess.TimeoutExpired as e:
            results.append((skill, example, script, "FAIL", "超时 (>50s)"))
            print("    FAIL (timeout)")

    for skill, example, reason in SKIP:
        results.append((skill, example, "-", "SKIP", reason))
        print(f"\n>>> SKIP: {example} — {reason}")

    print("\n" + "=" * 70)
    print("汇总表格")
    print("=" * 70)
    print(f"{'Skill':<35} {'示例':<28} {'脚本':<38} {'结果':<6}")
    print("-" * 110)
    for skill, example, script, status, detail in results:
        print(f"{skill:<35} {example:<28} {script:<38} {status:<6}")
        if status == "FAIL" and detail:
            print(f"  错误: {detail.strip()[:300]}")

    fail_count = sum(1 for *_, s, _ in results if s == "FAIL")
    pass_count = sum(1 for *_, s, _ in results if s == "PASS")
    skip_count = sum(1 for *_, s, _ in results if s == "SKIP")
    print(f"\n总计: PASS={pass_count}, FAIL={fail_count}, SKIP={skip_count}")
    os._exit(1 if fail_count else 0)
