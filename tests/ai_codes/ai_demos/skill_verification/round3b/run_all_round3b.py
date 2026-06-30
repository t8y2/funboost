"""round3b: 批量运行 3 个 skill 的运行时/静态验证脚本"""
import glob
import json
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
    p for p in glob.glob(str(ROUND3B / "*.py"))
    if Path(p).name not in ("run_all_round3b.py",)
    and (
        Path(p).name.startswith("basics_")
        or Path(p).name.startswith("concepts_")
        or Path(p).name.startswith("broker_")
    )
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
        out = (proc.stdout or "") + (proc.stderr or "")
        ok = proc.returncode == 66
        return {
            "script": name,
            "ok": ok,
            "returncode": proc.returncode,
            "elapsed": elapsed,
            "output_tail": out[-1200:],
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
            "output_tail": (stderr + stdout)[-1200:],
        }


def main():
    results = []
    for script in scripts:
        print(f"Running {Path(script).name} ...", flush=True)
        results.append(run_one(script))

    passed = sum(1 for r in results if r["ok"])
    print(f"\n=== ROUND3B SUMMARY: {passed}/{len(results)} passed ===\n")
    for r in results:
        status = "PASS" if r["ok"] else "FAIL"
        print(f"{status}\t{r['script']}\trc={r['returncode']}\t{r['elapsed']}s")

    out_json = ROUND3B / "round3b_results.json"
    out_json.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nResults written to {out_json}")


if __name__ == "__main__":
    main()
