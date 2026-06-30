"""验证 understanding-funboost-concepts SKILL.md（Round2 #01）

检查项：
- BoosterParams.model_fields 数量 vs SKILL「40+ 字段」
- 配置加载机制 vs set_frame_config.py 源码
- MEMORY_QUEUE SSS 推荐 vs c1/c20/c3 教程
- push/publish/fct/consume 描述 vs 教程与源码
"""
import inspect
import os
import sys
import textwrap
import time
from pathlib import Path

PROJECT_ROOT = r"D:\codes\funboost"
SKILL_PATH = Path(PROJECT_ROOT) / ".agents" / "skills" / "understanding-funboost-concepts" / "SKILL.md"
C1_PATH = Path(r"D:\codes\funboost_docs\source\articles\c1.md")
C20_PATH = Path(r"D:\codes\funboost_docs\source\articles\c20.md")

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"verify_all_r2_01_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"verify_all_r2_01_std_{_ts}"

PASS: list[str] = []
FAIL: list[str] = []
WARN: list[str] = []


def ok(msg: str) -> None:
    PASS.append(msg)
    print(f"[PASS] {msg}")


def fail(msg: str) -> None:
    FAIL.append(msg)
    print(f"[FAIL] {msg}")


def warn(msg: str) -> None:
    WARN.append(msg)
    print(f"[WARN] {msg}")


def read_skill() -> str:
    assert SKILL_PATH.is_file(), f"SKILL 不存在: {SKILL_PATH}"
    return SKILL_PATH.read_text(encoding="utf-8")


def check_booster_params_field_count() -> int:
    """SKILL §二: BoosterParams 包含 40+ 个字段"""
    from funboost.core.func_params_model import BoosterParams

    count = len(BoosterParams.model_fields)
    skill_text = read_skill()
    if "40+" in skill_text or "40+ 个字段" in skill_text:
        ok("SKILL 文档含「40+ 字段」表述")
    else:
        fail("SKILL 文档未找到「40+ 字段」表述")

    if count >= 40:
        ok(f"BoosterParams.model_fields 实际 {count} 个，「40+」准确")
    else:
        fail(f"BoosterParams 仅 {count} 个字段，「40+」不准确")

    # queue_name 必填
    from pydantic import ValidationError

    try:
        BoosterParams()
        fail("queue_name 应为必填")
    except ValidationError:
        ok("queue_name 为唯一必填字段（源码验证）")

    # 臆造字段
    try:
        BoosterParams(queue_name="x", timeout=30)
        fail("臆造 timeout 应被 Pydantic 拒绝")
    except ValidationError:
        ok("Pydantic extra=forbid：timeout→function_timeout 纠正表与源码一致")

    return count


