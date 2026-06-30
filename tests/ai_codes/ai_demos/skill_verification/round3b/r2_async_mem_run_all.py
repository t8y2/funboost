"""round3b 批量运行 r2_async_mem_* 验证脚本"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(r"D:\codes\funboost")
SCRIPTS_DIR = ROOT / "tests" / "ai_codes" / "ai_demos" / "skill_verification" / "round3b"
TIMEOUT = 50


def run_one(script_path: Path) -> dict:
    env = {**os.environ, "PYTHONPATH": str(ROOT)}
    try:
        r = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(ROOT),
            env=env,
            timeout=TIMEOUT,
            capture_output=True,
            text=True,
        )
        out = (r.stdout or "") + (r.stderr or "")
        ok = r.returncode == 66 and "[PASS]" in out
        return {
            "script": script_path.name,
            "status": "PASS" if ok else "FAIL",
            "exit_code": r.returncode,
            "has_pass_marker": "[PASS]" in out,
            "tail": out[-1500:],
        }
    except subprocess.TimeoutExpired as e:
        out = (e.stdout or b"").decode(errors="replace") + (e.stderr or b"").decode(errors="replace")
        return {
            "script": script_path.name,
            "status": "FAIL",
            "exit_code": -1,
            "has_pass_marker": False,
            "tail": out[-1500:] + "\n[TIMEOUT]",
        }


if __name__ == "__main__":
    scripts = sorted(SCRIPTS_DIR.glob("r2_async_mem_*.py"))
    scripts = [s for s in scripts if s.name != "r2_async_mem_run_all.py"]
    results = []
    print(f"Running {len(scripts)} scripts from round3b...\n")
    for s in scripts:
        row = run_one(s)
        results.append(row)
        print(f"{row['status']}\t{row['script']}\texit={row['exit_code']}")
        if row["status"] != "PASS":
            print(row["tail"])
            print("-" * 60)
        time.sleep(1)

    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = len(results) - passed
    summary = {"passed": passed, "failed": failed, "total": len(results), "results": results}
    out_file = SCRIPTS_DIR / "r2_async_mem_results.json"
    out_file.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nTotal: {passed} passed, {failed} failed, {len(results)} total")
    print(f"Results saved to {out_file}")
    sys.exit(0 if failed == 0 else 1)
