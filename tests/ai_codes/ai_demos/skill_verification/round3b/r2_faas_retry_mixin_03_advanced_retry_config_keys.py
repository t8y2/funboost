"""round3b r2: funboost-advanced-retry — advanced_retry_config 字典键名与源码一致性"""
import inspect
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"r2_retry_cfg_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"r2_retry_cfg_std_{_ts}"

EXAMPLE = "advanced-retry / advanced_retry_config keys"
PASS = True

SKILL_KEYS = {
    "retry_mode": "sleep",
    "retry_base_interval": 1.0,
    "retry_multiplier": 2.0,
    "retry_max_interval": 60.0,
    "retry_jitter": False,
}


def report(ok: bool, msg: str):
    global PASS
    if not ok:
        PASS = False
    tag = "PASS" if ok else "FAIL"
    print(f"[{tag}] {EXAMPLE}: {msg}")


try:
    from funboost import BoosterParams
    from funboost.consumers.base_consumer import AbstractConsumer

    cfg = BoosterParams(queue_name="__r2_cfg__").advanced_retry_config
    report(isinstance(cfg, dict), f"BoosterParams.advanced_retry_config 是 dict, keys={list(cfg.keys())}")

    for key, expected_default in SKILL_KEYS.items():
        if key not in cfg:
            report(False, f"源码缺少键 {key!r}")
        elif cfg[key] != expected_default:
            report(False, f"键 {key!r} 默认值不符: 预期 {expected_default!r}, 实际 {cfg[key]!r}")
        else:
            report(True, f"键 {key!r} 存在且默认值={expected_default!r}")

    # base_consumer._init_advanced_retry_config 读取的键
    init_src = inspect.getsource(AbstractConsumer._init_advanced_retry_config)
    for key in SKILL_KEYS:
        needle = f"cfg['{key}']"
        report(needle in init_src, f"_init_advanced_retry_config 读取 cfg['{key}']")

    # 自定义配置可写入
    custom = BoosterParams(
        queue_name="__custom__",
        is_using_advanced_retry=True,
        advanced_retry_config={
            "retry_mode": "requeue",
            "retry_base_interval": 2.0,
            "retry_multiplier": 3.0,
            "retry_max_interval": 60.0,
            "retry_jitter": True,
        },
    )
    for key in SKILL_KEYS:
        report(key in custom.advanced_retry_config, f"BoosterParams 可设置 advanced_retry_config[{key!r}]")

    # retry_mode 合法值校验存在于源码
    report("'sleep'" in init_src and "'requeue'" in init_src, "源码支持 retry_mode='sleep'/'requeue'")

except Exception as e:
    report(False, f"异常: {type(e).__name__}: {e}")

if __name__ == "__main__":
    time.sleep(15)
    print(f"\n=== 最终结果: {'PASS' if PASS else 'FAIL'} ===")
    os._exit(66 if PASS else 1)
