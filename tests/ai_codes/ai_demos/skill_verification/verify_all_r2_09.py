"""Round2 验证 r2_09：developing-funboost-broker / mixin / testing SKILL vs 教程/源码/AGENTS.md

broker:
  - register_custom_broker 参数名 broker_kind, publisher_class, consumer_class
  - AbstractPublisher/Consumer 抽象方法 _publish_impl/_dispatch_task/_confirm_consume/_requeue

mixin:
  - _submit_task(self, kw)
  - 三个后置钩子签名 _both_sync_and_aio / _frame / _aio_frame

testing:
  - PYTHONPATH 生效 + funboost_config 加载路径
  - os._exit(66) + LOG_PATH 三环境变量模式
"""
import glob
import inspect
import os
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
LOG_DIR = r"D:\pythonlogs\ai_console_outs"
_ts = int(time.time())
PRINT_NAME = f"verify_all_r2_09_{_ts}"
STD_NAME = f"verify_all_r2_09_std_{_ts}"

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


def read_skill(rel_path):
    path = os.path.join(PROJECT_ROOT, ".agents", "skills", rel_path, "SKILL.md")
    if os.path.isfile(path):
        return open(path, encoding="utf-8").read()
    fail(f"找不到 SKILL.md: {path}")
    return ""


def read_tutorial(rel_path):
    path = os.path.join(PROJECT_ROOT, "funboost", rel_path)
    if os.path.isfile(path):
        return open(path, encoding="utf-8").read()
    fail(f"找不到教程: {path}")
    return ""


# ── 1. developing-funboost-broker ───────────────────────────────────────────


def check_broker_register_custom_broker():
    """SKILL / 教程 §2: register_custom_broker(broker_kind, publisher_class, consumer_class)"""
    from funboost import register_custom_broker
    from funboost.factories.broker_kind__publsiher_consumer_type_map import (
        register_custom_broker as register_from_factory,
    )

    ok("register_custom_broker 可从 funboost 顶层导入")

    sig = inspect.signature(register_custom_broker)
    params = list(sig.parameters.keys())
    expected = ["broker_kind", "publisher_class", "consumer_class"]
    if params == expected:
        ok(f"register_custom_broker 参数名正确: {params}")
    else:
        fail(f"register_custom_broker 参数名错误: 期望 {expected}, 实际 {params}")

    if register_custom_broker is register_from_factory:
        ok("funboost 导出与工厂模块同一 register_custom_broker 对象")
    else:
        warn("funboost 与工厂模块 register_custom_broker 不是同一对象")

    skill = read_skill("developing-funboost-broker")
    tutorial = read_tutorial("md_for_ai/如何扩展增加新的中间件.md")
    if 'register_custom_broker("MY_BROKER"' in skill or "register_custom_broker('MY_BROKER'" in skill:
        ok("broker SKILL 示例使用 register_custom_broker(broker_kind, Publisher, Consumer)")
    else:
        fail("broker SKILL 未找到 register_custom_broker 三参数调用示例")

    if "register_custom_broker" in tutorial:
        ok("教程 md 提及 register_custom_broker")
    else:
        fail("教程 md 未提及 register_custom_broker")


