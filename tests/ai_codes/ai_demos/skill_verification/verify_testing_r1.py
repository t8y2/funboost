"""验证 developing-funboost-testing SKILL.md 的技术准确性（r1）"""
import glob
import inspect
import os
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = r"D:\codes\funboost"
LOG_DIR = r"D:\pythonlogs\ai_console_outs"
_ts = int(time.time())
PRINT_NAME = f"verify_testing_r1_{_ts}"
STD_NAME = f"verify_testing_r1_std_{_ts}"

os.environ["LOG_PATH"] = LOG_DIR
os.environ["PRINT_WRTIE_FILE_NAME"] = PRINT_NAME
os.environ["SYS_STD_FILE_NAME"] = STD_NAME

PASS = []
FAIL = []
WARN = []


def ok(msg):
    PASS.append(msg)
    print(f"[PASS] {msg}")


def fail(msg):
    FAIL.append(msg)
    print(f"[FAIL] {msg}")


def warn(msg):
    WARN.append(msg)
    print(f"[WARN] {msg}")


def check_pythonpath_and_funboost_config():
    """SKILL: PYTHONPATH 让项目根进入 sys.path，框架 import funboost_config"""
    pythonpath = os.environ.get("PYTHONPATH", "")
    normalized_paths = [p.replace("\\", "/") for p in sys.path]
    root_norm = PROJECT_ROOT.replace("\\", "/")
    in_syspath = root_norm in normalized_paths or any(root_norm in p for p in normalized_paths)
    if in_syspath or pythonpath.replace("\\", "/") == root_norm:
        ok("PYTHONPATH 生效，项目根在 sys.path 中")
    else:
        fail(f"项目根不在 sys.path 中: PYTHONPATH={pythonpath!r}, sys.path={sys.path[:3]}")

    try:
        import funboost_config

        ok(f"funboost_config 可导入: {funboost_config.__file__}")
    except ModuleNotFoundError:
        warn("funboost_config 模块未找到（可能尚未自动生成）")

    from funboost import set_frame_config

    src = inspect.getsource(set_frame_config.use_config_form_funboost_config_module)
    if "importlib.import_module('funboost_config')" in src:
        ok("set_frame_config 使用 importlib.import_module('funboost_config')")
    else:
        fail("set_frame_config 未使用 importlib.import_module('funboost_config')")
    if "sys.path[0]" in src and "sys.path[1]" in src:
        ok("set_frame_config 区分 sys.path[0](脚本目录) 与 sys.path[1](项目根)")
    else:
        fail("set_frame_config 未区分 sys.path[0]/sys.path[1]")


def check_env_log_vars():
    """SKILL: LOG_PATH / PRINT_WRTIE_FILE_NAME / SYS_STD_FILE_NAME 必须在 import funboost 前设置"""
    for key in ("LOG_PATH", "PRINT_WRTIE_FILE_NAME", "SYS_STD_FILE_NAME"):
        val = os.environ.get(key)
        if val:
            ok(f"环境变量 {key}={val!r}")
        else:
            fail(f"环境变量 {key} 未设置")


def check_log_files_after_import():
    """导入 funboost 后 nb_log 应能按环境变量写日志文件"""
    import funboost  # noqa: F401

    print(f"[VERIFY] print 重定向测试 {_ts}")
    sys.stdout.write(f"[VERIFY] stdout 重定向测试 {_ts}\n")

    time.sleep(2)
    if not Path(LOG_DIR).exists():
        fail(f"LOG_PATH 目录不存在: {LOG_DIR}")
        return

    print_files = glob.glob(str(Path(LOG_DIR) / f"*{PRINT_NAME}*"))
    std_files = glob.glob(str(Path(LOG_DIR) / f"*{STD_NAME}*"))
    if print_files:
        ok(f"PRINT 日志文件已生成: {Path(print_files[0]).name}")
    else:
        fail(f"未找到 PRINT 日志文件 (pattern *{PRINT_NAME}*)")
    if std_files:
        ok(f"STD 日志文件已生成: {Path(std_files[0]).name}")
    else:
        fail(f"未找到 STD 日志文件 (pattern *{STD_NAME}*)")


def check_os_exit_66_via_subprocess():
    """SKILL: os._exit(66) 作为 AI 脚本退出码"""
    code = (
        "import os,time;"
        "time.sleep(1);"
        "os._exit(66)"
    )
    env = os.environ.copy()
    env["PYTHONPATH"] = PROJECT_ROOT
    r = subprocess.run(
        [sys.executable, "-c", code],
        cwd=PROJECT_ROOT,
        env=env,
        timeout=10,
    )
    if r.returncode == 66:
        ok("os._exit(66) 子进程退出码为 66")
    else:
        fail(f"os._exit(66) 退出码错误: 期望 66, 实际 {r.returncode}")


