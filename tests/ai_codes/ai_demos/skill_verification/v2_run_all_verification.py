"""批量运行 v2_ skill 验证 demo 并汇总 PASS/FAIL"""
import os
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(r"D:\codes\funboost")
DEMO_DIR = PROJECT_ROOT / "tests" / "ai_codes" / "ai_demos" / "skill_verification"

DEMOS = [
    ("developing-funboost-testing", "测试脚本模板", "v2_testing_template.py", 35),
    ("developing-funboost-testing", "方式一 os._exit + 日志", "v2_testing_os_exit_pattern.py", 35),
    ("developing-funboost-testing", "方式二 subprocess.run", "v2_testing_subprocess_pattern.py", 45),
    ("developing-funboost-testing", "测试 TXT broker", "v2_testing_txt_broker.py", 35),
    ("developing-funboost-testing", "测试 Mixin", "v2_testing_mixin.py", 35),
    ("funboost-async-programming", "§1.1 ASYNC 协程模式", "v2_async_1_1_async_fetch.py", 35),
    ("funboost-async-programming", "§1.2 THREADING + async def", "v2_async_1_2_thread_async.py", 35),
    ("funboost-async-programming", "§2 异步发布", "v2_async_2_aio_publish.py", 35),
    ("funboost-async-programming", "§3 异步 RPC", "v2_async_3_async_rpc.py", 35),
    ("funboost-async-programming", "§3 get_aio_future", "v2_async_3_get_aio_future.py", 35),
    ("funboost-async-programming", "§5.1 specify_async_loop", "v2_async_5_1_specify_loop.py", 35),
    ("funboost-async-programming", "§5.4 AioAsyncResult 模式", "v2_async_5_4_aio_result_pattern.py", 35),
    ("funboost-async-programming", "§6 FastAPI", "v2_async_6_fastapi.py", 35),
    ("funboost-async-programming", "§7 混合 async/sync", "v2_async_7_mixed.py", 35),
    ("funboost-async-programming", "§8.1 最小完整示例", "v2_async_8_1_minimal.py", 35),
    ("funboost-async-programming", "§8.2 Redis RPC（MEMORY 替代）", "v2_async_8_2_redis_rpc.py", 35),
]

NON_PYTHON = [
    ("developing-funboost-testing", "PYTHONPATH PowerShell/CMD", "N/A（Shell 命令，非 Python 示例）"),
]


def run_demo(skill: str, name: str, script: str, timeout: int) -> dict:
    path = DEMO_DIR / script
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJECT_ROOT)
    t0 = time.time()
    try:
        r = subprocess.run(
            [sys.executable, str(path)],
            cwd=str(PROJECT_ROOT),
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        elapsed = time.time() - t0
        output = (r.stdout or "") + (r.stderr or "")
        if r.returncode == 66:
            status = "PASS"
            detail = f"exit=66, {elapsed:.1f}s"
        elif r.returncode == 0 and "subprocess" in script:
            status = "PASS"
            detail = f"subprocess 正常结束, {elapsed:.1f}s"
        else:
            status = "FAIL"
            tail = output.strip()[-800:] if output.strip() else "(无输出)"
            detail = f"exit={r.returncode}, {elapsed:.1f}s | {tail}"
        return {"skill": skill, "name": name, "script": script, "status": status, "detail": detail}
    except subprocess.TimeoutExpired as e:
        out = ""
        if e.stdout:
            out += e.stdout if isinstance(e.stdout, str) else e.stdout.decode(errors="replace")
        if e.stderr:
            out += e.stderr if isinstance(e.stderr, str) else e.stderr.decode(errors="replace")
        return {
            "skill": skill,
            "name": name,
            "script": script,
            "status": "FAIL",
            "detail": f"超时 {timeout}s | {out.strip()[-500:]}",
        }
    except Exception as e:
        return {
            "skill": skill,
            "name": name,
            "script": script,
            "status": "FAIL",
            "detail": str(e),
        }


def main():
    results = []
    for skill, name, script, timeout in DEMOS:
        print(f"Running {script} ...")
        results.append(run_demo(skill, name, script, timeout))

    for skill, name, note in NON_PYTHON:
        results.append(
            {"skill": skill, "name": name, "script": "-", "status": "N/A", "detail": note}
        )

    print("\n" + "=" * 100)
    print(f"{'Skill':<32} {'示例':<28} {'脚本':<36} {'结果':<6} 详情")
    print("-" * 100)
    pass_n = fail_n = 0
    for r in results:
        print(f"{r['skill']:<32} {r['name']:<28} {r['script']:<36} {r['status']:<6} {r['detail'][:120]}")
        if r["status"] == "PASS":
            pass_n += 1
        elif r["status"] == "FAIL":
            fail_n += 1

    print("=" * 100)
    print(f"汇总: PASS={pass_n}, FAIL={fail_n}, N/A={len(NON_PYTHON)}")
    sys.exit(1 if fail_n else 0)


if __name__ == "__main__":
    main()
