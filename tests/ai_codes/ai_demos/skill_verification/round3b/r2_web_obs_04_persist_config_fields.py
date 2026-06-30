"""round3b / funboost-observability §5 FunctionResultStatusPersistanceConfig 导入路径与字段"""
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"r2_web_obs_04_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"r2_web_obs_04_std_{_ts}"

from funboost import FunctionResultStatusPersistanceConfig
from pydantic import ValidationError

expected_fields = {
    "is_save_status": False,
    "is_save_result": False,
    "expire_seconds": 7 * 24 * 3600,
    "is_use_bulk_insert": False,
    "table_name": None,
}

cfg = FunctionResultStatusPersistanceConfig()
for field, default in expected_fields.items():
    assert hasattr(cfg, field), f"missing field {field}"
    assert getattr(cfg, field) == default, f"{field} default mismatch"

cfg2 = FunctionResultStatusPersistanceConfig(
    is_save_status=True,
    is_save_result=True,
    expire_seconds=17 * 24 * 3600,
    table_name="my_project_all_tasks",
    is_use_bulk_insert=True,
)
assert cfg2.table_name == "my_project_all_tasks"

try:
    FunctionResultStatusPersistanceConfig(is_save_status=False, is_save_result=True)
    raise AssertionError("expected ValueError when is_save_result without is_save_status")
except ValueError:
    pass

print("[PASS] FunctionResultStatusPersistanceConfig from funboost, fields & validation ok")

if __name__ == "__main__":
    time.sleep(12)
    os._exit(66)
