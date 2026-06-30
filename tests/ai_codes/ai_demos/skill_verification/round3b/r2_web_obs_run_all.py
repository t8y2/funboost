"""round3b 批量运行 r2_web_obs_* 验证脚本"""
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(r"D:\codes\funboost")
SCRIPTS_DIR = ROOT / "tests" / "ai_codes" / "ai_demos" / "skill_verification" / "round3b"
TIMEOUT = 50


def run_one(script_path: Path) -> tuple[str, int, str]:
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
        return script_path.name, r.returncode, out[-3000:]
    except subprocess.TimeoutExpired as e:
        out = (e.stdout or b"").decode(errors="replace") + (e.stderr or b"").decode(errors="replace")
        return script_path.name, -1, out[-3000:] + "\n[TIMEOUT]"


if __name__ == "__main__":
    scripts = sorted(SCRIPTS_DIR.glob("r2_web_obs_*.py"))
    scripts = [s for s in scripts if s.name != "r2_web_obs_run_all.py"]
    print(f"Running {len(scripts)} scripts...\n")
    results = []
    for s in scripts:
        name, code, tail = run_one(s)
        ok = code == 66 and "[PASS]" in tail
        results.append((name, ok, code, tail))
        print(f"{'PASS' if ok else 'FAIL'}\t{name}\texit={code}")
        if not ok:
            print(tail)
            print("-" * 60)
        time.sleep(1)
    passed = sum(1 for _, ok, _, _ in results if ok)
    failed = len(results) - passed
    print(f"\nTotal: {passed} passed, {failed} failed, {len(results)} total")
    sys.exit(0 if failed == 0 else 1)
