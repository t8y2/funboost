"""验证 funboost-memory-queue-pool SKILL.md（r2-05）

覆盖：
1. MemoryFunboostPool 基本用法
2. get_future 获取结果
3. 不可 pickle 对象入参
"""
import inspect
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"verify_all_r2_05_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"verify_all_r2_05_std_{_ts}"

from funboost import (
    boost,
    BoosterParams,
    BrokerEnum,
    MemoryFunboostPool,
)

PASS = []
FAIL = []


def ok(msg):
    PASS.append(msg)
    print(f"[PASS] {msg}")


def fail(msg):
    FAIL.append(msg)
    print(f"[FAIL] {msg}")


def check_skill_vs_tutorial_api():
    """SKILL 与 c4.md 教程 API 差异：以源码为准"""
    sig = inspect.signature(MemoryFunboostPool.__init__)
    params = list(sig.parameters.keys())
    if "queue_name" not in params:
        ok("MemoryFunboostPool 无 queue_name 参数（SKILL 正确，c4.md 4.38.1 示例过时）")
    else:
        fail("MemoryFunboostPool 存在 queue_name 参数，与 SKILL 描述不符")

    expected = ["self", "concurrent_num", "qps", "is_future_direct_ret_result", "is_auto_start_consuming_message"]
    if params == expected:
        ok(f"MemoryFunboostPool 构造参数与 SKILL 一致: {expected[1:]}")
    else:
        fail(f"MemoryFunboostPool 构造参数不符: {params}")


def test_memory_funboost_pool_basic():
    """MemoryFunboostPool 基本用法：submit + future.result()"""

    def add(a, b):
        return a + b

    with MemoryFunboostPool(concurrent_num=5, qps=20) as pool:
        fut = pool.submit(add, 5, 3)
        result = fut.result(timeout=10)
        if result == 8:
            ok("MemoryFunboostPool.submit + future.result() = 8")
        else:
            fail(f"MemoryFunboostPool 结果错误: {result!r}")

        mapped = list(pool.map(add, [1, 2, 3], [4, 5, 6]))
        if mapped == [5, 7, 9]:
            ok("MemoryFunboostPool.map = [5, 7, 9]")
        else:
            fail(f"MemoryFunboostPool.map 结果错误: {mapped}")


def test_get_future():
    """@boost + MEMORY_QUEUE 使用 get_future 获取 FunctionResultStatus"""

    @boost(BoosterParams(
        queue_name=f"verify_r2_05_future_{_ts}",
        broker_kind=BrokerEnum.MEMORY_QUEUE,
        concurrent_num=5,
    ))
    def add(x, y):
        return x + y

    add.consume()
    future = add.publisher.get_future(10, 20)
    status = future.result(timeout=10)
    if status.result == 30 and status.success:
        ok("get_future() 返回 FunctionResultStatus: result=30, success=True")
    else:
        fail(f"get_future 结果错误: result={status.result}, success={status.success}")


def test_unpickleable_arg():
    """不可 pickle 对象作为 MEMORY_QUEUE 入参（c3.md / SKILL 示例 D）"""

    class DBConnection:
        def query(self, sql):
            return f"result of {sql}"

    @boost(BoosterParams(
        queue_name=f"verify_r2_05_nosql_{_ts}",
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
        fail(f"不可 pickle 对象测试失败: result={status.result}, success={status.success}")


if __name__ == "__main__":
    print("=== SKILL vs 教程 API 静态校验 ===")
    check_skill_vs_tutorial_api()

    print("\n=== 运行时验证 ===")
    test_memory_funboost_pool_basic()
    test_get_future()
    test_unpickleable_arg()

    print(f"\n=== 汇总: PASS={len(PASS)}, FAIL={len(FAIL)} ===")
    if FAIL:
        for item in FAIL:
            print(f"  FAIL: {item}")
        os._exit(1)
    print("[DONE] verify_all_r2_05 全部通过")
    os._exit(66)
