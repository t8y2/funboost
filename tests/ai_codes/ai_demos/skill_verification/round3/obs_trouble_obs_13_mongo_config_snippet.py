"""验证 round3 / funboost-observability SKILL §5 BrokerConnConfig MONGO_CONNECT_URL 配置片段"""
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"obs_trouble_obs_13_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"obs_trouble_obs_13_std_{_ts}"

from funboost_config import BrokerConnConfig

# SKILL 示例：class BrokerConnConfig(DataClassBase): MONGO_CONNECT_URL = '...'
assert hasattr(BrokerConnConfig, 'MONGO_CONNECT_URL'), "BrokerConnConfig 缺少 MONGO_CONNECT_URL"
mongo_url = BrokerConnConfig.MONGO_CONNECT_URL
print(f"[OK] MONGO_CONNECT_URL = {mongo_url!r}")

if __name__ == "__main__":
    time.sleep(15)
    os._exit(66)
