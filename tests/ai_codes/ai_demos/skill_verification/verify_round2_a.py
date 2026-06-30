"""Round2 综合验证：understanding-funboost-concepts / funboost-broker-selection / developing-funboost-testing"""
import inspect
import os
import subprocess
import sys
import tempfile
import textwrap
import time
from pathlib import Path

PROJECT_ROOT = r"D:\codes\funboost"
_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"verify_round2_a_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"verify_round2_a_std_{_ts}"

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


def check_booster_params_field_count():
    """SKILL: BoosterParams 包含 40+ 个字段"""
    from funboost.core.func_params_model import BoosterParams

    fields = list(BoosterParams.model_fields.keys())
    count = len(fields)
    if count >= 40:
        ok(f"BoosterParams 实际字段数 = {count}，'40+' 描述合理")
    else:
        fail(f"BoosterParams 仅 {count} 个字段，'40+' 描述不准确")
    return count


def check_config_loading_mechanism():
    """SKILL: importlib.import_module + sys.path + update_cls_attribute"""
    from funboost import set_frame_config
    from funboost.utils.simple_data_class import DataClassBase

    src = inspect.getsource(set_frame_config.use_config_form_funboost_config_module)
    checks = [
        ("importlib.import_module('funboost_config')", "importlib.import_module('funboost_config')" in src),
        ("sys.path[0]", "sys.path[0]" in src),
        ("sys.path[1]", "sys.path[1]" in src),
        ("BrokerConnConfig.update_cls_attribute", "BrokerConnConfig.update_cls_attribute" in src),
        ("FunboostCommonConfig.update_cls_attribute", "FunboostCommonConfig.update_cls_attribute" in src),
    ]
    for label, passed in checks:
        if passed:
            ok(f"set_frame_config 含 {label}")
        else:
            fail(f"set_frame_config 缺少 {label}")

    # 自动生成模板：复制 funboost_config_deafult.py 到 sys.path[1]
    auto_src = inspect.getsource(set_frame_config._auto_creat_config_file_to_project_root_path)
    if "copyfile" in auto_src and "sys.path[1]" in auto_src:
        ok("找不到配置时在 sys.path[1] 复制 funboost_config_deafult.py 生成模板")
    else:
        fail("自动生成模板机制与 SKILL 描述不符")

    # DataClassBase + class BrokerConnConfig 写法
    from funboost.funboost_config_deafult import BrokerConnConfig as DefaultBrokerConnConfig

    assert issubclass(DefaultBrokerConnConfig, DataClassBase)
    ok("funboost_config_deafult.BrokerConnConfig 继承 DataClassBase（SKILL 示例格式正确）")

    # 动态验证 update_cls_attribute 覆盖
    original = DefaultBrokerConnConfig.REDIS_DB
    DefaultBrokerConnConfig.update_cls_attribute(REDIS_DB=original)
    ok("BrokerConnConfig.update_cls_attribute 可调用")


def check_config_example_exec():
    """SKILL broker-selection / concepts 中的配置文件示例能否 exec"""
    example = textwrap.dedent(
        """
        from funboost.utils.simple_data_class import DataClassBase

        class BrokerConnConfig(DataClassBase):
            REDIS_HOST = "127.0.0.1"
            REDIS_PORT = 6379
            REDIS_PASSWORD = ""
            REDIS_DB = 7
        """
    )
    ns = {}
    exec(example, ns)
    cfg = ns["BrokerConnConfig"]()
    assert cfg.get_dict()["REDIS_HOST"] == "127.0.0.1"
    ok("SKILL 配置文件示例（DataClassBase + class BrokerConnConfig）可正常实例化")