def check_broker_abstract_methods():
    """SKILL / 教程: Publisher/Consumer 必须实现的抽象方法"""
    from funboost.consumers.base_consumer import AbstractConsumer
    from funboost.publishers.base_publisher import AbstractPublisher

    skill_pub = {"_publish_impl", "clear", "get_message_count", "close"}
    skill_con = {"_dispatch_task", "_confirm_consume", "_requeue"}

    def abstract_methods(cls):
        return {
            name
            for name, method in inspect.getmembers(cls, predicate=inspect.isfunction)
            if getattr(method, "__isabstractmethod__", False)
        }

    pub_abs = abstract_methods(AbstractPublisher)
    con_abs = abstract_methods(AbstractConsumer)

    if pub_abs == skill_pub:
        ok(f"AbstractPublisher 抽象方法: {sorted(pub_abs)}")
    else:
        fail(f"AbstractPublisher 抽象方法不符: SKILL={skill_pub}, 源码={pub_abs}")

    if con_abs == skill_con:
        ok(f"AbstractConsumer 抽象方法: {sorted(con_abs)}")
    else:
        fail(f"AbstractConsumer 抽象方法不符: SKILL={skill_con}, 源码={con_abs}")

    sig = inspect.signature(AbstractPublisher._publish_impl)
    if list(sig.parameters.keys()) == ["self", "msg"]:
        ok("AbstractPublisher._publish_impl(self, msg) 签名正确")
    else:
        fail(f"_publish_impl 签名异常: {sig}")

    sig = inspect.signature(AbstractConsumer._dispatch_task)
    if list(sig.parameters.keys()) == ["self"]:
        ok("AbstractConsumer._dispatch_task(self) 签名正确")
    else:
        fail(f"_dispatch_task 签名异常: {sig}")

    for method_name in ("_confirm_consume", "_requeue"):
        sig = inspect.signature(getattr(AbstractConsumer, method_name))
        if list(sig.parameters.keys()) == ["self", "kw"]:
            ok(f"AbstractConsumer.{method_name}(self, kw) 签名正确")
        else:
            fail(f"{method_name} 签名异常: {sig}")

    tutorial = read_tutorial("md_for_ai/如何扩展增加新的中间件.md")
    for marker in ("_publish_impl", "_dispatch_task", "_confirm_consume", "_requeue"):
        if marker in tutorial:
            ok(f"教程 md 列出抽象方法 {marker}")
        else:
            fail(f"教程 md 未列出 {marker}")


def check_broker_skill_vs_tutorial():
    """SKILL 与教程 md 关键表述对照"""
    skill = read_skill("developing-funboost-broker")
    tutorial = read_tutorial("md_for_ai/如何扩展增加新的中间件.md")

    if "consumer_override_cls" in skill and "publisher_override_cls" in skill:
        ok("broker SKILL 含 override_cls 方式")
    else:
        fail("broker SKILL 缺少 override_cls 说明")

    if "BrokerEnum.EMPTY" in tutorial:
        ok("教程 md 说明 override_cls + BrokerEnum.EMPTY 可新增全新 broker")
        if "BrokerEnum.EMPTY" not in skill:
            warn("broker SKILL 未提及 override_cls + BrokerEnum.EMPTY 新增 broker（教程有）")
    else:
        warn("教程 md 未找到 BrokerEnum.EMPTY 说明")

    if "self._submit_task(kw)" in skill:
        ok("broker SKILL 强调 _dispatch_task 内调用 self._submit_task(kw)")
    else:
        fail("broker SKILL 未强调 _submit_task 调用")

    if "broker_exclusive_config" in skill and '["my_key"]' in skill.replace("'", '"'):
        ok("broker SKILL 使用 broker_exclusive_config[] 方括号访问")
    else:
        warn("broker SKILL broker_exclusive_config 访问示例可能不完整")

    if skill.rstrip().endswith("|"):
        warn("broker SKILL.md 第 199 行附近有多余 trailing `|` 字符（Markdown 格式瑕疵）")


# ── 2. developing-funboost-mixin ────────────────────────────────────────────


def check_mixin_submit_task_signature():
    from funboost.consumers.base_consumer import AbstractConsumer

    sig = inspect.signature(AbstractConsumer._submit_task)
    params = list(sig.parameters.keys())
    if params == ["self", "kw"]:
        ok(f"AbstractConsumer._submit_task 签名正确: {sig}")
    else:
        fail(f"_submit_task 签名不符: {params}")

    skill = read_skill("developing-funboost-mixin")
    if "def _submit_task(self, kw):" in skill:
        ok("mixin SKILL 示例 _submit_task(self, kw) 与源码一致")
    else:
        fail("mixin SKILL 未找到 _submit_task(self, kw) 示例")


