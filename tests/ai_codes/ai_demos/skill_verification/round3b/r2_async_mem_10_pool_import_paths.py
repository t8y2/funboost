"""round3b: 验证 MemoryFunboostPool / FunboostPool / get_future / get_aio_future import 路径"""
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"r2_async_mem_10_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"r2_async_mem_10_std_{_ts}"

from funboost import MemoryFunboostPool, FunboostPool, boost, BoosterParams, BrokerEnum
from funboost.publishers.local_python_queue_publisher import LocalPythonQueuePublisher

assert MemoryFunboostPool.__module__ == "funboost.core.funboost_pool"
assert FunboostPool.__module__ == "funboost.core.funboost_pool"
assert hasattr(MemoryFunboostPool, "submit")
assert hasattr(FunboostPool, "submit")

# publisher API on MEMORY_QUEUE
@boost(BoosterParams(queue_name=f"r2_import_{_ts}", broker_kind=BrokerEnum.MEMORY_QUEUE))
def dummy(x):
    return x


assert hasattr(LocalPythonQueuePublisher, "get_future")
assert hasattr(LocalPythonQueuePublisher, "get_aio_future")
assert hasattr(dummy.publisher, "get_future")
assert hasattr(dummy.publisher, "get_aio_future")

print("[PASS] MemoryFunboostPool/FunboostPool from funboost import OK")
print("[PASS] publisher.get_future / get_aio_future exist on MEMORY_QUEUE")
time.sleep(15)
os._exit(66)
