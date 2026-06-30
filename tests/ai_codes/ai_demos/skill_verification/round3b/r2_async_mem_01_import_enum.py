"""round3b: 验证 ConcurrentModeEnum.ASYNC 拼写与 import 路径"""
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"r2_async_mem_01_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"r2_async_mem_01_std_{_ts}"

# skill 推荐路径
from funboost import ConcurrentModeEnum as CM_from_funboost
from funboost.constant import ConcurrentModeEnum as CM_from_constant

assert CM_from_funboost is CM_from_constant
assert hasattr(CM_from_funboost, "ASYNC")
assert CM_from_funboost.ASYNC == "async"
assert CM_from_funboost.THREADING == "threading"

print(f"[PASS] ConcurrentModeEnum.ASYNC={CM_from_funboost.ASYNC!r}")
print(f"[PASS] import from funboost and funboost.constant both OK")

time.sleep(15)
os._exit(66)