def check_mixin_three_hook_signatures():
    """SKILL / base_consumer.py / 教程: 三个后置钩子签名"""
    from funboost.consumers.base_consumer import AbstractConsumer

    hooks = {
        "_both_sync_and_aio_frame_custom_record_process_info_func": False,
        "_frame_custom_record_process_info_func": False,
        "_aio_frame_custom_record_process_info_func": True,
    }
    expected_params = ["self", "current_function_result_status", "kw"]

    for name, is_async in hooks.items():
        method = getattr(AbstractConsumer, name, None)
        if method is None:
            fail(f"AbstractConsumer 缺少 {name}")
            continue
        sig = inspect.signature(method)
        params = list(sig.parameters.keys())
        if params == expected_params:
            ok(f"AbstractConsumer.{name}{sig} 参数签名正确")
        else:
            fail(f"{name} 参数不符: 期望 {expected_params}, 实际 {params}")
        if inspect.iscoroutinefunction(method) == is_async:
            ok(f"{name} async={is_async} 与源码一致")
        else:
            fail(f"{name} async 属性不符: 预期 {is_async}")

    tutorial = read_tutorial("md_for_ai/如何扩展增加新的中间件.md")
    for name in hooks:
        if name in tutorial:
            ok(f"教程 md 列出 mixin 钩子 {name}")
        else:
            fail(f"教程 md 未列出 {name}")

    skill = read_skill("developing-funboost-mixin")
    for name in hooks:
        if name in skill:
            ok(f"mixin SKILL 文档含 {name}")
        else:
            fail(f"mixin SKILL 未文档化 {name}")


def check_mixin_skill_content():
    from funboost.core.func_params_model import BoosterParams as BoosterParamsModel

    model_fields = set(BoosterParamsModel.model_fields.keys())
    for field in ("consumer_override_cls", "publisher_override_cls", "user_options"):
        if field in model_fields:
            ok(f"BoosterParams.{field} 存在（mixin SKILL 使用）")
        else:
            fail(f"BoosterParams.{field} 不存在")

    skill = read_skill("developing-funboost-mixin")
    if "super()._submit_task(kw)" in skill:
        ok("mixin SKILL 强调 super()._submit_task(kw)")
    else:
        fail("mixin SKILL 未强调 super()._submit_task")

    if "simple_run_in_executor" in skill:
        ok("mixin SKILL 提及 simple_run_in_executor 复用同步 IO 逻辑")
    else:
        warn("mixin SKILL 未提及 simple_run_in_executor")


# ── 3. developing-funboost-testing ──────────────────────────────────────────


def check_testing_pythonpath():
    """AGENTS.md §十二 / testing SKILL: PYTHONPATH=项目根"""
    pythonpath = os.environ.get("PYTHONPATH", "")
    normalized_paths = [p.replace("\\", "/") for p in sys.path]
    root_norm = PROJECT_ROOT.replace("\\", "/")
    in_syspath = root_norm in normalized_paths or any(root_norm in p for p in normalized_paths)
    if in_syspath or pythonpath.replace("\\", "/") == root_norm:
        ok("PYTHONPATH 生效，项目根在 sys.path 中")
    else:
        fail(f"项目根不在 sys.path: PYTHONPATH={pythonpath!r}")

    try:
        import funboost_config

        ok(f"funboost_config 可导入: {funboost_config.__file__}")
    except ModuleNotFoundError:
        warn("funboost_config 尚未生成（首次运行会自动创建）")

    import funboost.set_frame_config as sfc

    src = inspect.getsource(sfc.use_config_form_funboost_config_module)
    if "import_module('funboost_config')" in src or 'import_module("funboost_config")' in src:
        ok("set_frame_config 通过 import_module('funboost_config') 加载（AGENTS.md / SKILL）")
    else:
        fail("set_frame_config 未使用 import_module('funboost_config')")