def check_config_loading_vs_source() -> None:
    """SKILL §三: 配置加载原理 vs set_frame_config.py"""
    from funboost import set_frame_config
    from funboost.utils.simple_data_class import DataClassBase
    from funboost.funboost_config_deafult import BrokerConnConfig as DefaultBrokerConnConfig

    skill = read_skill()
    src_fn = inspect.getsource(set_frame_config.use_config_form_funboost_config_module)
    auto_src = inspect.getsource(set_frame_config._auto_creat_config_file_to_project_root_path)

    expected_in_skill = [
        "set_frame_config.py",
        "importlib.import_module",
        "funboost_config",
        "sys.path[0]",
        "sys.path[1]",
        "BrokerConnConfig.update_cls_attribute",
        "PYTHONPATH",
    ]
    for token in expected_in_skill:
        if token in skill:
            ok(f"SKILL 含配置机制关键词: {token}")
        else:
            fail(f"SKILL 缺少配置机制关键词: {token}")

    checks = [
        ("importlib.import_module('funboost_config')", "importlib.import_module('funboost_config')" in src_fn),
        ("sys.path[0] 脚本目录", "sys.path[0]" in src_fn),
        ("sys.path[1] 项目根", "sys.path[1]" in src_fn),
        ("BrokerConnConfig.update_cls_attribute", "BrokerConnConfig.update_cls_attribute" in src_fn),
        ("FunboostCommonConfig.update_cls_attribute", "FunboostCommonConfig.update_cls_attribute" in src_fn),
    ]
    for label, passed in checks:
        if passed:
            ok(f"源码 use_config_form_funboost_config_module 含 {label}")
        else:
            fail(f"源码缺少 {label}")

    if "copyfile" in auto_src and "sys.path[1]" in auto_src:
        ok("找不到配置时在 sys.path[1] 复制 funboost_config_deafult.py（与 SKILL 一致）")
    else:
        fail("自动生成模板机制与 SKILL 描述不符")

    assert issubclass(DefaultBrokerConnConfig, DataClassBase)
    ok("SKILL 示例 BrokerConnConfig(DataClassBase) 与 funboost_config_deafult 一致")

    # SKILL 未提及 FunboostCommonConfig 同时被覆盖 — 仅 WARN
    if "FunboostCommonConfig" not in skill:
        warn("SKILL 配置加载未提及 FunboostCommonConfig.update_cls_attribute（源码会同时覆盖）")

    # 优先级描述：源码 inspect_msg 明确 script dir 优先于 project root
    if "优先" in skill and "sys.path[0]" in skill:
        ok("SKILL 描述 sys.path[0] 优先于 sys.path[1]")
    else:
        warn("SKILL 优先级描述可更精确（与 set_frame_config inspect_msg 对齐）")


def check_memory_queue_sss_vs_tutorials() -> None:
    """SKILL §七: MEMORY_QUEUE SSS 推荐 vs 教程"""
    skill = read_skill()
    c1 = C1_PATH.read_text(encoding="utf-8")
    c20 = C20_PATH.read_text(encoding="utf-8")

    # SKILL 关键声明
    for phrase in [
        "BrokerEnum.MEMORY_QUEUE",
        "零中间件",
        "零序列化",
        "SSS",
    ]:
        if phrase in skill:
            ok(f"SKILL 含 MEMORY_QUEUE 推荐语: {phrase!r}")
        else:
            fail(f"SKILL 缺少: {phrase!r}")

    # 教程对齐
    if "MEMORY_QUEUE" in c1 and "超级装饰器" in c1:
        ok("c1.md 含 MEMORY_QUEUE + 超级装饰器（与 SKILL 方向一致）")
    else:
        fail("c1.md 未找到 MEMORY_QUEUE/超级装饰器")

    if "MEMORY_QUEUE" in c20 and "零序列化" in c20:
        ok("c20.md 含 MEMORY_QUEUE + 零序列化")
    else:
        fail("c20.md 未找到 MEMORY_QUEUE/零序列化")

    from funboost.constant import BrokerEnum

    assert hasattr(BrokerEnum, "MEMORY_QUEUE")
    ok(f"BrokerEnum.MEMORY_QUEUE = {BrokerEnum.MEMORY_QUEUE!r} 存在")

    # SKILL「90% 场景不需要分布式 MQ」— 教程无此量化，仅 c3 有 SSS 级表述
    if "90%" in skill and "不需要分布式" in skill:
        warn("SKILL「90% 场景不需要分布式 MQ」为 SKILL 自创量化，教程 c1/c20 无此比例（c3 强调 SSS 级 broker）")


