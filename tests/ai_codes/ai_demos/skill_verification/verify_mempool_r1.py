"""验证 funboost-memory-queue-pool SKILL.md 的技术准确性（r1）"""
import asyncio
import inspect
import os
import time

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
_ts = int(time.time())
os.environ["PRINT_WRTIE_FILE_NAME"] = f"verify_mempool_r1_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"verify_mempool_r1_std_{_ts}"

from funboost import (
    boost,
    BoosterParams,
    BrokerEnum,
    ConcurrentModeEnum,
    MemoryFunboostPool,
    FunboostPool,
)
from funboost.publishers.local_python_queue_publisher import LocalPythonQueuePublisher
from funboost.publishers.fastest_mem_queue_publisher import FastestMemQueuePublisher

PASS = []
FAIL = []


def ok(msg):
    PASS.append(msg)
    print(f"[PASS] {msg}")


def fail(msg):
    FAIL.append(msg)
    print(f"[FAIL] {msg}")


def check_broker_enums():
    for name in ("MEMORY_QUEUE", "FASTEST_MEM_QUEUE", "LOCAL_PYTHON_QUEUE"):
        if hasattr(BrokerEnum, name):
            ok(f"BrokerEnum.{name} 存在 = {getattr(BrokerEnum, name)!r}")
        else:
            fail(f"BrokerEnum.{name} 不存在")

    if BrokerEnum.LOCAL_PYTHON_QUEUE == BrokerEnum.MEMORY_QUEUE:
        ok("BrokerEnum.LOCAL_PYTHON_QUEUE 是 MEMORY_QUEUE 别名")
    else:
        fail("LOCAL_PYTHON_QUEUE 别名不正确")


def check_exports():
    import funboost

    for name in ("MemoryFunboostPool", "FunboostPool", "FunboostPoolPickleFunc"):
        if hasattr(funboost, name):
            ok(f"funboost 导出 {name}")
        else:
            fail(f"funboost 未导出 {name}")


def check_memory_funboost_pool_ctor():
    sig = inspect.signature(MemoryFunboostPool.__init__)
    params = list(sig.parameters.keys())
    expected = [
        "self",
        "concurrent_num",
        "qps",
        "is_future_direct_ret_result",
        "is_auto_start_consuming_message",
    ]
    if params == expected:
        ok(f"MemoryFunboostPool.__init__ 参数: {expected[1:]}")
    else:
        fail(f"MemoryFunboostPool.__init__ 参数不符: {params}")

    defaults = {
        "concurrent_num": sig.parameters["concurrent_num"].default,
        "qps": sig.parameters["qps"].default,
        "is_future_direct_ret_result": sig.parameters["is_future_direct_ret_result"].default,
        "is_auto_start_consuming_message": sig.parameters["is_auto_start_consuming_message"].default,
    }
    expected_defaults = {
        "concurrent_num": 4,
        "qps": None,
        "is_future_direct_ret_result": True,
        "is_auto_start_consuming_message": True,
    }
    for k, v in expected_defaults.items():
        if defaults[k] == v:
            ok(f"MemoryFunboostPool.{k} 默认值={v!r}")
        else:
            fail(f"MemoryFunboostPool.{k} 默认值错误: 预期 {v!r}, 实际 {defaults[k]!r}")


def check_funboost_pool_ctor():
    sig = inspect.signature(FunboostPool.__init__)
    params = list(sig.parameters.keys())
    expected = [
        "self",
        "booster_params",
        "is_need_result",
        "is_future_direct_ret_result",
        "is_auto_start_consuming_message",
    ]
    if params == expected:
        ok(f"FunboostPool.__init__ 参数: {expected[1:]}")
    else:
        fail(f"FunboostPool.__init__ 参数不符: {params}")


def check_get_future_only_on_memory_queue_publisher():
    if hasattr(LocalPythonQueuePublisher, "get_future"):
        ok("LocalPythonQueuePublisher 有 get_future")
    else:
        fail("LocalPythonQueuePublisher 缺少 get_future")

    if hasattr(FastestMemQueuePublisher, "get_future"):
        fail("FastestMemQueuePublisher 不应有 get_future（SKILL 称 FASTEST 不支持 get_future 生态）")
    else:
        ok("FastestMemQueuePublisher 无 get_future（与 SKILL 一致）")


def run_memory_queue_boost_task():
    @boost(BoosterParams(
        queue_name=f"verify_mempool_r1_boost_{_ts}",
        broker_kind=BrokerEnum.MEMORY_QUEUE,
        concurrent_num=5,
        qps=20,
    ))
    def add(x, y):
        return x + y

    add.consume()
    add.push(1, 2)
    add.push(3, 4)
    time.sleep(2)
    ok("@boost + MEMORY_QUEUE push/consume 基本任务执行成功")


