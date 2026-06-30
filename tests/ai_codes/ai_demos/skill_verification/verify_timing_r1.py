"""验证 funboost-timing-jobs SKILL.md 的技术准确性（r1）"""
import inspect
import os
import time
from datetime import datetime, timedelta

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
_ts = int(time.time())
os.environ["PRINT_WRTIE_FILE_NAME"] = f"verify_timing_r1_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"verify_timing_r1_std_{_ts}"

from funboost import boost, BoosterParams, BrokerEnum, ApsJobAdder, enable_ctrl_c_quit_on_windows
from funboost.core.func_params_model import BoosterParams as BoosterParamsModel
from funboost.timing_job import ApsJobAdder as ApsJobAdderFromSubpkg
from funboost.timing_job.timing_push import ApsJobAdder as ApsJobAdderFromModule

PASS = []
FAIL = []


def ok(msg):
    PASS.append(msg)
    print(f"[PASS] {msg}")


def fail(msg):
    FAIL.append(msg)
    print(f"[FAIL] {msg}")


def check_exports():
    import funboost

    if hasattr(funboost, "ApsJobAdder"):
        ok("funboost 导出 ApsJobAdder")
    else:
        fail("funboost 未导出 ApsJobAdder")

    if ApsJobAdder is ApsJobAdderFromSubpkg is ApsJobAdderFromModule:
        ok("ApsJobAdder 三处导入路径一致")
    else:
        fail("ApsJobAdder 导入路径不一致")


def check_booster_params_timing_fields():
    """SKILL 未详述但源码存在的定时相关 BoosterParams 字段"""
    model_fields = BoosterParamsModel.model_fields
    for field in (
        "delay_task_apscheduler_jobstores_kind",
        "allow_run_time_cron",
        "schedule_tasks_on_main_thread",
    ):
        if field in model_fields:
            ok(f"BoosterParams.{field} 存在于源码")
        else:
            fail(f"BoosterParams.{field} 不存在")

    defaults = BoosterParamsModel(queue_name="__timing_defaults__")
    if defaults.delay_task_apscheduler_jobstores_kind == "redis":
        ok("BoosterParams.delay_task_apscheduler_jobstores_kind 默认值='redis'")
    else:
        fail(
            f"delay_task_apscheduler_jobstores_kind 默认值错误: "
            f"{defaults.delay_task_apscheduler_jobstores_kind!r}"
        )


def check_aps_job_adder_constructor():
    sig = inspect.signature(ApsJobAdder.__init__)
    params = list(sig.parameters.keys())
    if params == ["self", "booster", "job_store_kind", "is_auto_start", "is_auto_paused"]:
        ok("ApsJobAdder.__init__ 参数列表正确")
    else:
        fail(f"ApsJobAdder.__init__ 参数不符: {params}")

    defaults = {
        "job_store_kind": sig.parameters["job_store_kind"].default,
        "is_auto_start": sig.parameters["is_auto_start"].default,
        "is_auto_paused": sig.parameters["is_auto_paused"].default,
    }
    expected = {"job_store_kind": "memory", "is_auto_start": True, "is_auto_paused": False}
    for name, expected_val in expected.items():
        if defaults[name] == expected_val:
            ok(f"ApsJobAdder.__init__ {name} 默认值={expected_val!r}")
        else:
            fail(f"ApsJobAdder.__init__ {name} 默认={defaults[name]!r}, 预期={expected_val!r}")


def check_add_push_job_signature():
    sig = inspect.signature(ApsJobAdder.add_push_job)
    param_names = list(sig.parameters.keys())
    expected = [
        "self",
        "trigger",
        "args",
        "kwargs",
        "id",
        "name",
        "misfire_grace_time",
        "coalesce",
        "max_instances",
        "next_run_time",
        "jobstore",
        "executor",
        "replace_existing",
        "trigger_args",
    ]
    if param_names == expected:
        ok("add_push_job 参数列表与源码一致")
    else:
        fail(f"add_push_job 参数不符: {param_names}")

    if sig.parameters["replace_existing"].default is False:
        ok("add_push_job replace_existing 默认值=False")
    else:
        fail(f"replace_existing 默认值错误: {sig.parameters['replace_existing'].default!r}")

    if sig.parameters["trigger"].default is None:
        ok("add_push_job trigger 默认值=None")
    else:
        fail(f"trigger 默认值错误: {sig.parameters['trigger'].default!r}")