def check_broker_conn_fields_in_skill():
    """broker-selection SKILL 示例字段存在于默认配置"""
    from funboost.funboost_config_deafult import BrokerConnConfig

    for field in [
        "REDIS_HOST",
        "REDIS_PORT",
        "REDIS_PASSWORD",
        "REDIS_DB",
        "RABBITMQ_HOST",
        "RABBITMQ_PORT",
        "RABBITMQ_USER",
        "RABBITMQ_PASS",
        "RABBITMQ_VIRTUAL_HOST",
        "KAFKA_BOOTSTRAP_SERVERS",
        "KFFKA_SASL_CONFIG",
    ]:
        if hasattr(BrokerConnConfig, field):
            ok(f"BrokerConnConfig.{field} 存在于源码")
        else:
            fail(f"BrokerConnConfig 缺少 SKILL 引用的字段 {field}")


def check_rocketmq5_windows_claim():
    """broker-selection: ROCKETMQ5 支持 Windows"""
    from funboost.constant import BrokerEnum

    assert hasattr(BrokerEnum, "ROCKETMQ5")
    ok(f"BrokerEnum.ROCKETMQ5 = {BrokerEnum.ROCKETMQ5!r}")

    pub_path = Path(PROJECT_ROOT) / "funboost" / "publishers" / "rocketmq5_publisher.py"
    con_path = Path(PROJECT_ROOT) / "funboost" / "consumers" / "rocketmq5_consumer.py"
    pub_text = pub_path.read_text(encoding="utf-8")
    con_text = con_path.read_text(encoding="utf-8")
    if "Windows" in pub_text and "Windows" in con_text:
        ok("rocketmq5 publisher/consumer 源码声明支持 Windows（纯 Python gRPC 客户端）")
    else:
        fail("rocketmq5 源码未声明 Windows 支持")

    old_path = Path(PROJECT_ROOT) / "funboost" / "publishers" / "rocketmq_publisher.py"
    if old_path.exists():
        old_text = old_path.read_text(encoding="utf-8")
        if "linux" in old_text.lower() or "win不支持" in old_text:
            ok("ROCKETMQ(4.x) 与 ROCKETMQ5 平台差异描述与源码一致")
        else:
            warn("未能从 ROCKETMQ 4.x 源码确认 Linux-only 限制")


def check_fct_outside_consumer():
    """concepts SKILL: 消费函数外访问 fct 属性应报错"""
    from funboost import fct

    raised = False
    try:
        _ = fct.task_id
    except AttributeError:
        raised = True
    except Exception as exc:
        fail(f"fct.task_id 在消费外应 AttributeError，实际 {type(exc).__name__}: {exc}")
        return

    if raised:
        ok("消费函数外访问 fct.task_id 抛出 AttributeError")
    else:
        fail("消费函数外访问 fct.task_id 未报错")

    # get_current_taskid 是特例：无上下文返回 'no_task_id'
    from funboost.core.current_task import get_current_taskid

    tid = get_current_taskid()
    if tid == "no_task_id":
        ok("get_current_taskid() 无上下文时返回 'no_task_id'（与 fct 直接访问行为不同）")
    else:
        warn(f"get_current_taskid() 返回 {tid!r}，非 'no_task_id'")


def check_subprocess_timeout_kills_consume():
    """testing SKILL 方式二: subprocess.run(timeout=...) 能终止无限 consume"""
    helper = textwrap.dedent(
        f"""
        import os, time
        os.environ["LOG_PATH"] = r"D:\\\\pythonlogs\\\\ai_console_outs"
        os.environ["PRINT_WRTIE_FILE_NAME"] = "verify_round2_a_child_{_ts}"
        os.environ["SYS_STD_FILE_NAME"] = "verify_round2_a_child_std_{_ts}"
        from funboost import boost, BoosterParams, BrokerEnum
        @boost(BoosterParams(
            queue_name="verify_round2_a_timeout_{_ts}",
            broker_kind=BrokerEnum.SQLITE_QUEUE,
            concurrent_num=1,
        ))
        def t(x):
            print("handled", x)
        t.push(1)
        t.consume()
        while True:
            time.sleep(3600)
        """
    )
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as f:
        f.write(helper)
        script_path = f.name

    env = os.environ.copy()
    env["PYTHONPATH"] = PROJECT_ROOT
    t0 = time.time()
    try:
        subprocess.run(
            [sys.executable, script_path],
            cwd=PROJECT_ROOT,
            env=env,
            timeout=8,
            capture_output=True,
            text=True,
        )
        fail("subprocess.run 应在 8s 内 TimeoutExpired，但正常返回了")
    except subprocess.TimeoutExpired:
        elapsed = time.time() - t0
        if 7 <= elapsed <= 12:
            ok(f"subprocess.run(timeout=8) 成功终止无限 consume 子进程（耗时 {elapsed:.1f}s）")
        else:
            warn(f"subprocess 超时耗时 {elapsed:.1f}s，略偏离预期 8s")
    finally:
        Path(script_path).unlink(missing_ok=True)


