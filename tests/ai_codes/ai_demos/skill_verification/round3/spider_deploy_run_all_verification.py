"""round3: 批量运行 spider_deploy_* 验证脚本并汇总结果"""
import glob
import os
import subprocess
import sys

ROOT = r"D:\codes\funboost"
ROUND3 = os.path.join(ROOT, "tests", "ai_codes", "ai_demos", "skill_verification", "round3")
TIMEOUT = 25


def main():
    scripts = sorted(
        p for p in glob.glob(os.path.join(ROUND3, "spider_deploy_*.py"))
        if not p.endswith("spider_deploy_run_all_verification.py")
    )
    env = os.environ.copy()
    env["PYTHONPATH"] = ROOT
    rows = []
    for script in scripts:
        name = os.path.basename(script)
        try:
            proc = subprocess.run(
                [sys.executable, script],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
                timeout=TIMEOUT,
            )
            out = (proc.stdout or "") + (proc.stderr or "")
            if "最终结果: PASS" in out:
                status = "PASS"
            elif "最终结果: SKIP" in out:
                status = "SKIP"
            elif "最终结果: FAIL" in out:
                status = "FAIL"
            elif proc.returncode == 66:
                status = "PASS" if "FAIL" not in out.split("最终结果")[-1] else "FAIL"
            else:
                status = f"FAIL(rc={proc.returncode})"
            detail = ""
            for line in out.splitlines():
                if line.startswith("[FAIL]") or "Traceback" in line:
                    detail = line[:120]
                    break
            rows.append((name, status, detail))
        except subprocess.TimeoutExpired:
            rows.append((name, "TIMEOUT", f">{TIMEOUT}s"))
        except Exception as e:
            rows.append((name, "ERROR", str(e)[:120]))

    print("| 脚本 | 结果 | 备注 |")
    print("|------|------|------|")
    for name, status, detail in rows:
        print(f"| {name} | {status} | {detail} |")
    passed = sum(1 for _, s, _ in rows if s == "PASS")
    skipped = sum(1 for _, s, _ in rows if s == "SKIP")
    failed = sum(1 for _, s, _ in rows if s not in ("PASS", "SKIP"))
    print(f"\n汇总: PASS={passed} SKIP={skipped} FAIL/OTHER={failed} TOTAL={len(rows)}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