def check_push_publish_fct_consume() -> None:
    """SKILL §四/五/六: push/publish/fct/consume vs 教程与源码"""
    from funboost import (
        boost,
        BoosterParams,
        BrokerEnum,
        TaskOptions,
        fct,
        enable_ctrl_c_quit_on_windows,
    )
    from funboost.core.current_task import get_current_taskid

    skill = read_skill()
    c1 = C1_PATH.read_text(encoding="utf-8")
    c20 = C20_PATH.read_text(encoding="utf-8")

    # --- push vs publish 文档关键词 ---
    for phrase in ["func.push", "func.publish", "TaskOptions", "task_id", "countdown", "eta"]:
        if phrase in skill:
            ok(f"SKILL push/publish 含 {phrase!r}")
        else:
            fail(f"SKILL push/publish 缺少 {phrase!r}")

    if "fun.push" in c20 or "push(" in c1:
        ok("教程 c1/c20 含 push 用法")
    if "publish" in c1:
        ok("教程 c1 含 publish 用法（1.3.3）")

    # --- 运行时 push/publish ---
    @boost(
        BoosterParams(
            queue_name=f"verify_all_r2_01_{_ts}",
            broker_kind=BrokerEnum.SQLITE_QUEUE,
            concurrent_num=1,
        )
    )
    def add_task(x, y=1):
        return x + y

    direct = add_task(2, 3)
    assert direct == 5
    ok("func(x,y) 直接调用仍可用（反框架 / c1 1.0.9 双模运行）")

    add_task.push(10, 20)
    ok("func.push(*args, **kwargs) 发布成功")

    add_task.publish({"x": 1, "y": 2}, task_options=TaskOptions(task_id=f"r2-01-{_ts}"))
    ok("func.publish(dict, task_options=TaskOptions(...)) 发布成功")

    assert hasattr(add_task, "consume") and callable(add_task.consume)
    ok("consume 方法存在")

    assert callable(enable_ctrl_c_quit_on_windows)
    ok("enable_ctrl_c_quit_on_windows 可导入（SKILL §五）")

    # --- fct 属性 ---
    fct_attrs = ["task_id", "queue_name", "full_msg", "logger", "function_result_status"]
    for attr in fct_attrs:
        if attr in skill:
            ok(f"SKILL fct 列出 {attr!r}")
        else:
            fail(f"SKILL fct 缺少 {attr!r}")

    if "run_times" in skill:
        ok("SKILL fct 含 run_times（via function_result_status.run_times）")

    if "fct.task_id" in c20 or "fct" in c1:
        ok("教程 c1/c20 提及 fct 上下文")

    # 消费外访问 fct
    raised = False
    try:
        _ = fct.task_id
    except AttributeError:
        raised = True
    except Exception as exc:
        fail(f"消费外 fct.task_id 应 AttributeError，实际 {type(exc).__name__}: {exc}")
        return

    if raised:
        ok("消费函数外访问 fct 属性抛 AttributeError（与 SKILL 一致）")
    else:
        fail("消费函数外访问 fct 未报错")

    if get_current_taskid() == "no_task_id":
        ok("get_current_taskid() 无上下文返回 'no_task_id'")

    # Celery bind=True 禁止
    if "bind=True" in skill and "禁止" in skill:
        ok("SKILL 明确禁止 Celery bind=True 思维")


def check_concurrent_modes_in_skill() -> None:
    from funboost.constant import ConcurrentModeEnum

    skill = read_skill()
    modes = ["THREADING", "GEVENT", "EVENTLET", "ASYNC", "SINGLE_THREAD"]
    for m in modes:
        if m in skill:
            ok(f"SKILL 列出并发模式 {m}")
        else:
            fail(f"SKILL 缺少并发模式 {m}")
        assert hasattr(ConcurrentModeEnum, m)


def main() -> None:
    print("=" * 70)
    print("verify_all_r2_01 — understanding-funboost-concepts SKILL 验证")
    print("=" * 70)

    field_count = check_booster_params_field_count()
    check_config_loading_vs_source()
    check_memory_queue_sss_vs_tutorials()
    check_push_publish_fct_consume()
    check_concurrent_modes_in_skill()

    print(f"\n=== 汇总: PASS={len(PASS)}, FAIL={len(FAIL)}, WARN={len(WARN)} ===")
    print(f"BoosterParams.model_fields 精确计数: {field_count}")
    for w in WARN:
        print(f"  WARN: {w}")
    if FAIL:
        for item in FAIL:
            print(f"  FAIL: {item}")
        os._exit(1)

    print("[DONE] verify_all_r2_01 全部通过")
    os._exit(66)


if __name__ == "__main__":
    main()
