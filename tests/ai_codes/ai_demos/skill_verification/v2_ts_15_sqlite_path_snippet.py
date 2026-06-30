"""验证 funboost-troubleshooting SKILL §6.5 BrokerConnConfig SQLLITE_QUEUES_PATH 配置片段"""
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"v2_ts_15_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"v2_ts_15_std_{_ts}"

from funboost_config import BrokerConnConfig

assert hasattr(BrokerConnConfig, 'SQLLITE_QUEUES_PATH'), "BrokerConnConfig 缺少 SQLLITE_QUEUES_PATH"
path = BrokerConnConfig.SQLLITE_QUEUES_PATH
print(f"[OK] SQLLITE_QUEUES_PATH = {path!r}")

if __name__ == "__main__":
    time.sleep(15)
    os._exit(66)
