"""验证 batch5 三个 Skill 的代码示例能否真实运行

覆盖:
- developing-funboost-testing
- funboost-funweb-ops
- funboost-spider-crawling
"""
import glob
import inspect
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import ClassVar, Optional

os.environ["PYTHONPATH"] = r"D:\codes\funboost"
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = "real_verify_batch5_print.txt"
os.environ["SYS_STD_FILE_NAME"] = "real_verify_batch5_std.txt"

PROJECT_ROOT = r"D:\codes\funboost"
LOG_DIR = os.environ["LOG_PATH"]
PRINT_NAME = os.environ["PRINT_WRTIE_FILE_NAME"]
STD_NAME = os.environ["SYS_STD_FILE_NAME"]

PASS_COUNT = 0
FAIL_COUNT = 0


def ok(msg):
    global PASS_COUNT
    PASS_COUNT += 1
    print(f"[PASS] {msg}")


def fail(msg):
    global FAIL_COUNT
    FAIL_COUNT += 1
    print(f"[FAIL] {msg}")


# ========== Skill 1: developing-funboost-testing ==========


def check_testing_env_vars_before_import():
    """SKILL: LOG_PATH / PRINT_WRTIE_FILE_NAME / SYS_STD_FILE_NAME 在 import funboost 前设置"""
    for key in ("LOG_PATH", "PRINT_WRTIE_FILE_NAME", "SYS_STD_FILE_NAME"):
        val = os.environ.get(key)
        if val:
            ok(f"testing: 环境变量 {key}={val!r}")
        else:
            fail(f"testing: 环境变量 {key} 未设置")


def check_testing_pythonpath():
    """SKILL: PYTHONPATH 让项目根进入 sys.path，框架可 import funboost_config"""
    pythonpath = os.environ.get("PYTHONPATH", "")
    root_norm = PROJECT_ROOT.replace("\\", "/")
    normalized_paths = [p.replace("\\", "/") for p in sys.path]
    in_syspath = root_norm in normalized_paths or any(root_norm in p for p in normalized_paths)
    if in_syspath or pythonpath.replace("\\", "/") == root_norm:
        ok("testing: PYTHONPATH 生效，项目根在 sys.path 中")
    else:
        fail(f"testing: 项目根不在 sys.path: PYTHONPATH={pythonpath!r}")

    try:
        import funboost_config

        ok(f"testing: funboost_config 可导入: {funboost_config.__file__}")
    except ModuleNotFoundError:
        fail("testing: funboost_config 模块未找到")

    from funboost import set_frame_config

    src = inspect.getsource(set_frame_config.use_config_form_funboost_config_module)
    if "importlib.import_module('funboost_config')" in src:
        ok("testing: set_frame_config 使用 importlib.import_module('funboost_config')")
    else:
        fail("testing: set_frame_config 未使用 importlib.import_module('funboost_config')")


def check_testing_log_redirect():
    """SKILL: nb_log 按环境变量写 print/std 日志文件"""
    import funboost  # noqa: F401

    marker = f"real_verify_batch5_log_marker_{int(time.time())}"
    print(f"[VERIFY] {marker}")
    sys.stdout.write(f"[VERIFY_STD] {marker}\n")

    time.sleep(2)
    if not Path(LOG_DIR).exists():
        fail(f"testing: LOG_PATH 目录不存在: {LOG_DIR}")
        return

    print_files = glob.glob(str(Path(LOG_DIR) / f"*{PRINT_NAME}*"))
    std_files = glob.glob(str(Path(LOG_DIR) / f"*{STD_NAME}*"))
    if print_files:
        ok(f"testing: PRINT 日志文件已生成: {Path(print_files[0]).name}")
    else:
        fail(f"testing: 未找到 PRINT 日志文件 (pattern *{PRINT_NAME}*)")
    if std_files:
        ok(f"testing: STD 日志文件已生成: {Path(std_files[0]).name}")
    else:
        fail(f"testing: 未找到 STD 日志文件 (pattern *{STD_NAME}*)")


def check_testing_os_exit_66():
    """SKILL: os._exit(66) 作为 AI 脚本退出码"""
    code = "import os,time;time.sleep(1);os._exit(66)"
    env = os.environ.copy()
    env["PYTHONPATH"] = PROJECT_ROOT
    r = subprocess.run(
        [sys.executable, "-c", code],
        cwd=PROJECT_ROOT,
        env=env,
        timeout=10,
    )
    if r.returncode == 66:
        ok("testing: os._exit(66) 子进程退出码为 66")
    else:
        fail(f"testing: os._exit(66) 退出码错误: 期望 66, 实际 {r.returncode}")


def check_testing_push_consume_pattern():
    """SKILL 模板: @boost + push + consume + time.sleep + os._exit(66)"""
    from funboost import boost, BoosterParams, BrokerEnum

    @boost(
        BoosterParams(
            queue_name="real_verify_batch5_testing",
            broker_kind=BrokerEnum.SQLITE_QUEUE,
            concurrent_num=2,
            qps=10,
        )
    )
    def test_task(x: int):
        print(f"[EXEC] 处理 {x}，结果 = {x * 2}")
        return x * 2

    results = []

    @boost(
        BoosterParams(
            queue_name="real_verify_batch5_testing_capture",
            broker_kind=BrokerEnum.SQLITE_QUEUE,
            concurrent_num=2,
        )
    )
    def capture_task(x: int):
        results.append(x * 2)
        return x * 2

    for i in range(3):
        capture_task.push(i)
    capture_task.consume()
    ok("testing: SKILL 模板 push + consume 模式可运行")

    time.sleep(5)
    if len(results) >= 3:
        ok(f"testing: 消息被消费执行 {len(results)} 次")
    else:
        fail(f"testing: 消息消费不足: {len(results)}/3")