def check_testing_log_env_and_os_exit():
    """AGENTS.md / testing SKILL: LOG_PATH 三变量 + os._exit(66)"""
    for key in ("LOG_PATH", "PRINT_WRTIE_FILE_NAME", "SYS_STD_FILE_NAME"):
        if os.environ.get(key):
            ok(f"环境变量 {key} 已设置")
        else:
            fail(f"环境变量 {key} 未设置")

    import funboost  # noqa: F401

    print(f"[VERIFY r2_09] print 重定向 {_ts}")
    sys.stdout.write(f"[VERIFY r2_09] stdout 重定向 {_ts}\n")
    time.sleep(2)

    if Path(LOG_DIR).exists():
        print_files = glob.glob(str(Path(LOG_DIR) / f"*{PRINT_NAME}*"))
        std_files = glob.glob(str(Path(LOG_DIR) / f"*{STD_NAME}*"))
        if print_files:
            ok(f"PRINT 日志已生成: {Path(print_files[0]).name}")
        else:
            fail(f"未找到 PRINT 日志 *{PRINT_NAME}*")
        if std_files:
            ok(f"STD 日志已生成: {Path(std_files[0]).name}")
        else:
            fail(f"未找到 STD 日志 *{STD_NAME}*")
    else:
        fail(f"LOG_PATH 目录不存在: {LOG_DIR}")

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
        ok("os._exit(66) 子进程退出码为 66（AGENTS.md / testing SKILL 推荐模式）")
    else:
        fail(f"os._exit(66) 退出码错误: 期望 66, 实际 {r.returncode}")


def check_testing_skill_vs_agents():
    skill = read_skill("developing-funboost-testing")
    agents_path = os.path.join(PROJECT_ROOT, "AGENTS.md")
    agents = open(agents_path, encoding="utf-8").read() if os.path.isfile(agents_path) else ""

    dirs_skill = [
        "tests/ai_codes/ai_demos/",
        "tests/ai_codes/regression_testing/",
        "test_frame/",
    ]
    for d in dirs_skill:
        if d in skill:
            ok(f"testing SKILL 目录规范含 {d}")
        else:
            fail(f"testing SKILL 缺少目录 {d}")

    if "os._exit(66)" in skill and "os._exit(66)" in agents:
        ok("testing SKILL 与 AGENTS.md 均推荐 os._exit(66)")
    else:
        fail("testing SKILL 或 AGENTS.md 缺少 os._exit(66)")

    if "subprocess.run" in skill and "timeout=30" in skill:
        ok("testing SKILL 含 subprocess.run + timeout 方式二")
    else:
        warn("testing SKILL subprocess 示例可能不完整")

    if "不要在脚本内设置" in skill or "脚本内设置无效" in skill:
        ok("testing SKILL 说明 PYTHONPATH 须在命令行设置")
    else:
        warn("testing SKILL 未明确 PYTHONPATH 不在脚本内设置")

    if "SQLITE_QUEUE" in skill:
        ok("testing SKILL 推荐 SQLITE_QUEUE 零配置测试")
    else:
        warn("testing SKILL 未推荐 SQLITE_QUEUE")


def check_testing_functional_pattern():
    """SKILL 模板: push + consume + sleep + os._exit(66)"""
    from funboost import boost, BoosterParams, BrokerEnum

    @boost(
        BoosterParams(
            queue_name=f"verify_all_r2_09_{_ts}",
            broker_kind=BrokerEnum.SQLITE_QUEUE,
            concurrent_num=2,
            qps=10,
        )
    )
    def mini_task(x: int):
        print(f"[MINI r2_09] x={x}")
        return x * 2

    for i in range(3):
        mini_task.push(i)
    mini_task.consume()
    ok("testing SKILL push + consume 模式可运行")


if __name__ == "__main__":
    print("=== developing-funboost-broker SKILL 验证 ===")
    check_broker_register_custom_broker()
    check_broker_abstract_methods()
    check_broker_skill_vs_tutorial()

    print("\n=== developing-funboost-mixin SKILL 验证 ===")
    check_mixin_submit_task_signature()
    check_mixin_three_hook_signatures()
    check_mixin_skill_content()

    print("\n=== developing-funboost-testing SKILL 验证 ===")
    check_testing_pythonpath()
    check_testing_log_env_and_os_exit()
    check_testing_skill_vs_agents()
    check_testing_functional_pattern()

    print(f"\n=== 汇总: PASS={len(PASS)}, FAIL={len(FAIL)}, WARN={len(WARN)} ===")
    for w in WARN:
        print(f"  WARN: {w}")
    if FAIL:
        for item in FAIL:
            print(f"  FAIL: {item}")
        os._exit(1)
    print("[DONE] verify_all_r2_09 全部通过")
    time.sleep(5)
    os._exit(66)
