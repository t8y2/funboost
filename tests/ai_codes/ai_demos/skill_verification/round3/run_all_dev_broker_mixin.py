"""批量运行 round3 dev_broker_mixin 验证脚本并汇总结果"""
import glob
import os
import subprocess
import sys

ROOT = r"D:\codes\funboost"
SCRIPTS_DIR = os.path.join(ROOT, "tests", "ai_codes", "ai_demos", "skill_verification", "round3")
ENV = {**os.environ, "PYTHONPATH": ROOT}

scripts = sorted(glob.glob(os.path.join(SCRIPTS_DIR, "dev_broker_mixin_*.py")))
scripts = [s for s in scripts if not s.endswith("run_all.py")]

results = []
for script in scripts:
    name = os.path.basename(script)
    print(f"\n{'='*60}\nRUN: {name}\n{'='*60}")
    proc = subprocess.run(
        [sys.executable, script],
        cwd=ROOT,
        env=ENV,
        capture_output=True,
        text=True,
        timeout=60,
    )
    stdout = proc.stdout or ""
    stderr = proc.stderr or ""
    combined = stdout + stderr
    status = "PASS" if proc.returncode == 66 and "[PASS]" in combined else "FAIL"
    if proc.returncode != 66 and status == "PASS":
        status = "FAIL"
    if proc.returncode == 66 and "[FAIL]" in combined:
        status = "FAIL"
    if proc.returncode not in (66, 0) and "[PASS]" not in combined:
        status = "FAIL"
    # refine: PASS if exit 66 and contains [PASS]
    if proc.returncode == 66 and "[PASS]" in combined:
        status = "PASS"
    elif "[FAIL]" in combined or proc.returncode not in (66,):
        if "[PASS]" in combined and proc.returncode == 66:
            status = "PASS"
        else:
            status = "FAIL"

    # extract last status line
    last_line = ""
    for line in combined.splitlines():
        if line.startswith("[PASS]") or line.startswith("[FAIL]") or line.startswith("[START]"):
            if line.startswith("[PASS]") or line.startswith("[FAIL]"):
                last_line = line

    results.append({
        "script": name,
        "exit_code": proc.returncode,
        "status": status,
        "summary": last_line,
        "error_hint": combined[-500:] if status == "FAIL" else "",
    })
    print(combined[-2000:] if len(combined) > 2000 else combined)
    print(f">>> {status} exit={proc.returncode}")

print("\n\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
for r in results:
    print(f"{r['status']:4} | exit={r['exit_code']} | {r['script']} | {r['summary']}")

passed = sum(1 for r in results if r["status"] == "PASS")
print(f"\nTotal: {passed}/{len(results)} PASS")
