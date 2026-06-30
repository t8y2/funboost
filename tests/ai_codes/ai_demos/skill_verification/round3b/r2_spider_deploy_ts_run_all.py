"""round3b 汇总运行 r2_spider_deploy_ts_* 验证脚本"""
import glob
import os
import subprocess
import sys
import time

PROJECT_ROOT = r"D:\codes\funboost"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def run_script(path: str) -> dict:
    name = os.path.basename(path)
    env = os.environ.copy()
    env["PYTHONPATH"] = PROJECT_ROOT
    try:
        proc = subprocess.run(
            [sys.executable, path],
            cwd=PROJECT_ROOT,
            env=env,
            capture_output=True,
            text=True,
            timeout=50,
        )
        output = (proc.stdout or "") + (proc.stderr or "")
        passed = "=== 最终结果: PASS ===" in output
        return {
            "script": name,
            "exit_code": proc.returncode,
            "passed": passed,
            "output": output,
        }
    except subprocess.TimeoutExpired:
        return {"script": name, "exit_code": -1, "passed": False, "output": "TIMEOUT"}
    except Exception as e:
        return {"script": name, "exit_code": -1, "passed": False, "output": str(e)}


if __name__ == "__main__":
    scripts = sorted(
        p for p in glob.glob(os.path.join(SCRIPT_DIR, "r2_spider_deploy_ts_*.py"))
        if not p.endswith("_run_all.py")
    )
    results = []
    for script in scripts:
        print(f"\n{'='*60}\n运行: {os.path.basename(script)}\n{'='*60}")
        r = run_script(script)
        results.append(r)
        print(r["output"][-2000:] if len(r["output"]) > 2000 else r["output"])

    print("\n" + "=" * 80)
    print("ROUND3B 验证汇总")
    print("=" * 80)
    print(f"{'脚本':<45} {'退出码':<8} {'结果'}")
    print("-" * 80)
    all_pass = True
    for r in results:
        status = "PASS" if r["passed"] else "FAIL"
        if not r["passed"]:
            all_pass = False
        print(f"{r['script']:<45} {r['exit_code']:<8} {status}")
    print("-" * 80)
    print(f"总计: {len(results)}  通过: {sum(1 for r in results if r['passed'])}  失败: {sum(1 for r in results if not r['passed'])}")
    print(f"整体: {'ALL PASS' if all_pass else 'HAS FAILURES'}")
    time.sleep(12)
    os._exit(66 if all_pass else 1)
