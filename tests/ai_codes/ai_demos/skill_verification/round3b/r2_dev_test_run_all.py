"""round3b: 批量运行 developing-funboost-broker + developing-funboost-testing 第2轮验证脚本"""
import glob
import os
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = r"D:\codes\funboost"
ROUND3B = Path(__file__).parent
TIMEOUT = 50
ENV = {**os.environ, "PYTHONPATH": PROJECT_ROOT}

scripts = sorted(
    p for p in glob.glob(str(ROUND3B / "r2_dev_test_*.py"))
    if Path(p).name not in ("r2_dev_test_run_all.py",)
)


def run_one(script_path: str) -> dict:
    name = Path(script_path).name
    t0 = time.time()
    try:
        proc = subprocess.run(
            [sys.executable, script_path],
            cwd=PROJECT_ROOT,
            timeout=TIMEOUT,
            env=ENV,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        elapsed = round(time.time() - t0, 1)
        ok = proc.returncode == 66 and "[PASS]" in (proc.stdout or "")
        out = proc.stdout or ""
        if not ok and "[FAIL]" not in out:
            ok = proc.returncode == 66 and "PASS" in out
        err_tail = (proc.stderr or proc.stdout or "")[-1000:]
        return {
            "script": name,
            "ok": ok,
            "returncode": proc.returncode,
            "elapsed": elapsed,
            "output_tail": out[-600:],
            "error": "" if ok else err_tail,
        }
    except subprocess.TimeoutExpired as e:
        stdout = e.stdout or ""
        stderr = e.stderr or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", errors="replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", errors="replace")
        return {
            "script": name,
            "ok": False,
            "returncode": "TIMEOUT",
            "elapsed": TIMEOUT,
            "output_tail": "",
            "error": (stderr + stdout)[-1000:],
        }


def main():
    results = []
    for script in scripts:
        print(f"Running {Path(script).name} ...", flush=True)
        results.append(run_one(script))

    passed = sum(1 for r in results if r["ok"])
    print(f"\n=== ROUND3B R2 SUMMARY: {passed}/{len(results)} passed ===\n")
    for r in results:
        status = "PASS" if r["ok"] else "FAIL"
        print(f"{status}\t{r['script']}\trc={r['returncode']}\t{r['elapsed']}s")
        if not r["ok"]:
            print(r.get("output_tail") or r["error"])


if __name__ == "__main__":
    main()
