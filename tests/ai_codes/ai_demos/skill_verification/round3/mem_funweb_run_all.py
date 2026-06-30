"""round3 批量运行 mem_funweb_* 验证脚本"""
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(r"D:\codes\funboost")
SCRIPTS_DIR = ROOT / "tests" / "ai_codes" / "ai_demos" / "skill_verification" / "round3"
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
        return script_path.name, r.returncode, out[-2000:]
    except subprocess.TimeoutExpired as e:
        out = (e.stdout or b"").decode(errors="replace") + (e.stderr or b"").decode(errors="replace")
        return script_path.name, -1, out[-2000:] + "\n[TIMEOUT]"


if __name__ == "__main__":
    scripts = sorted(SCRIPTS_DIR.glob("mem_funweb_*.py"))
    scripts = [s for s in scripts if s.name != "mem_funweb_run_all.py"]
    print(f"Running {len(scripts)} scripts...\n")
    passed = failed = 0
    for s in scripts:
        name, code, tail = run_one(s)
        ok = code == 66 or ("[PASS]" in tail and code in (66, 0))
        status = "PASS" if ok else "FAIL"
        if ok:
            passed += 1
        else:
            failed += 1
        print(f"{status}\t{name}\texit={code}")
        if not ok:
            print(tail)
            print("-" * 60)
        time.sleep(1)
    print(f"\nTotal: {passed} passed, {failed} failed, {len(scripts)} total")
    sys.exit(0 if failed == 0 else 1)
