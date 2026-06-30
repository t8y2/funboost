"""Round2-07: 验证 funweb / spider / remote-deploy 三个 SKILL 与对应教程（c13/c8/c9）

运行时校验（以源码为准）：
- funweb: start_funboost_web_manager 参数名与默认值（含 port=27018）
- spider: SimpleSpiderClient / AsyncSpiderClient 导入路径
- deploy: Booster.fabric_deploy 方法存在
"""
import inspect
import os
import sys
import time
from pathlib import Path

PROJECT_ROOT = r"D:\codes\funboost"
SKILLS = {
    "funweb": {
        "skill": Path(PROJECT_ROOT) / ".agents/skills/funboost-funweb-ops/SKILL.md",
        "tutorial": Path(r"D:\codes\funboost_docs\source\articles\c13.md"),
    },
    "spider": {
        "skill": Path(PROJECT_ROOT) / ".agents/skills/funboost-spider-crawling/SKILL.md",
        "tutorial": Path(r"D:\codes\funboost_docs\source\articles\c8.md"),
    },
    "deploy": {
        "skill": Path(PROJECT_ROOT) / ".agents/skills/funboost-remote-deploy/SKILL.md",
        "tutorial": Path(r"D:\codes\funboost_docs\source\articles\c9.md"),
    },
}

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"verify_all_r2_07_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"verify_all_r2_07_std_{_ts}"

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


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def verify_files_exist():
    for name, paths in SKILLS.items():
        if paths["skill"].is_file():
            ok(f"{name}: SKILL.md 存在")
        else:
            fail(f"{name}: SKILL.md 不存在: {paths['skill']}")
        if paths["tutorial"].is_file():
            ok(f"{name}: 教程存在")
        else:
            fail(f"{name}: 教程不存在: {paths['tutorial']}")


def verify_funweb_api():
    """SKILL + c13: start_funboost_web_manager 参数与默认端口"""
    from funboost.funweb.app import start_funboost_web_manager

    ok("funweb: from funboost.funweb.app import start_funboost_web_manager 可导入")

    try:
        from funboost.funboost_web_manager.app import start_funboost_web_manager as fn2

        if start_funboost_web_manager is fn2:
            ok("funweb: 等价路径 funboost.funboost_web_manager.app 指向同一函数")
        else:
            fail("funweb: funweb.app 与 funboost_web_manager.app 不是同一函数")
    except ImportError as e:
        fail(f"funweb: 等价导入路径失败: {e}")

    sig = inspect.signature(start_funboost_web_manager)
    param_names = list(sig.parameters.keys())
    expected = ["host", "port", "block", "debug", "care_project_name"]
    if param_names == expected:
        ok(f"funweb: start_funboost_web_manager 参数名 {expected}")
    else:
        fail(f"funweb: 参数名不符, 预期 {expected}, 实际 {param_names}")

    defaults = {
        "host": "0.0.0.0",
        "port": 27018,
        "block": False,
        "debug": False,
        "care_project_name": None,
    }
    for name, expected_val in defaults.items():
        actual = sig.parameters[name].default
        if actual == expected_val:
            ok(f"funweb: {name} 默认值={expected_val!r}")
        else:
            fail(f"funweb: {name} 默认值错误: 预期 {expected_val!r}, 实际 {actual!r}")

    skill_text = _read(SKILLS["funweb"]["skill"])
    c13_text = _read(SKILLS["funweb"]["tutorial"])
    for needle in (
        "python -m funboost.funweb.app",
        "port=27018",
        "admin",
        "123456",
        "is_send_consumer_heartbeat_to_redis",
        "care_project_name",
    ):
        if needle in skill_text:
            ok(f"funweb SKILL 含关键描述: {needle!r}")
        else:
            fail(f"funweb SKILL 缺关键描述: {needle!r}")

    for needle in ("27018", "start_funboost_web_manager", "funboost.funweb.app"):
        if needle in c13_text:
            ok(f"funweb c13 含: {needle!r}")
        else:
            fail(f"funweb c13 缺: {needle!r}")

    if "BrokerEnum.REDIS_ACK_ABLE" in skill_text and "BrokerEnum.REDIS" in c13_text:
        warn("funweb: SKILL 示例用 REDIS_ACK_ABLE，c13 测试代码用 REDIS（SKILL 更贴近生产，非错误）")

    c13_only = [
        ("should_check_publish_func_params", "c13 测试代码有 should_check_publish_func_params，SKILL 未提及"),
        ("脚本部署", "c13 §13.4 脚本部署详细说明，SKILL 已覆盖但可补充 auto_start/auto_restart 细节"),
        ("远程部署", "c13 §13.4.6 funweb 脚本部署远程更新，SKILL 未单独强调"),
    ]
    for kw, msg in c13_only:
        if kw in c13_text and kw not in skill_text:
            warn(f"funweb: {msg}")