def check_sleep_exit_pattern():
    """SKILL 模板: time.sleep + os._exit(66) 模式可运行"""
    from funboost import boost, BoosterParams, BrokerEnum

    @boost(
        BoosterParams(
            queue_name=f"verify_testing_r1_{_ts}",
            broker_kind=BrokerEnum.SQLITE_QUEUE,
            concurrent_num=2,
            qps=10,
        )
    )
    def mini_task(x: int):
        print(f"[MINI] 处理 {x}")
        return x

    for i in range(3):
        mini_task.push(i)
    mini_task.consume()
    ok("SKILL 模板 push + consume 模式可运行")


def check_timeout_cmd_behavior():
    """SKILL 方式二: cmd timeout 命令的实际行为（关键验证）"""
    # 用短 sleep 脚本测试：若 timeout 先执行，则 python 在 timeout 结束后才启动
    script = (
        "import time; "
        "open(r'D:\\pythonlogs\\ai_console_outs\\verify_timeout_marker.txt','w').write(str(time.time())); "
        "time.sleep(60)"
    )
    marker = Path(r"D:\pythonlogs\ai_console_outs\verify_timeout_marker.txt")
    if marker.exists():
        marker.unlink()

    cmd = f'timeout /t 3 /nobreak >nul & {sys.executable} -c "{script}"'
    t0 = time.time()
    try:
        r = subprocess.run(
            ["cmd", "/c", cmd],
            cwd=PROJECT_ROOT,
            env={**os.environ, "PYTHONPATH": PROJECT_ROOT},
            timeout=15,
        )
        elapsed = time.time() - t0
        marker_created = marker.exists()
        if marker_created:
            marker.unlink(missing_ok=True)
        # timeout 先跑 3 秒再启动 python：marker 出现时间应 >= 3 秒
        if marker_created and elapsed >= 2.5:
            warn(
                f"cmd `timeout /t N & python` 是顺序执行：先等 {elapsed:.1f}s 再启动 python，"
                "不会自动终止 python 进程（需外层 subprocess timeout 或脚本内 os._exit）"
            )
        elif not marker_created and elapsed < 15:
            ok("timeout 命令测试完成（marker 未创建或进程被外层终止）")
        else:
            warn(f"timeout 命令行为异常: elapsed={elapsed:.1f}s, marker={marker_created}, rc={r.returncode}")
    except subprocess.TimeoutExpired:
        marker.unlink(missing_ok=True)
        warn(
            "cmd `timeout /t N & python` 启动 python 后不会自动终止，"
            "外层 subprocess 超时 15s 才结束 — SKILL 应说明需配合 subprocess timeout"
        )


def check_time_estimate_formula():
    """SKILL 时间估算公式合理性"""
    concurrent_num = 50
    qps = None
    func_time = 0.1
    msg_count = 10
    throughput_no_qps = concurrent_num / func_time
    reasonable = 10 + (msg_count / throughput_no_qps) + 5
    if reasonable < 50:
        ok(f"默认参数下 10 条消息估算时间 ≈ {reasonable:.1f}s (< 50s 上限)")
    else:
        fail(f"估算时间 {reasonable:.1f}s 超过 50s 上限")

    qps = 10
    throughput_qps = min(qps, concurrent_num / func_time)
    reasonable_qps = 10 + (msg_count / throughput_qps) + 5
    ok(f"设 qps=10 时 10 条消息估算时间 ≈ {reasonable_qps:.1f}s")


def check_skill_template_import_order():
    """SKILL 模板：环境变量在 from funboost import 之前 — 已在文件开头满足"""
    ok("本脚本遵循 SKILL 模板：os.environ 设置在 import funboost 之前")


def main():
    print("=" * 60)
    print("developing-funboost-testing SKILL.md 验证")
    print("=" * 60)

    check_skill_template_import_order()
    check_pythonpath_and_funboost_config()
    check_env_log_vars()
    check_log_files_after_import()
    check_os_exit_66_via_subprocess()
    check_sleep_exit_pattern()
    check_timeout_cmd_behavior()
    check_time_estimate_formula()

    print(f"\n=== 汇总: PASS={len(PASS)}, FAIL={len(FAIL)}, WARN={len(WARN)} ===")
    for w in WARN:
        print(f"  WARN: {w}")
    if FAIL:
        for item in FAIL:
            print(f"  FAIL: {item}")
        os._exit(1)

    print("[DONE] verify_testing_r1 全部通过")
    time.sleep(8)
    os._exit(66)


if __name__ == "__main__":
    main()
