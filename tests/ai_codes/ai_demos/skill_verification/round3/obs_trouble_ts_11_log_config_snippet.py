"""验证 round3 / funboost-troubleshooting SKILL §5.3 FunboostCommonConfig 减少启动刷屏配置片段"""
import os
import time
import logging

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"obs_trouble_ts_11_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"obs_trouble_ts_11_std_{_ts}"

from funboost_config import FunboostCommonConfig

# SKILL 示例字段应存在于 FunboostCommonConfig
assert hasattr(FunboostCommonConfig, 'SHOW_HOW_FUNBOOST_CONFIG_SETTINGS')
assert hasattr(FunboostCommonConfig, 'FUNBOOST_PROMPT_LOG_LEVEL')
assert hasattr(FunboostCommonConfig, 'KEEPALIVETIMETHREAD_LOG_LEVEL')
print(f"[OK] SHOW_HOW_FUNBOOST_CONFIG_SETTINGS={FunboostCommonConfig.SHOW_HOW_FUNBOOST_CONFIG_SETTINGS}")
print(f"[OK] FUNBOOST_PROMPT_LOG_LEVEL={FunboostCommonConfig.FUNBOOST_PROMPT_LOG_LEVEL}")

if __name__ == "__main__":
    time.sleep(15)
    os._exit(66)
