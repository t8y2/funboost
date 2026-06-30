"""批量运行 spider + remote-deploy skill 验证 demo，汇总 PASS/FAIL"""
import glob
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = r"D:\codes\funboost"
DEMO_DIR = os.path.join(ROOT, "tests", "ai_codes", "ai_demos", "skill_verification")
PATTERN = os.path.join(DEMO_DIR, "v2_spider_*.py")
PATTERN2 = os.path.join(DEMO_DIR, "v2_remote_*.py")

SCRIPTS = sorted(glob.glob(PATTERN) + glob.glob(PATTERN2))
ENV = {**os.environ, "PYTHONPATH": ROOT}


def run_one(script_path: str) -> dict:
    name = os.path.basename(script_path)
    try:
        proc = subprocess.run(
            [sys.executable, script_path],
            cwd=ROOT,
            env=ENV,
            capture_output=True,
            text=True,
            timeout=25,
            encoding="utf-8",
            errors="replace",
        )
        out = (proc.stdout or "") + (proc.stderr or "")
        if "=== 最终结果: SKIP" in out:
            final = "SKIP"
        elif "=== 最终结果: PASS ===" in out:
            final = "PASS"
        elif "=== 最终结果: FAIL ===" in out:
            final = "FAIL"
        elif proc.returncode == 66:
            final = "PASS" if "[FAIL]" not in out else "FAIL"
        else:
            final = "FAIL"
        fails = re.findall(r"\[FAIL\] (.+)", out)
        return {"script": name, "result": final, "fails": fails, "output_tail": out[-800:]}
    except subprocess.TimeoutExpired:
        return {"script": name, "result": "FAIL", "fails": ["超时 (>25s)"], "output_tail": ""}
    except Exception as e:
        return {"script": name, "result": "FAIL", "fails": [str(e)], "output_tail": ""}


if __name__ == "__main__":
    print(f"共 {len(SCRIPTS)} 个验证脚本\n")
    results = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        futs = {pool.submit(run_one, s): s for s in SCRIPTS}
        for fut in as_completed(futs):
            results.append(fut.result())

    results.sort(key=lambda x: x["script"])
    pass_n = sum(1 for r in results if r["result"] == "PASS")
    fail_n = sum(1 for r in results if r["result"] == "FAIL")
    skip_n = sum(1 for r in results if r["result"] == "SKIP")

    print(f"{'脚本':<45} {'结果':<6} 失败项")
    print("-" * 90)
    for r in results:
        fail_detail = "; ".join(r["fails"][:2]) if r["fails"] else ""
        print(f"{r['script']:<45} {r['result']:<6} {fail_detail}")

    print("-" * 90)
    print(f"PASS={pass_n}  FAIL={fail_n}  SKIP={skip_n}  TOTAL={len(results)}")
