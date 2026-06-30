"""验证 funboost-broker-selection SKILL.md 的技术准确性（静态核对，不启动消费）"""
import os
import sys

# SKILL.md 中列出的所有 BrokerEnum 名称（含别名）
SKILL_BROKER_NAMES = [
    # Redis 家族
    "REDIS", "REDIS_ACK_ABLE", "REDIS_ACK_USING_TIMEOUT", "REDIS_STREAM",
    "REDIS_PRIORITY", "REDIS_BRPOP_LPUSH", "REDIS_PUBSUB",
    "REDIS_ZSET_PRIORITY", "REDIS_ZSET_DELAY",
    # RabbitMQ 家族
    "RABBITMQ_AMQPSTORM", "RABBITMQ", "RABBITMQ_COMPLEX_ROUTING",
    "RABBITMQ_AMQP", "RABBITMQ_PIKA", "RABBITMQ_RABBITPY",
    # Kafka 家族
    "KAFKA", "KAFKA_CONFLUENT", "CONFLUENT_KAFKA", "KAFKA_CONFLUENT_SASlPlAIN",
    # 其他
    "ROCKETMQ", "ROCKETMQ5", "PULSAR", "NSQ", "MQTT",
    "NATS_CORE", "NATS_JETSTREAM", "ZEROMQ", "SQS", "HTTPSQS",
    "TCP", "UDP", "HTTP", "GRPC", "WEBSOCKET",
    "CELERY", "DRAMATIQ", "HUEY", "RQ", "NAMEKO", "KOMBU",
    "MONGOMQ", "SQLACHEMY", "POSTGRES", "PEEWEE",
    "MEMORY_QUEUE", "FASTEST_MEM_QUEUE", "SQLITE_QUEUE", "TXT_FILE",
    "MYSQL_CDC", "WATCHDOG", "EMPTY",
]

# SKILL.md 配置示例中引用的 BrokerConnConfig 字段
SKILL_BROKER_CONN_FIELDS = [
    "REDIS_HOST", "REDIS_PORT", "REDIS_PASSWORD", "REDIS_DB",
    "RABBITMQ_HOST", "RABBITMQ_PORT", "RABBITMQ_USER", "RABBITMQ_PASS",
    "RABBITMQ_VIRTUAL_HOST", "KAFKA_BOOTSTRAP_SERVERS",
]

# SKILL.md 提到的 SASL 配置字段（含源码拼写）
SKILL_SASL_CONFIG_FIELD = "KFFKA_SASL_CONFIG"

# SKILL.md broker_exclusive_config 示例键名
SKILL_EXCLUSIVE_CONFIG_KEYS = ["queue_durable", "no_ack"]
SKILL_EXCLUSIVE_BROKER = "RABBITMQ_AMQPSTORM"


def verify_broker_enum():
    from funboost.constant import BrokerEnum

    missing = []
    alias_mismatch = []
    for name in SKILL_BROKER_NAMES:
        if not hasattr(BrokerEnum, name):
            missing.append(name)
            continue
        val = getattr(BrokerEnum, name)
        if not isinstance(val, str):
            alias_mismatch.append(f"{name} is not str: {type(val)}")

    # 收集源码中所有 broker 枚举名（排除别名：值与其他属性相同的）
    all_attrs = {k: v for k, v in vars(BrokerEnum).items()
                 if not k.startswith("_") and isinstance(v, str)}
    value_to_first_name = {}
    primary_names = set()
    for name, val in all_attrs.items():
        if val not in value_to_first_name:
            value_to_first_name[val] = name
            primary_names.add(name)

    skill_primary = {n for n in SKILL_BROKER_NAMES if n in primary_names}
    not_in_skill = sorted(primary_names - skill_primary)

    return {
        "missing": missing,
        "alias_mismatch": alias_mismatch,
        "not_in_skill": not_in_skill,
        "total_primary_brokers": len(primary_names),
    }


def verify_broker_conn_config():
    from funboost.funboost_config_deafult import BrokerConnConfig

    missing_fields = []
    for field in SKILL_BROKER_CONN_FIELDS:
        if not hasattr(BrokerConnConfig, field):
            missing_fields.append(field)

    sasl_ok = hasattr(BrokerConnConfig, SKILL_SASL_CONFIG_FIELD)

    return {
        "missing_fields": missing_fields,
        "sasl_config_exists": sasl_ok,
        "all_config_fields_count": len([
            k for k in dir(BrokerConnConfig)
            if k.isupper() and not k.startswith("_")
        ]),
    }


