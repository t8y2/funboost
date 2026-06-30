"""批量运行 round3 timing + workflow skill 验证脚本"""
import glob
import os
import subprocess
import sys

ROOT = r"D:\codes\funboost"
SCRIPT_DIR = os.path.join(ROOT, "tests", "ai_codes", "ai_demos", "skill_verification", "round3")


def main():
    scripts = sorted(
        p for p in glob.glob(os.path.join(SCRIPT_DIR, "timing_wf_*.py"))
        if not p.endswith("timing_wf_run_all.py")
    )
    env = os.environ.copy()
    env["PYTHONPATH"] = ROOT
    results = []
    for script in scripts:
        name = os.path.basename(script)
        print(f"\n{'=' * 60}\nRUN {name}\n{'=' * 60}")
        proc = subprocess.run(
            [sys.executable, script],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            timeout=50,
        )
        ok = proc.returncode == 66 and "[DONE]" in proc.stdout
        err = ""
        if proc.returncode != 66:
            err = (proc.stderr or proc.stdout)[-500:]
        elif "[OK]" not in proc.stdout and "[DONE]" not in proc.stdout:
            ok = False
            err = "missing [OK] or [DONE] marker"
        results.append((name, ok, proc.returncode, err))
        status = "PASS" if ok else "FAIL"
        print(f"{status} exit={proc.returncode}")
        if not ok:
            print(err)

    print(f"\n{'=' * 60}\nSUMMARY\n{'=' * 60}")
    passed = sum(1 for _, ok, _, _ in results if ok)
    for name, ok, code, err in results:
        print(f"{'PASS' if ok else 'FAIL'} | exit={code} | {name}")
        if err and not ok:
            print(f"  -> {err[:200]}")
    print(f"\nTotal: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
