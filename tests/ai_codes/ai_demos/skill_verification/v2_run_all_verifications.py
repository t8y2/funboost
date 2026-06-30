"""批量运行 v2_ skill 验证脚本并汇总结果"""
import glob
import os
import subprocess
import sys

ROOT = r"D:\codes\funboost"
DEMO_DIR = os.path.join(ROOT, "tests", "ai_codes", "ai_demos", "skill_verification")
ENV = {**os.environ, "PYTHONPATH": ROOT}

SCRIPTS = sorted(glob.glob(os.path.join(DEMO_DIR, "v2_*.py")))
SCRIPTS = [s for s in SCRIPTS if not s.endswith("v2_run_all_verifications.py")]


def classify_result(stdout, stderr, returncode):
    text = (stdout or "") + (stderr or "")
    if "[FAIL]" in text:
        for line in text.splitlines():
            if "[FAIL]" in line:
                return "FAIL", line.strip()
        return "FAIL", "输出含 [FAIL]"
    if returncode != 66 and returncode != 0:
        err = (stderr or stdout or "").strip().splitlines()
        snippet = err[-1] if err else f"exit code {returncode}"
        return "FAIL", snippet[:200]
    if "[PASS]" in text:
        for line in text.splitlines():
            if "[PASS]" in line:
                return "PASS", line.strip()
    if "Traceback" in text:
        lines = [l for l in text.splitlines() if l.strip()]
        return "FAIL", lines[-1][:200] if lines else "Traceback"
    return "PASS", "exit 66, 无 Traceback"


def main():
    rows = []
    for script in SCRIPTS:
        name = os.path.basename(script)
        print(f"\n>>> Running {name} ...")
        try:
            proc = subprocess.run(
                [sys.executable, script],
                cwd=ROOT,
                env=ENV,
                capture_output=True,
                text=True,
                timeout=45,
            )
            status, detail = classify_result(proc.stdout, proc.stderr, proc.returncode)
        except subprocess.TimeoutExpired:
            status, detail = "FAIL", "subprocess timeout 45s"
        rows.append((name, status, detail))
        print(f"    {status}: {detail[:120]}")

    print("\n" + "=" * 80)
    print(f"{'脚本':<45} {'结果':<6} 说明")
    print("-" * 80)
    for name, status, detail in rows:
        print(f"{name:<45} {status:<6} {detail[:80]}")
    print("=" * 80)
    passed = sum(1 for _, s, _ in rows if s == "PASS")
    print(f"总计: {passed}/{len(rows)} PASS")


if __name__ == "__main__":
    main()