@boost(BoosterParams(
    queue_name="verify_timing_r1_task",
    broker_kind=BrokerEnum.SQLITE_QUEUE,
    concurrent_num=3,
    qps=5,
))
def cleanup_expired_data(table_name: str):
    print(f"[OK] cleanup_expired_data table_name={table_name}")
    return table_name


@boost(BoosterParams(
    queue_name="verify_timing_r1_heartbeat",
    broker_kind=BrokerEnum.SQLITE_QUEUE,
    concurrent_num=2,
))
def heartbeat(service_name: str):
    print(f"[OK] heartbeat service_name={service_name}")


def run_skill_code_patterns():
    cleanup_expired_data.consume()

    try:
        ApsJobAdder(cleanup_expired_data, job_store_kind="sqlite")
        fail("不支持的 job_store_kind 应抛出 ValueError")
    except ValueError as e:
        if "Unsupported job_store_kind" in str(e):
            ok("不支持的 job_store_kind 抛出 ValueError('Unsupported job_store_kind')")
        else:
            fail(f"ValueError 消息不符: {e}")

    # SKILL 核心模式：默认 job_store_kind='memory' + interval
    adder_mem = ApsJobAdder(cleanup_expired_data)
    if adder_mem.job_store_kind == "memory":
        ok("ApsJobAdder(func) 默认 job_store_kind='memory'")
    else:
        fail(f"默认 job_store_kind 错误: {adder_mem.job_store_kind!r}")

    adder_mem.add_push_job(
        trigger="interval",
        seconds=30,
        kwargs={"table_name": "sessions"},
        id="cleanup_sessions",
        replace_existing=True,
    )
    ok("interval trigger + kwargs + replace_existing=True 注册成功")

    adder_mem.add_push_job(
        trigger="cron",
        hour=2,
        minute=0,
        kwargs={"table_name": "logs"},
        id="cleanup_logs_daily",
        replace_existing=True,
    )
    ok("cron trigger hour/minute + kwargs 注册成功")

    # SKILL 一次性 date 任务
    run_at = datetime.now() + timedelta(seconds=8)
    adder_mem.add_push_job(
        trigger="date",
        run_date=run_at,
        kwargs={"table_name": "once"},
        id="cleanup_once",
        replace_existing=True,
    )
    ok("date trigger + run_date=datetime 注册成功")

    # SKILL args 位置参数
    adder_mem.add_push_job(
        trigger="interval",
        seconds=10,
        args=("direct_table",),
        id="cleanup_args_job",
        replace_existing=True,
    )
    ok("args=() 位置参数注册成功")

    # SKILL 完整示例 import 路径（funboost.timing_job）
    heartbeat.consume()
    adder_subpkg = ApsJobAdderFromSubpkg(heartbeat, job_store_kind="memory")
    adder_subpkg.add_push_job(
        trigger="interval",
        seconds=5,
        kwargs={"service_name": "api-server"},
        id="api_heartbeat",
    )
    ok("from funboost.timing_job import ApsJobAdder 可用")

    cleanup_expired_data.push("manual_push")
    ok("consume + push 手动发布正常")


if __name__ == "__main__":
    print("=== 静态校验 ===")
    check_exports()
    check_booster_params_timing_fields()
    check_aps_job_adder_constructor()
    check_add_push_job_signature()

    print("\n=== SKILL 代码模式运行 ===")
    run_skill_code_patterns()

    time.sleep(10)
    print(f"\n=== 汇总: PASS={len(PASS)}, FAIL={len(FAIL)} ===")
    if FAIL:
        for item in FAIL:
            print(f"  FAIL: {item}")
        os._exit(1)
    print("[DONE] verify_timing_r1 全部通过")
    os._exit(66)