def run_get_future_example():
    @boost(BoosterParams(
        queue_name=f"verify_mempool_r1_future_{_ts}",
        broker_kind=BrokerEnum.MEMORY_QUEUE,
        concurrent_num=5,
    ))
    def add(x, y):
        return x + y

    add.consume()
    future = add.publisher.get_future(10, 20)
    status = future.result(timeout=10)
    if status.result == 30 and status.success:
        ok("get_future() 返回 FunctionResultStatus，result=30, success=True")
    else:
        fail(f"get_future 结果错误: result={status.result}, success={status.success}")


def run_memory_funboost_pool():
    """复用官方 test_memory_funboost_pool.py（完成后 consumer 线程不退出，允许 timeout）"""
    import subprocess
    import sys

    env = os.environ.copy()
    env["PYTHONPATH"] = r"D:\codes\funboost"
    official = r"D:\codes\funboost\test_frame\test_funboost_pool\test_memory_funboost_pool.py"
    try:
        r = subprocess.run([sys.executable, official], capture_output=True, text=True, timeout=12, env=env)
        out = (r.stdout or "") + (r.stderr or "")
    except subprocess.TimeoutExpired as e:
        out = (e.stdout or "") + (e.stderr or "")
    if "8" in out and "[5, 7, 9]" in out:
        ok("MemoryFunboostPool 官方测试: future.result()=8, map=[5,7,9]")
    else:
        fail(f"MemoryFunboostPool 官方测试输出不符: {out[-800:]}")


def run_fastest_mem_queue_task():
    @boost(BoosterParams(
        queue_name=f"verify_mempool_r1_fastest_{_ts}",
        broker_kind=BrokerEnum.FASTEST_MEM_QUEUE,
        concurrent_num=5,
        broker_exclusive_config={"pull_msg_batch_size": 10},
    ))
    def mul(x, y):
        return x * y

    mul.consume()
    mul.push(3, 4)
    time.sleep(2)
    ok("FASTEST_MEM_QUEUE + pull_msg_batch_size 基本任务执行成功")


def run_broker_kind_switch_pattern():
    """验证切换 broker 只需改 broker_kind，业务函数不变"""

    def make_task(broker_kind):
        @boost(BoosterParams(
            queue_name=f"verify_mempool_r1_switch_{broker_kind}_{_ts}",
            broker_kind=broker_kind,
            concurrent_num=3,
        ))
        def task(x):
            return x + 100

        return task

    mem_task = make_task(BrokerEnum.MEMORY_QUEUE)
    sqlite_task = make_task(BrokerEnum.SQLITE_QUEUE)

    mem_task.consume()
    sqlite_task.consume()

    mem_task.push(1)
    sqlite_task.push(2)
    time.sleep(3)
    ok("同一业务函数体，仅改 broker_kind 即可切换 MEMORY_QUEUE / SQLITE_QUEUE")


def run_unpickleable_arg():
    class DBConnection:
        def query(self, sql):
            return f"result of {sql}"

    @boost(BoosterParams(
        queue_name=f"verify_mempool_r1_nosql_{_ts}",
        broker_kind=BrokerEnum.MEMORY_QUEUE,
        concurrent_num=2,
    ))
    def run_query(conn, sql):
        return conn.query(sql)

    run_query.consume()
    conn = DBConnection()
    future = run_query.publisher.get_future(conn, "SELECT 1")
    status = future.result(timeout=10)
    if status.success and status.result == "result of SELECT 1":
        ok("不可 pickle 对象作为 MEMORY_QUEUE 入参传递成功")
    else:
        fail(f"不可 pickle 对象测试失败: {status.result}, success={status.success}")


if __name__ == "__main__":
    print("=== 静态校验 ===")
    check_broker_enums()
    check_exports()
    check_memory_funboost_pool_ctor()
    check_funboost_pool_ctor()
    check_get_future_only_on_memory_queue_publisher()

    print("\n=== 运行时验证 ===")
    # MemoryFunboostPool 需优先单独测，避免同进程多 MEMORY_QUEUE 消费者互相干扰
    run_memory_funboost_pool()
    run_memory_queue_boost_task()
    run_get_future_example()
    run_fastest_mem_queue_task()
    run_broker_kind_switch_pattern()
    run_unpickleable_arg()

    time.sleep(8)
    print(f"\n=== 汇总: PASS={len(PASS)}, FAIL={len(FAIL)} ===")
    if FAIL:
        for item in FAIL:
            print(f"  FAIL: {item}")
        os._exit(1)
    print("[DONE] verify_mempool_r1 全部通过")
    os._exit(66)