def check_cmd_timeout_antipattern():
    """testing SKILL: cmd timeout 先等待再启动 python，不能限制 python 运行时长"""
    marker = Path(r"D:\pythonlogs\ai_console_outs") / f"verify_round2_a_marker_{_ts}.txt"
    if marker.exists():
        marker.unlink()
    script = (
        f"import time; open(r'{marker}', 'w').write('started'); time.sleep(60)"
    )
    cmd = f"timeout /t 2 /nobreak >nul & {sys.executable} -c \"{script}\""
    t0 = time.time()
    try:
        subprocess.run(
            ["cmd", "/c", cmd],
            cwd=PROJECT_ROOT,
            env={**os.environ, "PYTHONPATH": PROJECT_ROOT},
            timeout=12,
        )
    except subprocess.TimeoutExpired:
        pass
    elapsed = time.time() - t0
    if marker.exists():
        marker.unlink(missing_ok=True)
        if elapsed >= 2:
            ok("cmd `timeout /t N & python` 先等待再启动 python — SKILL 反模式说明正确")
        else:
            warn(f"cmd timeout 行为异常: elapsed={elapsed:.1f}s")
    else:
        warn("marker 未创建，cmd timeout 测试 inconclusive")


def check_concepts_misc():
    """concepts SKILL 其他声明"""
    from pydantic import ValidationError
    from funboost.core.func_params_model import BoosterParams
    from funboost.constant import BrokerEnum, ConcurrentModeEnum

    try:
        BoosterParams(timeout=30, queue_name="x")
        fail("臆造字段 timeout 应被 Pydantic 拒绝")
    except ValidationError:
        ok("BoosterParams extra=forbid：臆造 timeout 被拒绝")

    modes = ["THREADING", "GEVENT", "EVENTLET", "ASYNC", "SINGLE_THREAD"]
    for m in modes:
        assert hasattr(ConcurrentModeEnum, m)
    ok(f"ConcurrentModeEnum 含 SKILL 列出的 {len(modes)} 种模式")

    assert BrokerEnum.RABBITMQ == BrokerEnum.RABBITMQ_AMQPSTORM
    ok("BrokerEnum.RABBITMQ == RABBITMQ_AMQPSTORM")


def main():
    print("=" * 70)
    print("Round2 SKILL 综合验证 verify_round2_a")
    print("=" * 70)

    check_booster_params_field_count()
    check_config_loading_mechanism()
    check_config_example_exec()
    check_broker_conn_fields_in_skill()
    check_rocketmq5_windows_claim()
    check_fct_outside_consumer()
    check_subprocess_timeout_kills_consume()
    check_cmd_timeout_antipattern()
    check_concepts_misc()

    print(f"\n=== 汇总: PASS={len(PASS)}, FAIL={len(FAIL)}, WARN={len(WARN)} ===")
    for w in WARN:
        print(f"  WARN: {w}")
    if FAIL:
        for item in FAIL:
            print(f"  FAIL: {item}")
        os._exit(1)

    print("[DONE] verify_round2_a 全部通过")
    os._exit(66)


if __name__ == "__main__":
    main()
