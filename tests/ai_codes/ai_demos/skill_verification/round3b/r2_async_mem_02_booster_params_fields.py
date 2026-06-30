"""round3b: 验证 specify_async_loop / is_auto_start_specify_async_loop_in_child_thread 存在于 BoosterParams"""
import asyncio
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"r2_async_mem_02_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"r2_async_mem_02_std_{_ts}"

from funboost import BoosterParams, BrokerEnum, ConcurrentModeEnum

fields = BoosterParams.model_fields
assert "specify_async_loop" in fields, "missing specify_async_loop"
assert "is_auto_start_specify_async_loop_in_child_thread" in fields, (
    "missing is_auto_start_specify_async_loop_in_child_thread"
)

loop = asyncio.new_event_loop()
params = BoosterParams(
    queue_name=f"r2_bp_fields_{_ts}",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    concurrent_mode=ConcurrentModeEnum.ASYNC,
    specify_async_loop=loop,
    is_auto_start_specify_async_loop_in_child_thread=False,
)
assert params.specify_async_loop is loop
assert params.is_auto_start_specify_async_loop_in_child_thread is False

print("[PASS] BoosterParams.specify_async_loop exists and accepts loop")
print("[PASS] BoosterParams.is_auto_start_specify_async_loop_in_child_thread exists")

time.sleep(15)
os._exit(66)
