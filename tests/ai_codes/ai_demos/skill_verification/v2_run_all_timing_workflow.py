"""批量运行 v2 timing/workflow skill 验证脚本并汇总结果"""
import os
import subprocess
import sys
import time

ROOT = r"D:\codes\funboost"
DEMO_DIR = os.path.join(ROOT, "tests", "ai_codes", "ai_demos", "skill_verification")

SCRIPTS = [
    ("funboost-timing-jobs", "核心代码模式（interval + cron）", "v2_timing_core_pattern.py"),
    ("funboost-timing-jobs", "Redis 作业存储（改用 memory）", "v2_timing_redis_job_store.py"),
    ("funboost-timing-jobs", "一次性 date 定时任务", "v2_timing_date_once.py"),
    ("funboost-timing-jobs", "args 位置参数", "v2_timing_args_positional.py"),
    ("funboost-timing-jobs", "完整示例 heartbeat", "v2_timing_full_heartbeat.py"),
    ("funboost-workflow", "核心任务定义", "v2_workflow_task_definitions.py"),
    ("funboost-workflow", "Chain 串行流水线", "v2_workflow_chain.py"),
    ("funboost-workflow", "Group 并行执行", "v2_workflow_group.py"),
    ("funboost-workflow", "Chord 扇出后聚合", "v2_workflow_chord.py"),
    ("funboost-workflow", "复杂嵌套 chain+chord", "v2_workflow_nested.py"),
]

env = os.environ.copy()
env["PYTHONPATH"] = ROOT

results = []
for skill, example, script in SCRIPTS:
    path = os.path.join(DEMO_DIR, script)
    print(f"\n{'='*60}\nRunning {script} ...")
    t0 = time.time()
    try:
        proc = subprocess.run(
            [sys.executable, path],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            timeout=50,
            encoding="utf-8",
            errors="replace",
        )
        elapsed = time.time() - t0
        stdout = proc.stdout or ""
        stderr = proc.stderr or ""
        combined = stdout + stderr
        if proc.returncode == 66 and "[DONE]" in combined and "Traceback" not in combined:
            status = "PASS"
            detail = f"exit=66, {elapsed:.1f}s"
        elif proc.returncode == 66 and "[OK]" in combined and "Traceback" not in combined:
            status = "PASS"
            detail = f"exit=66, {elapsed:.1f}s"
        else:
            status = "FAIL"
            err_lines = [ln for ln in combined.splitlines() if "Error" in ln or "Traceback" in ln or "FAIL" in ln]
            detail = f"exit={proc.returncode}, {elapsed:.1f}s"
            if err_lines:
                detail += " | " + err_lines[-1][:200]
            else:
                detail += " | 未看到 [DONE] 或存在异常"
        results.append((skill, example, script, status, detail))
        print(combined[-2000:] if len(combined) > 2000 else combined)
        print(f">>> {status}: {detail}")
    except subprocess.TimeoutExpired as e:
        out = (e.stdout or b"").decode("utf-8", errors="replace") if isinstance(e.stdout, bytes) else (e.stdout or "")
        err = (e.stderr or b"").decode("utf-8", errors="replace") if isinstance(e.stderr, bytes) else (e.stderr or "")
        results.append((skill, example, script, "FAIL", "timeout 50s"))
        print(out[-1000:] + err[-1000:])
        print(">>> FAIL: timeout")

print("\n" + "=" * 80)
print(f"{'Skill':<22} {'示例':<28} {'脚本':<32} {'结果':<6} 详情")
print("-" * 80)
for skill, example, script, status, detail in results:
    print(f"{skill:<22} {example:<28} {script:<32} {status:<6} {detail}")

fail_count = sum(1 for r in results if r[3] == "FAIL")
print("-" * 80)
print(f"总计: {len(results)}  PASS: {len(results)-fail_count}  FAIL: {fail_count}")
sys.exit(1 if fail_count else 0)
