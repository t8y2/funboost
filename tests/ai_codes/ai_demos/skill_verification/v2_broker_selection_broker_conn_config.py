"""验证 funboost-broker-selection SKILL.md — Broker 连接配置示例"""
import os
import sys
import time

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
_ts = int(time.time())
os.environ["PRINT_WRTIE_FILE_NAME"] = f"v2_broker_conn_config_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"v2_broker_conn_config_std_{_ts}"

PASS = True


def report(name: str, ok: bool, detail: str = ""):
    global PASS
    if not ok:
        PASS = False
    status = "PASS" if ok else "FAIL"
    msg = f"[{status}] {name}"
    if detail:
        msg += f" — {detail}"
    print(msg)


try:
    from funboost.utils.simple_data_class import DataClassBase
    report("import DataClassBase", True)
except Exception as e:
    report("import DataClassBase", False, str(e))
    time.sleep(15)
    os._exit(66)


# SKILL.md 中的 funboost_config.py 配置片段
class BrokerConnConfig(DataClassBase):
    REDIS_HOST = "127.0.0.1"
    REDIS_PORT = 6379
    REDIS_PASSWORD = ""
    REDIS_DB = 7

    RABBITMQ_HOST = "127.0.0.1"
    RABBITMQ_PORT = 5672
    RABBITMQ_USER = "rabbitmq_user"
    RABBITMQ_PASS = "rabbitmq_pass"
    RABBITMQ_VIRTUAL_HOST = "/"

    KAFKA_BOOTSTRAP_SERVERS = ["127.0.0.1:9092"]


if __name__ == "__main__":
    skill_fields = [
        "REDIS_HOST", "REDIS_PORT", "REDIS_PASSWORD", "REDIS_DB",
        "RABBITMQ_HOST", "RABBITMQ_PORT", "RABBITMQ_USER", "RABBITMQ_PASS",
        "RABBITMQ_VIRTUAL_HOST", "KAFKA_BOOTSTRAP_SERVERS",
    ]
    for field in skill_fields:
        ok = hasattr(BrokerConnConfig, field)
        report(f"BrokerConnConfig.{field} 存在", ok)

    report(
        "BrokerConnConfig 继承 DataClassBase",
        issubclass(BrokerConnConfig, DataClassBase),
    )
    report(
        "KAFKA_BOOTSTRAP_SERVERS 类型正确",
        isinstance(BrokerConnConfig.KAFKA_BOOTSTRAP_SERVERS, list),
    )

    try:
        from funboost.funboost_config_deafult import BrokerConnConfig as DefaultConfig
        report("框架默认 BrokerConnConfig 可 import", True)
        report(
            "框架默认配置含 REDIS_HOST",
            hasattr(DefaultConfig, "REDIS_HOST"),
        )
    except Exception as e:
        report("框架默认 BrokerConnConfig 可 import", False, str(e))

    print(f"\n=== 最终结果: {'PASS' if PASS else 'FAIL'} ===")
    sys.stdout.flush()
    time.sleep(15)
    os._exit(66)
