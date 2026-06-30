"""批量运行 v2_ skill 验证 demo 并汇总结果"""
import glob
import os
import subprocess
import sys

ROOT = r"D:\codes\funboost"
DEMO_DIR = os.path.join(ROOT, "tests", "ai_codes", "ai_demos", "skill_verification")
PATTERN = os.path.join(DEMO_DIR, "v2_*.py")
SKIP = {os.path.basename(__file__)}


def run_demo(path: str) -> dict:
    name = os.path.basename(path)
    env = os.environ.copy()
    env["PYTHONPATH"] = ROOT
    proc = subprocess.run(
        [sys.executable, path],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    out = (proc.stdout or "") + (proc.stderr or "")
    passed = proc.returncode == 66 and "最终结果: PASS" in out
    failed_line = ""
    for line in out.splitlines():
        if line.startswith("[FAIL]") or "Traceback" in line or "Error" in line and "FAIL" in out:
            if line.startswith("[FAIL]"):
                failed_line = line
                break
    if not passed and not failed_line:
        for line in out.splitlines():
            if "最终结果: FAIL" in line or proc.returncode not in (0, 66):
                failed_line = line or f"exit_code={proc.returncode}"
                break
    return {
        "name": name,
        "passed": passed,
        "exit_code": proc.returncode,
        "fail_detail": failed_line,
        "output_tail": "\n".join(out.splitlines()[-8:]),
    }


if __name__ == "__main__":
    scripts = sorted(p for p in glob.glob(PATTERN) if os.path.basename(p) not in SKIP)
    results = []
    for script in scripts:
        print(f"\n{'='*60}\n运行 {os.path.basename(script)} ...")
        try:
            r = run_demo(script)
        except subprocess.TimeoutExpired:
            r = {"name": os.path.basename(script), "passed": False, "exit_code": -1, "fail_detail": "超时 60s", "output_tail": ""}
        results.append(r)
        status = "PASS" if r["passed"] else "FAIL"
        print(f"  => {status} (exit={r['exit_code']})")
        if not r["passed"]:
            print(f"  详情: {r['fail_detail']}")

    print("\n" + "=" * 60)
    print("汇总表格")
    print(f"{'脚本':<45} {'结果':<6} 说明")
    print("-" * 80)
    for r in results:
        detail = "" if r["passed"] else (r["fail_detail"] or r["output_tail"][:60])
        print(f"{r['name']:<45} {'PASS' if r['passed'] else 'FAIL':<6} {detail}")

    fail_n = sum(1 for r in results if not r["passed"])
    print(f"\n总计: {len(results)} 个 demo, PASS={len(results)-fail_n}, FAIL={fail_n}")
    sys.exit(0 if fail_n == 0 else 1)
