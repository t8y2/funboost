"""round3b: funboost-broker-selection — BrokerEnum 枚举 + BrokerConnConfig 静态验证"""
import os
import sys
import time

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
_ts = int(time.time())
os.environ["PRINT_WRTIE_FILE_NAME"] = f"r3b_broker_01_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"r3b_broker_01_std_{_ts}"

PASS = True
SKILL = "funboost-broker-selection"


def report(name: str, ok: bool, detail: str = ""):
    global PASS
    if not ok:
        PASS = False
    status = "PASS" if ok else "FAIL"
    msg = f"[{status}] {name}"
    if detail:
        msg += f" — {detail}"
    print(msg)


# SKILL 文档列出的全部 BrokerEnum 名称
SKILL_BROKER_ENUMS = [
    "REDIS", "REDIS_ACK_ABLE", "REDIS_ACK_USING_TIMEOUT", "REDIS_STREAM",
    "REDIS_PRIORITY", "REDIS_BRPOP_LPUSH", "REDIS_PUBSUB", "REDIS_ZSET_PRIORITY",
    "REDIS_ZSET_DELAY",
    "RABBITMQ_AMQPSTORM", "RABBITMQ", "RABBITMQ_COMPLEX_ROUTING", "RABBITMQ_AMQP",
    "RABBITMQ_PIKA", "RABBITMQ_RABBITPY",
    "KAFKA", "KAFKA_CONFLUENT", "CONFLUENT_KAFKA", "KAFKA_CONFLUENT_SASlPlAIN",
    "ROCKETMQ", "ROCKETMQ5", "PULSAR", "NSQ", "MQTT", "NATS_CORE", "NATS_JETSTREAM",
    "ZEROMQ", "SQS", "HTTPSQS", "TCP", "UDP", "HTTP", "GRPC", "WEBSOCKET",
    "CELERY", "DRAMATIQ", "HUEY", "RQ", "NAMEKO", "KOMBU",
    "MONGOMQ", "SQLACHEMY", "POSTGRES", "PEEWEE",
    "MEMORY_QUEUE", "FASTEST_MEM_QUEUE", "SQLITE_QUEUE", "TXT_FILE",
    "MYSQL_CDC", "WATCHDOG", "EMPTY",
]

SKILL_BROKER_CONN_FIELDS = [
    "REDIS_HOST", "REDIS_PORT", "REDIS_PASSWORD", "REDIS_DB",
    "RABBITMQ_HOST", "RABBITMQ_PORT", "RABBITMQ_USER", "RABBITMQ_PASS",
    "RABBITMQ_VIRTUAL_HOST", "KAFKA_BOOTSTRAP_SERVERS",
]


if __name__ == "__main__":
    print(f"=== {SKILL} static verify ===\n")

    for name in ("boost", "BoosterParams", "BrokerEnum"):
        try:
            mod = __import__("funboost", fromlist=[name])
            getattr(mod, name)
            report(f"from funboost import {name}", True)
        except Exception as e:
            report(f"from funboost import {name}", False, str(e))

    from funboost import BoosterParams, BrokerEnum
    from funboost.funboost_config_deafult import BrokerConnConfig as DefaultBrokerConnConfig

    for enum_name in SKILL_BROKER_ENUMS:
        ok = hasattr(BrokerEnum, enum_name)
        val = getattr(BrokerEnum, enum_name, None) if ok else None
        report(f"BrokerEnum.{enum_name}", ok, "" if ok else "不存在")
        if ok and enum_name not in ("RABBITMQ", "CONFLUENT_KAFKA"):
            try:
                BoosterParams(queue_name=f"r3b_enum_{enum_name.lower()}", broker_kind=val)
                report(f"BoosterParams(broker_kind=BrokerEnum.{enum_name}) 接受", True)
            except Exception as e:
                report(f"BoosterParams(broker_kind=BrokerEnum.{enum_name}) 接受", False, str(e))

    report("BrokerEnum.RABBITMQ == RABBITMQ_AMQPSTORM", BrokerEnum.RABBITMQ == BrokerEnum.RABBITMQ_AMQPSTORM)
    report("BrokerEnum.CONFLUENT_KAFKA == KAFKA_CONFLUENT", BrokerEnum.CONFLUENT_KAFKA == BrokerEnum.KAFKA_CONFLUENT)

    try:
        from funboost.utils.simple_data_class import DataClassBase
        report("import DataClassBase", True)
    except Exception as e:
        report("import DataClassBase", False, str(e))

    for field in SKILL_BROKER_CONN_FIELDS:
        report(f"DefaultBrokerConnConfig.{field} 存在", hasattr(DefaultBrokerConnConfig, field))

    report("broker_exclusive_config 在 BoosterParams", "broker_exclusive_config" in BoosterParams.model_fields)

    try:
        BoosterParams(
            queue_name="rabbit_task_r3b",
            broker_kind=BrokerEnum.RABBITMQ_AMQPSTORM,
            broker_exclusive_config={"queue_durable": True, "no_ack": False},
        )
        report("broker_exclusive_config(queue_durable,no_ack) 实例化", True)
    except Exception as e:
        report("broker_exclusive_config(queue_durable,no_ack) 实例化", False, str(e))

    print(f"\n=== {SKILL} 最终结果: {'PASS' if PASS else 'FAIL'} ===")
    sys.stdout.flush()
    time.sleep(12)
    os._exit(66 if PASS else 1)