def verify_spider_imports():
    """SKILL + c8: funspider 客户端导入路径"""
    from funboost.contrib.funspider import SimpleSpiderClient, AsyncSpiderClient

    ok("spider: from funboost.contrib.funspider import SimpleSpiderClient 可导入")
    ok("spider: from funboost.contrib.funspider import AsyncSpiderClient 可导入")

    from funboost.contrib.funspider import SpiderItem, SpiderResponse, Field, create_engine, create_async_engine

    for cls in (SpiderItem, SpiderResponse, Field, create_engine, create_async_engine):
        ok(f"spider: funboost.contrib.funspider 导出 {cls.__name__ if hasattr(cls, '__name__') else cls}")

    if inspect.isclass(SimpleSpiderClient) and inspect.isclass(AsyncSpiderClient):
        ok("spider: SimpleSpiderClient / AsyncSpiderClient 为类")
    else:
        fail("spider: SimpleSpiderClient / AsyncSpiderClient 类型异常")

    skill_text = _read(SKILLS["spider"]["skill"])
    c8_text = _read(SKILLS["spider"]["tutorial"])

    import_line = "from funboost.contrib.funspider import SimpleSpiderClient"
    if import_line in skill_text and import_line in c8_text:
        ok("spider: SKILL 与 c8 导入路径一致: funboost.contrib.funspider")
    else:
        fail("spider: SKILL 与 c8 导入路径不一致")

    async_line = "from funboost.contrib.funspider import AsyncSpiderClient"
    if async_line in skill_text:
        ok("spider: SKILL 含 AsyncSpiderClient 导入")
    else:
        fail("spider: SKILL 缺 AsyncSpiderClient 导入示例")

    for needle in ("do_task_filtering", "task_filtering_expire_seconds", "BoostersManager.consume_group"):
        if needle.replace(".", "") in skill_text.replace(".", "") or needle in skill_text:
            ok(f"spider SKILL 含: {needle}")
        else:
            fail(f"spider SKILL 缺: {needle}")

    if "funspider_demo1.py" in skill_text or "funspider_demos" in skill_text:
        ok("spider SKILL 引用 funspider demo 源码")
    else:
        warn("spider: SKILL 未引用 funspider_demo1.py（c8 §8.32 有提及）")

    if "boost_spider" in skill_text and "boost_spider" in c8_text:
        ok("spider: SKILL 与 c8 均覆盖 boost_spider")
    else:
        fail("spider: boost_spider 描述缺失")


