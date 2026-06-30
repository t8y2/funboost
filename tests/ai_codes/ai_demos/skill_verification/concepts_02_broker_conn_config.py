"""验证 understanding-funboost-concepts: BrokerConnConfig 配置类示例"""
import os
import time

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
_ts = int(time.time())
os.environ["PRINT_WRTIE_FILE_NAME"] = f"concepts_02_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"concepts_02_std_{_ts}"

from funboost.utils.simple_data_class import DataClassBase


class BrokerConnConfig(DataClassBase):
    REDIS_HOST = '127.0.0.1'
    REDIS_PORT = 6379
    REDIS_PASSWORD = 'your_password'
    REDIS_DB = 7


if __name__ == "__main__":
    assert BrokerConnConfig.REDIS_HOST == '127.0.0.1'
    assert BrokerConnConfig.REDIS_PORT == 6379
    assert BrokerConnConfig.REDIS_PASSWORD == 'your_password'
    assert BrokerConnConfig.REDIS_DB == 7
    print("[OK] BrokerConnConfig 示例类定义与属性访问正常")
    time.sleep(15)
    os._exit(66)
