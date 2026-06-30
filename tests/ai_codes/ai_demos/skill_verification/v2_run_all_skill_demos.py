"""批量运行 v2_ skill 验证脚本并汇总结果"""
import os
import subprocess
import sys
import time

ROOT = r"D:\codes\funboost"
DEMO_DIR = os.path.join(ROOT, "tests", "ai_codes", "ai_demos", "skill_verification")

DEMOS = [
    ("memory-queue-pool §4.1 MemoryFunboostPool", "v2_memory_funboost_pool_basic.py"),
    ("memory-queue-pool §4.2 FunboostPool+REDIS", "v2_funboost_pool_redis.py"),
    ("memory-queue-pool §5.1 get_future", "v2_get_future_boost.py"),
    ("memory-queue-pool §6 broker切换", "v2_broker_switch_pattern.py"),
    ("memory-queue-pool §7 示例A", "v2_example_a_boost_threadpool.py"),
    ("memory-queue-pool §7 示例B", "v2_example_b_memory_pool_context.py"),
    ("memory-queue-pool §7 示例C", "v2_example_c_get_future_sync_async.py"),
    ("memory-queue-pool §7 示例D", "v2_example_d_unpickleable_args.py"),
    ("funweb-ops §概述 导入路径", "v2_funweb_import_paths.py"),
    ("funweb-ops §1 start_funboost_web_manager", "v2_funweb_start_manager_call.py"),
    ("funweb-ops §3 WebOpsBoosterParams", "v2_funweb_webops_booster_params.py"),
    ("funweb-ops §3 care_project_name", "v2_funweb_care_project_name.py"),
    ("funweb-ops §4 多进程消费", "v2_funweb_multi_consumer_example.py"),
    ("funweb-ops §5 ApsJobAdder", "v2_funweb_aps_job_adder.py"),
    ("funweb-ops §6 完整示例", "v2_funweb_full_example_imports.py"),
]


def run_one(label, script):
    path = os.path.join(DEMO_DIR, script)
    env = os.environ.copy()
    env["PYTHONPATH"] = ROOT
    t0 = time.time()
    try:
        r = subprocess.run(
            [sys.executable, path],
            capture_output=True,
            text=True,
            timeout=60,
            env=env,
            cwd=ROOT,
        )
        elapsed = time.time() - t0
        out = (r.stdout or "") + (r.stderr or "")
        if r.returncode == 66 and "[PASS]" in out:
            return "PASS", f"exit=66, {elapsed:.1f}s", out
        if r.returncode == 66:
            return "PASS", f"exit=66 (no [PASS] marker), {elapsed:.1f}s", out
        err_line = ""
        for line in out.splitlines():
            if "Error" in line or "Traceback" in line or "Exception" in line:
                err_line = line.strip()
                break
        if not err_line and out.strip():
            err_line = out.strip().splitlines()[-1]
        return "FAIL", f"exit={r.returncode}, {err_line[:200]}", out
    except subprocess.TimeoutExpired as e:
        out = (e.stdout or "") + (e.stderr or "")
        return "FAIL", "timeout 60s", out
    except Exception as e:
        return "FAIL", str(e), ""


if __name__ == "__main__":
    results = []
    print(f"Running {len(DEMOS)} v2 demos...\n")
    for label, script in DEMOS:
        status, detail, out = run_one(label, script)
        results.append((label, script, status, detail))
        mark = "✓" if status == "PASS" else "✗"
        print(f"{mark} [{status}] {label} ({script}): {detail}")
        if status == "FAIL" and out:
            tail = out[-1500:]
            print(f"--- output tail ---\n{tail}\n")

    print("\n=== SUMMARY TABLE ===")
    print(f"{'Skill示例':<45} {'脚本':<42} {'结果':<6} 详情")
    print("-" * 120)
    for label, script, status, detail in results:
        print(f"{label:<45} {script:<42} {status:<6} {detail}")

    fails = [r for r in results if r[2] == "FAIL"]
    print(f"\nTotal: {len(results)}, PASS: {len(results)-len(fails)}, FAIL: {len(fails)}")
    sys.exit(1 if fails else 0)