def verify_fabric_deploy():
    """SKILL + c9: fabric_deploy 方法存在且参数与教程一致"""
    from funboost import boost, BoosterParams, BrokerEnum
    from funboost.core.fabric_deploy_helper import fabric_deploy, kill_all_remote_tasks

    ok("deploy: from funboost.core.fabric_deploy_helper import fabric_deploy 可导入")
    ok("deploy: kill_all_remote_tasks 可导入")

    @boost(BoosterParams(queue_name=f"verify_r2_07_deploy_{_ts}", broker_kind=BrokerEnum.MEMORY_QUEUE))
    def _deploy_probe(x):
        return x

    if hasattr(_deploy_probe, "fabric_deploy") and callable(_deploy_probe.fabric_deploy):
        ok("deploy: @boost 装饰函数具备 .fabric_deploy() 方法")
    else:
        fail("deploy: Booster 对象缺少 .fabric_deploy() 方法")

    if _deploy_probe.fabric_deploy is not fabric_deploy:
        ok("deploy: Booster.fabric_deploy 为绑定方法（非模块级函数本身）")
    else:
        fail("deploy: Booster.fabric_deploy 不应直接等于模块级 fabric_deploy")

    sig = inspect.signature(_deploy_probe.fabric_deploy)
    required = ["host", "port", "user", "password", "process_num"]
    for p in required:
        if p in sig.parameters:
            ok(f"deploy: fabric_deploy 含参数 {p!r}")
        else:
            fail(f"deploy: fabric_deploy 缺参数 {p!r}")

    if sig.parameters["process_num"].default == 1:
        ok("deploy: process_num 默认值=1")
    else:
        fail(f"deploy: process_num 默认值错误: {sig.parameters['process_num'].default!r}")

    for p in ("invoke_runner_kwargs", "only_upload_within_the_last_modify_time", "extra_shell_str", "pkey_file_path"):
        if p in sig.parameters:
            ok(f"deploy: fabric_deploy 含 SKILL/c9 文档参数 {p!r}")
        else:
            fail(f"deploy: fabric_deploy 缺参数 {p!r}")

    import funboost

    if hasattr(funboost, "fabric_deploy"):
        fail("deploy: funboost 顶层不应导出 fabric_deploy（SKILL 正确警告）")
    else:
        ok("deploy: fabric_deploy 不在 funboost 顶层 __init__（与 SKILL/c9 一致）")

    skill_text = _read(SKILLS["deploy"]["skill"])
    c9_text = _read(SKILLS["deploy"]["tutorial"])

    if ".fabric_deploy(" in skill_text:
        ok("deploy SKILL 示例使用 my_task.fabric_deploy(...)")
    else:
        fail("deploy SKILL 缺 .fabric_deploy 示例")

    for needle in ("process_num", "invoke_runner_kwargs", "pty", "only_upload_within_the_last_modify_time"):
        if needle in skill_text:
            ok(f"deploy SKILL 含: {needle}")
        else:
            fail(f"deploy SKILL 缺: {needle}")

    for needle in ("process_num", "invoke_runner_kwargs", "pty"):
        if needle in c9_text:
            ok(f"deploy c9 含: {needle}")
        else:
            fail(f"deploy c9 缺: {needle}")

    if "funboost_fabric_mark__" in skill_text:
        ok("deploy SKILL 进程 mark 格式 funboost_fabric_mark__{queue}__{func} 与源码一致")
    elif "funboost_fabric_mark" in skill_text:
        warn("deploy: SKILL mark 描述需确认双下划线格式（源码为 funboost_fabric_mark__{queue}__{func}）")
    else:
        fail("deploy SKILL 未描述 fabric mark")

    if "fsdf_fabric_mark" in c9_text or "-fsdfmark" in c9_text:
        warn("deploy: c9 教程示例 mark 格式过时（-fsdfmark / fsdf_fabric_mark），SKILL 已用新格式")


def main():
    print("=" * 60)
    print("verify_all_r2_07 — funweb / spider / remote-deploy SKILL 验证")
    print("=" * 60)

    verify_files_exist()
    print("\n--- funboost-funweb-ops ---")
    verify_funweb_api()
    print("\n--- funboost-spider-crawling ---")
    verify_spider_imports()
    print("\n--- funboost-remote-deploy ---")
    verify_fabric_deploy()

    print("\n" + "=" * 60)
    print(f"汇总: PASS={len(PASS)}, FAIL={len(FAIL)}, WARN={len(WARN)}")
    if WARN:
        for w in WARN:
            print(f"  [WARN] {w}")
    if FAIL:
        for f in FAIL:
            print(f"  [FAIL] {f}")
        print("OVERALL: FAIL")
        print("=" * 60)
        return 1

    print("OVERALL: PASS")
    print("=" * 60)
    time.sleep(1)
    os._exit(66)


if __name__ == "__main__":
    sys.exit(main())
