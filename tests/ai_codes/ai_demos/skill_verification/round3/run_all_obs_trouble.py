"""批量运行 round3 observability + troubleshooting 验证脚本 (obs_trouble_*)"""
import glob
import json
import os
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = r"D:\codes\funboost"
ROUND3 = Path(__file__).parent
TIMEOUT = 90
ENV = {**os.environ, "PYTHONPATH": PROJECT_ROOT}

scripts = sorted(
    p for p in glob.glob(str(ROUND3 / "obs_trouble_*.py"))
    if Path(p).name not in ("run_all_obs_trouble.py",)
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
        ok = proc.returncode in (0, 66)
        err_tail = (proc.stderr or proc.stdout or "")[-800:]
        return {
            "script": name,
            "ok": ok,
            "returncode": proc.returncode,
            "elapsed": elapsed,
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
            "error": (stderr + stdout)[-800:],
        }
    except Exception as e:
        return {
            "script": name,
            "ok": False,
            "returncode": "ERROR",
            "elapsed": round(time.time() - t0, 1),
            "error": str(e),
        }


def main():
    results = []
    for script in scripts:
        print(f"Running {Path(script).name} ...", flush=True)
        results.append(run_one(script))

    passed = sum(1 for r in results if r["ok"])
    failed = len(results) - passed
    print(f"\n=== OBS_TROUBLE ROUND3: {passed}/{len(results)} passed, {failed} failed ===\n")
    for r in results:
        status = "PASS" if r["ok"] else "FAIL"
        print(f"{status}\t{r['script']}\trc={r['returncode']}\t{r['elapsed']}s")

    out_json = ROUND3 / "obs_trouble_results.json"
    out_json.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nResults saved to {out_json}")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
