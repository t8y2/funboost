"""round3: 批量运行 faas_retry_* 验证脚本并汇总结果"""
import glob
import os
import subprocess
import sys

ROOT = r"D:\codes\funboost"
SCRIPTS_DIR = os.path.join(ROOT, "tests", "ai_codes", "ai_demos", "skill_verification", "round3")
TIMEOUT = 60

scripts = sorted(glob.glob(os.path.join(SCRIPTS_DIR, "faas_retry_*.py")))
scripts = [s for s in scripts if not s.endswith("run_all.py")]

results = []
for script in scripts:
    name = os.path.basename(script)
    env = {**os.environ, "PYTHONPATH": ROOT}
    try:
        proc = subprocess.run(
            [sys.executable, script],
            cwd=ROOT,
            env=env,
            timeout=TIMEOUT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        output = (proc.stdout or "") + (proc.stderr or "")
        passed = proc.returncode == 66 and "最终结果: PASS" in output
        status = "PASS" if passed else "FAIL"
        detail = ""
        if not passed:
            for line in output.splitlines():
                if "[FAIL]" in line or "Traceback" in line or "Error" in line:
                    detail = line.strip()[:120]
                    break
            if not detail:
                detail = f"exit_code={proc.returncode}"
        results.append((name, status, detail))
        print(f"{status} {name} (exit={proc.returncode})")
    except subprocess.TimeoutExpired:
        results.append((name, "TIMEOUT", f">{TIMEOUT}s"))
        print(f"TIMEOUT {name}")

print("\n=== SUMMARY ===")
for name, status, detail in results:
    print(f"{status}\t{name}\t{detail}")

fail_count = sum(1 for _, s, _ in results if s != "PASS")
print(f"\nTotal: {len(results)}, PASS: {len(results) - fail_count}, FAIL: {fail_count}")
sys.exit(0 if fail_count == 0 else 1)
