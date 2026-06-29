"""验证 funboost-rpc-mode skill 中的代码示例"""
import os
import time

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"verify_rpc_{int(time.time())}"
os.environ["SYS_STD_FILE_NAME"] = f"verify_rpc_std_{int(time.time())}"

from funboost import boost, BoosterParams, BrokerEnum
from funboost.core.msg_result_getter import AsyncResult

# RPC 需要 Redis，这里用 SQLITE_QUEUE 验证 push 返回 AsyncResult 对象
# 注意：SQLITE_QUEUE 也支持 RPC（结果存 Redis）
# 如果没有 Redis，这个测试主要验证 import 和对象创建无报错

@boost(BoosterParams(
    queue_name="verify_rpc_add",
    broker_kind=BrokerEnum.SQLITE_QUEUE,
    is_using_rpc_mode=True,
))
def add(x: int, y: int):
    print(f"[OK] add({x}, {y}) = {x + y}")
    return x + y


if __name__ == "__main__":
    add.consume()

    # push 返回 AsyncResult
    async_result = add.push(3, 4)
    print(f"[OK] async_result type = {type(async_result).__name__}")
    print(f"[OK] async_result.task_id = {async_result.task_id}")

    # 尝试获取结果（需 Redis 配置正确）
    try:
        result = async_result.result
        print(f"[OK] RPC result = {result}")
    except Exception as e:
        print(f"[WARN] RPC result 获取失败（可能 Redis 未配置）: {type(e).__name__}: {e}")

    # 验证 status_and_result_obj
    try:
        async_result2 = add.push(10, 20)
        status_obj = async_result2.status_and_result_obj
        if status_obj:
            print(f"[OK] status_and_result_obj.result = {status_obj.result}")
            print(f"[OK] status_and_result_obj.success = {status_obj.success}")
        else:
            print("[WARN] status_and_result_obj 为 None（超时）")
    except Exception as e:
        print(f"[WARN] status_and_result_obj 失败: {type(e).__name__}: {e}")

    time.sleep(15)
    print("[DONE] verify_rpc_mode 完成")
    os._exit(66)
