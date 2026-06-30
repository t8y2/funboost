"""Round2 汇总运行 round3b 全部 skill 验证脚本"""
import glob
import json
import os
import re
import subprocess
import sys
import time

ROOT = r"D:\codes\funboost"
SCRIPT_DIR = os.path.join(ROOT, "tests", "ai_codes", "ai_demos", "skill_verification", "round3b")
ENV = os.environ.copy()
ENV["PYTHONPATH"] = ROOT


def run_script(path: str) -> dict:
    name = os.path.basename(path)
    t0 = time.time()
    try:
        proc = subprocess.run(
            [sys.executable, path],
            cwd=ROOT,
            env=ENV,
            capture_output=True,
            text=True,
            timeout=60,
        )
        elapsed = round(time.time() - t0, 1)
        out = (proc.stdout or "") + (proc.stderr or "")
        final_match = re.search(r"=== 最终结果: (PASS|FAIL) ===", out)
        overall = final_match.group(1) if final_match else ("PASS" if proc.returncode == 66 else "FAIL")
        checks = re.findall(r"\[(PASS|FAIL)\] (.+)", out)
        return {
            "script": name,
            "skill": _skill_for(name),
            "overall": overall,
            "exit_code": proc.returncode,
            "elapsed_s": elapsed,
            "checks_pass": sum(1 for s, _ in checks if s == "PASS"),
            "checks_fail": sum(1 for s, _ in checks if s == "FAIL"),
            "failed_checks": [msg for s, msg in checks if s == "FAIL"],
            "output_tail": out[-2000:] if len(out) > 2000 else out,
        }
    except subprocess.TimeoutExpired:
        return {
            "script": name,
            "skill": _skill_for(name),
            "overall": "TIMEOUT",
            "exit_code": -1,
            "elapsed_s": 50,
            "checks_pass": 0,
            "checks_fail": 0,
            "failed_checks": ["subprocess timeout 50s"],
            "output_tail": "",
        }


def _skill_for(name: str) -> str:
    if "rpc" in name or name.startswith("r2_rpc_timing_wf_0[1-4]"):
        if any(x in name for x in ["01_rpc", "02_rpc", "03_rpc", "04_rpc"]):
            return "funboost-rpc-mode"
    if "01_rpc" in name or "02_rpc" in name or "03_rpc" in name or "04_rpc" in name:
        return "funboost-rpc-mode"
    if "05_timing" in name or "06_timing" in name:
        return "funboost-timing-jobs"
    if "07_workflow" in name or "08_workflow" in name or "09_workflow" in name or "10_workflow" in name or "11_workflow" in name:
        return "funboost-workflow"
    return "mixed"


if __name__ == "__main__":
    scripts = sorted(
        p for p in glob.glob(os.path.join(SCRIPT_DIR, "r2_rpc_timing_wf_*.py"))
        if not p.endswith("run_all.py")
    )
    results = []
    print(f"Running {len(scripts)} scripts from round3b...\n")
    for path in scripts:
        if path.endswith("run_all.py"):
            continue
        print(f">>> {os.path.basename(path)}")
        r = run_script(path)
        results.append(r)
        print(f"    {r['overall']} ({r['elapsed_s']}s)\n")

    out_path = os.path.join(SCRIPT_DIR, "r2_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print("=" * 80)
    print(f"{'Script':<52} {'Skill':<22} {'Result'}")
    print("-" * 80)
    skill_map = {
        "01_rpc": "funboost-rpc-mode",
        "02_rpc": "funboost-rpc-mode",
        "03_rpc": "funboost-rpc-mode",
        "04_rpc": "funboost-rpc-mode",
        "05_timing": "funboost-timing-jobs",
        "06_timing": "funboost-timing-jobs",
        "07_workflow": "funboost-workflow",
        "08_workflow": "funboost-workflow",
        "09_workflow": "funboost-workflow",
        "10_workflow": "funboost-workflow",
        "11_workflow": "funboost-workflow",
    }
    for r in results:
        skill = "unknown"
        for k, v in skill_map.items():
            if k.replace("_", "") in r["script"].replace("_", ""):
                skill = v
                break
        for k, v in skill_map.items():
            if k in r["script"]:
                skill = v
                break
        print(f"{r['script']:<52} {skill:<22} {r['overall']}")

    total_pass = sum(1 for r in results if r["overall"] == "PASS")
    print("-" * 80)
    print(f"TOTAL: {total_pass}/{len(results)} PASS")
    print(f"Results saved: {out_path}")

    time.sleep(2)
    os._exit(66 if total_pass == len(results) else 1)