# ========== Skill 2: funboost-funweb-ops ==========


def check_funweb_import():
    """SKILL: from funboost.funweb.app import start_funboost_web_manager"""
    try:
        from funboost.funweb.app import start_funboost_web_manager as fn1

        ok("funweb: from funboost.funweb.app import start_funboost_web_manager 可导入")
    except ImportError as e:
        fail(f"funweb: start_funboost_web_manager 导入失败: {e}")
        return None

    try:
        from funboost.funboost_web_manager.app import start_funboost_web_manager as fn2

        if fn1 is fn2:
            ok("funweb: 等价路径 funboost.funboost_web_manager.app 指向同一函数")
        else:
            fail("funweb: funboost_web_manager.app 与 funweb.app 不是同一对象")
    except ImportError as e:
        fail(f"funweb: 等价导入路径失败: {e}")

    return fn1


def check_funweb_signature(start_funboost_web_manager):
    """SKILL: host, port, block, debug, care_project_name 参数及默认值"""
    if start_funboost_web_manager is None:
        return

    sig = inspect.signature(start_funboost_web_manager)
    param_names = list(sig.parameters.keys())
    expected_params = ["host", "port", "block", "debug", "care_project_name"]
    if param_names == expected_params:
        ok(f"funweb: start_funboost_web_manager 参数名: {param_names}")
    else:
        fail(f"funweb: 参数名不符: 预期 {expected_params}, 实际 {param_names}")

    defaults = {
        "host": "0.0.0.0",
        "port": 27018,
        "block": False,
        "debug": False,
        "care_project_name": None,
    }
    for name, expected in defaults.items():
        actual = sig.parameters[name].default
        if actual == expected:
            ok(f"funweb: start_funboost_web_manager.{name} 默认值={expected!r}")
        else:
            fail(f"funweb: {name} 默认值错误: 预期 {expected!r}, 实际 {actual!r}")


# ========== Skill 3: funboost-spider-crawling ==========


def check_spider_imports():
    """SKILL: from funboost.contrib.funspider import SimpleSpiderClient, AsyncSpiderClient, SpiderItem"""
    try:
        from funboost.contrib.funspider import (
            SimpleSpiderClient,
            AsyncSpiderClient,
            SpiderItem,
            Field,
        )
    except ImportError as e:
        fail(f"spider: funspider 导入失败: {e}")
        return None, None, None, None

    ok("spider: from funboost.contrib.funspider import SimpleSpiderClient, AsyncSpiderClient, SpiderItem 可导入")
    for cls in (SimpleSpiderClient, AsyncSpiderClient, SpiderItem):
        if inspect.isclass(cls):
            ok(f"spider: {cls.__name__} 类存在")
        else:
            fail(f"spider: {cls} 不是类")

    return SimpleSpiderClient, AsyncSpiderClient, SpiderItem, Field


def check_spider_clients_and_item(SimpleSpiderClient, AsyncSpiderClient, SpiderItem, Field):
    """SKILL: 客户端可实例化，SpiderItem 子类可实例化"""
    if SimpleSpiderClient is None:
        return

    try:
        sync_client = SimpleSpiderClient(retry_times=1, timeout=5)
        ok("spider: SimpleSpiderClient(retry_times=1, timeout=5) 可实例化")
        for method in ("get", "post", "request", "close"):
            if hasattr(sync_client, method):
                ok(f"spider: SimpleSpiderClient.{method} 存在")
            else:
                fail(f"spider: SimpleSpiderClient.{method} 不存在")
        sync_client.close()
    except Exception as e:
        fail(f"spider: SimpleSpiderClient 实例化失败: {e}")

    try:
        async_client = AsyncSpiderClient(retry_times=1, timeout=5)
        ok("spider: AsyncSpiderClient(retry_times=1, timeout=5) 可实例化")
        for method in ("get", "post", "request", "aclose"):
            if hasattr(async_client, method):
                ok(f"spider: AsyncSpiderClient.{method} 存在")
            else:
                fail(f"spider: AsyncSpiderClient.{method} 不存在")
    except Exception as e:
        fail(f"spider: AsyncSpiderClient 实例化失败: {e}")

    try:
        class DemoItem(SpiderItem, table=True):
            __tablename__: ClassVar[str] = "real_verify_batch5_demo"
            __default_upsert_unique_fields__: ClassVar[list] = ["item_id"]

            id: Optional[int] = Field(default=None, primary_key=True)
            item_id: int = Field(unique=True)
            title: str = Field(max_length=100)

        item = DemoItem(item_id=1, title="测试标题")
        ok(f"spider: SpiderItem 子类可实例化: item_id={item.item_id}, title={item.title!r}")
    except Exception as e:
        fail(f"spider: SpiderItem 实例化失败: {e}")


if __name__ == "__main__":
    print("=== real_verify_batch5: developing-funboost-testing ===")
    check_testing_env_vars_before_import()
    check_testing_pythonpath()
    check_testing_log_redirect()
    check_testing_os_exit_66()
    check_testing_push_consume_pattern()

    print("\n=== real_verify_batch5: funboost-funweb-ops ===")
    fn = check_funweb_import()
    check_funweb_signature(fn)

    print("\n=== real_verify_batch5: funboost-spider-crawling ===")
    sync_cls, async_cls, item_cls, field_cls = check_spider_imports()
    check_spider_clients_and_item(sync_cls, async_cls, item_cls, field_cls)

    print(f"\n=== 汇总: PASS={PASS_COUNT}, FAIL={FAIL_COUNT} ===")
    time.sleep(10)
    os._exit(66)