def verify_broker_exclusive_config():
    from funboost.constant import BrokerEnum
    from funboost.core.broker_kind__exclusive_config_default_define import (
        broker_kind__exclusive_config_default_map,
        generate_broker_exclusive_config,
    )
    from funboost.core.loggers import flogger

    broker_kind = getattr(BrokerEnum, SKILL_EXCLUSIVE_BROKER)
    defaults = broker_kind__exclusive_config_default_map.get(broker_kind, {})
    missing_keys = [k for k in SKILL_EXCLUSIVE_CONFIG_KEYS if k not in defaults]

    merged = generate_broker_exclusive_config(
        broker_kind,
        {"queue_durable": True, "no_ack": False},
        flogger,
    )
    merge_ok = all(k in merged for k in SKILL_EXCLUSIVE_CONFIG_KEYS)

    return {
        "broker": SKILL_EXCLUSIVE_BROKER,
        "defaults_keys": sorted(defaults.keys()),
        "missing_keys_in_defaults": missing_keys,
        "merge_ok": merge_ok,
    }


def verify_broker_map_registration():
    """核对 SKILL 列出的 broker 是否能在映射表或 regist_to_funboost 中注册"""
    from funboost.constant import BrokerEnum
    from funboost.factories.broker_kind__publsiher_consumer_type_map import (
        broker_kind__publsiher_consumer_type_map,
        regist_to_funboost,
    )

    # 去重：别名与主名同值，只测主名
    tested = set()
    unregistered = []
    for name in SKILL_BROKER_NAMES:
        if not hasattr(BrokerEnum, name):
            continue
        val = getattr(BrokerEnum, name)
        if val in tested:
            continue
        tested.add(val)
        bk = val
        if bk not in broker_kind__publsiher_consumer_type_map:
            try:
                regist_to_funboost(bk)
            except Exception as e:
                unregistered.append(f"{name}({bk}): regist failed: {e}")
                continue
        if bk not in broker_kind__publsiher_consumer_type_map:
            unregistered.append(f"{name}({bk}): not in map after regist")

    return {"unregistered": unregistered, "tested_count": len(tested)}


def verify_config_loading_mechanism():
    import inspect
    from funboost import set_frame_config

    src = inspect.getsource(set_frame_config.use_config_form_funboost_config_module)
    checks = {
        "uses_importlib_import_module": "importlib.import_module('funboost_config')" in src,
        "uses_BrokerConnConfig_update": "BrokerConnConfig.update_cls_attribute" in src,
        "mentions_sys_path_script_dir": "sys.path[0]" in src,
        "mentions_sys_path_project_root": "sys.path[1]" in src,
        "auto_create_on_missing": "_auto_creat_config_file_to_project_root_path" in src,
    }
    return checks


def main():
    print("=" * 60)
    print("funboost-broker-selection SKILL.md 验证报告")
    print("=" * 60)

    r1 = verify_broker_enum()
    print("\n[1] BrokerEnum 核对")
    if r1["missing"]:
        print(f"  ❌ SKILL 中不存在于源码: {r1['missing']}")
    else:
        print(f"  ✅ SKILL 列出的 {len(SKILL_BROKER_NAMES)} 个名称均存在于 BrokerEnum")
    if r1["not_in_skill"]:
        print(f"  ⚠️  源码中有但 SKILL 未列出: {r1['not_in_skill']}")
    print(f"  ℹ️  源码主 broker 种类数: {r1['total_primary_brokers']}")

    r2 = verify_broker_conn_config()
    print("\n[2] BrokerConnConfig 字段核对")
    if r2["missing_fields"]:
        print(f"  ❌ SKILL 示例字段不存在: {r2['missing_fields']}")
    else:
        print(f"  ✅ SKILL 示例中 {len(SKILL_BROKER_CONN_FIELDS)} 个字段均存在")
    if r2["sasl_config_exists"]:
        print(f"  ✅ {SKILL_SASL_CONFIG_FIELD} 存在（源码拼写一致）")
    else:
        print(f"  ❌ {SKILL_SASL_CONFIG_FIELD} 不存在")

    r3 = verify_broker_exclusive_config()
    print("\n[3] broker_exclusive_config 核对")
    if r3["missing_keys_in_defaults"]:
        print(f"  ❌ 示例键名不在默认配置: {r3['missing_keys_in_defaults']}")
    else:
        print(f"  ✅ queue_durable / no_ack 均为 {SKILL_EXCLUSIVE_BROKER} 有效键")
        print(f"     完整默认键: {r3['defaults_keys']}")

    r4 = verify_broker_map_registration()
    print("\n[4] broker 映射注册核对")
    if r4["unregistered"]:
        for u in r4["unregistered"]:
            print(f"  ❌ {u}")
    else:
        print(f"  ✅ SKILL 列出的 {r4['tested_count']} 种 broker 均可注册到映射表")

    r5 = verify_config_loading_mechanism()
    print("\n[5] 配置加载机制核对")
    for k, v in r5.items():
        mark = "✅" if v else "❌"
        print(f"  {mark} {k}: {v}")

    failed = (
        bool(r1["missing"])
        or bool(r2["missing_fields"])
        or not r2["sasl_config_exists"]
        or bool(r3["missing_keys_in_defaults"])
        or bool(r4["unregistered"])
    )
    print("\n" + "=" * 60)
    print("OVERALL:", "FAIL" if failed else "PASS")
    print("=" * 60)
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
