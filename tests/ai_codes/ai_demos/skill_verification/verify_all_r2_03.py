"""Round2-03: 验证 funboost-broker-selection SKILL.md（BrokerEnum + MEMORY_QUEUE SSS 描述 vs c3 教程）"""
import inspect
import os
import sys
import time
from pathlib import Path

PROJECT_ROOT = r"D:\codes\funboost"
SKILL_PATH = Path(PROJECT_ROOT) / ".agents" / "skills" / "funboost-broker-selection" / "SKILL.md"
C3_PATH = Path(r"D:\codes\funboost_docs\source\articles\c3.md")

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"verify_all_r2_03_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"verify_all_r2_03_std_{_ts}"

PASS = []
FAIL = []
WARN = []

# SKILL.md「所有 Broker 枚举」章节列出的名称（含别名）
SKILL_BROKER_NAMES = [
    "REDIS", "REDIS_ACK_ABLE", "REDIS_ACK_USING_TIMEOUT", "REDIS_STREAM",
    "REDIS_PRIORITY", "REDIS_BRPOP_LPUSH", "REDIS_PUBSUB",
    "REDIS_ZSET_PRIORITY", "REDIS_ZSET_DELAY",
    "RABBITMQ_AMQPSTORM", "RABBITMQ", "RABBITMQ_COMPLEX_ROUTING",
    "RABBITMQ_AMQP", "RABBITMQ_PIKA", "RABBITMQ_RABBITPY",
    "KAFKA", "KAFKA_CONFLUENT", "CONFLUENT_KAFKA", "KAFKA_CONFLUENT_SASlPlAIN",
    "ROCKETMQ", "ROCKETMQ5", "PULSAR", "NSQ", "MQTT",
    "NATS_CORE", "NATS_JETSTREAM", "ZEROMQ", "SQS", "HTTPSQS",
    "TCP", "UDP", "HTTP", "GRPC", "WEBSOCKET",
    "CELERY", "DRAMATIQ", "HUEY", "RQ", "NAMEKO", "KOMBU",
    "MONGOMQ", "SQLACHEMY", "POSTGRES", "PEEWEE",
    "MEMORY_QUEUE", "FASTEST_MEM_QUEUE", "SQLITE_QUEUE", "TXT_FILE",
    "MYSQL_CDC", "WATCHDOG", "EMPTY",
]

# MEMORY_QUEUE SSS 描述：SKILL 与 c3/constant 应对齐的核心技术点
MEMORY_QUEUE_CLAIMS = [
    {
        "id": "sss_level",
        "label": "SSS 级核心 broker 定位",
        "skill_keywords": ["SSS", "超级装饰器"],
        "c3_keywords": ["sss级", "sss级broker", "最最最核心"],
        "constant_keywords": ["sss级", "最最最核心"],
    },
    {
        "id": "zero_serialization",
        "label": "零序列化 / 不序列化",
        "skill_keywords": ["零序列化", "不进行序列化"],
        "c3_keywords": ["不进行序列化和反序列化", "零序列化"],
        "constant_keywords": ["不进行序列化和反序列化"],
    },
    {
        "id": "unpickleable_args",
        "label": "支持不可 pickle 对象入参",
        "skill_keywords": ["不可 pickle", "不可pickle"],
        "c3_keywords": ["不可pickle序列化", "不可json序列化"],
        "constant_keywords": ["不可pickle序列化", "不可json序列化"],
    },
    {
        "id": "no_middleware",
        "label": "零中间件依赖",
        "skill_keywords": ["零中间件", "不需要 Redis"],
        "c3_keywords": ["queue.Queue", "没有socket io"],
        "constant_keywords": ["queue.Queue", "没有socket io"],
    },
    {
        "id": "qps_retry_timeout",
        "label": "QPS / 重试 / 超时能力",
        "skill_keywords": ["QPS", "重试", "超时"],
        "c3_keywords": ["qps", "重试", "超时杀死"],
        "constant_keywords": ["qps", "重试", "超时杀死"],
    },
    {
        "id": "threadpool_alternative",
        "label": "替代 ThreadPoolExecutor / 线程池场景",
        "skill_keywords": ["ThreadPoolExecutor", "线程池"],
        "c3_keywords": ["ThreadpoolExecutor", "线程池", "tomorrow"],
        "constant_keywords": ["ThreadpoolExecutor", "tomorrow"],
    },
    {
        "id": "get_future",
        "label": "get_future 结果获取（不依赖 Redis RPC）",
        "skill_keywords": ["get_future"],
        "c3_keywords": ["get_future", "get_aio_future"],
        "constant_keywords": ["get_future", "get_aio_future"],
    },
    {
        "id": "no_cross_process",
        "label": "不支持跨进程/跨机器/持久化",
        "skill_keywords": ["跨进程", "跨机器", "重启丢失", "持久化"],
        "c3_keywords": ["不支持跨进程", "跨脚本", "跨机器", "不支持持久化"],
        "constant_keywords": ["不支持跨进程", "跨脚本", "跨机器", "不支持持久化"],
    },
    {
        "id": "super_decorator",
        "label": "超级装饰器（一个 @boost 抵多个装饰器）",
        "skill_keywords": ["超级装饰器", "完美替代"],
        "c3_keywords": ["超级装饰器", "抵得上10个常规装饰器"],
        "constant_keywords": ["超级装饰器", "抵得上10个常规装饰器"],
    },
]


def ok(msg):
    PASS.append(msg)
    print(f"[PASS] {msg}")


def fail(msg):
    FAIL.append(msg)
    print(f"[FAIL] {msg}")


def warn(msg):
    WARN.append(msg)
    print(f"[WARN] {msg}")


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _contains_any(text: str, keywords: list) -> tuple:
    lowered = text.lower()
    for kw in keywords:
        if kw.lower() in lowered:
            return True, kw
    return False, None


def verify_skill_files_exist():
    if SKILL_PATH.is_file():
        ok(f"SKILL.md 存在: {SKILL_PATH}")
    else:
        fail(f"SKILL.md 不存在: {SKILL_PATH}")
    if C3_PATH.is_file():
        ok(f"c3.md 教程存在: {C3_PATH}")
    else:
        fail(f"c3.md 不存在: {C3_PATH}")


def verify_broker_enum_in_skill():
    from funboost.constant import BrokerEnum

    missing = [n for n in SKILL_BROKER_NAMES if not hasattr(BrokerEnum, n)]
    if missing:
        fail(f"SKILL 列出的 BrokerEnum 在源码中缺失: {missing}")
    else:
        ok(f"SKILL 列出的 {len(SKILL_BROKER_NAMES)} 个 BrokerEnum 名称均存在于 constant.py")

    all_attrs = {
        k: v for k, v in vars(BrokerEnum).items()
        if not k.startswith("_") and isinstance(v, str)
    }
    value_to_first = {}
    primary_names = set()
    for name, val in all_attrs.items():
        if val not in value_to_first:
            value_to_first[val] = name
            primary_names.add(name)

    skill_primary = {n for n in SKILL_BROKER_NAMES if n in primary_names}
    not_in_skill = sorted(primary_names - skill_primary)
    if not_in_skill:
        warn(f"源码主 broker 未在 SKILL 列出（多为别名）: {not_in_skill}")
    else:
        ok(f"SKILL 已覆盖全部 {len(primary_names)} 种主 broker")

    # 别名一致性抽查
    alias_checks = [
        ("RABBITMQ", "RABBITMQ_AMQPSTORM"),
        ("CONFLUENT_KAFKA", "KAFKA_CONFLUENT"),
        ("REDIS_ACK_USING_TIMEOUT", "REIDS_ACK_USING_TIMEOUT"),
    ]
    for alias, primary in alias_checks:
        if hasattr(BrokerEnum, alias) and hasattr(BrokerEnum, primary):
            if getattr(BrokerEnum, alias) == getattr(BrokerEnum, primary):
                ok(f"别名 {alias} == {primary}")
            else:
                fail(f"别名不一致: {alias} != {primary}")


def verify_memory_queue_sss_vs_c3():
    skill_text = _read_text(SKILL_PATH)
    c3_text = _read_text(C3_PATH)

    # constant.py MEMORY_QUEUE 区块 docstring
    from funboost.constant import BrokerEnum

    constant_src = inspect.getsource(BrokerEnum)
    mq_block_start = constant_src.find('"""')
    mq_doc = constant_src[mq_block_start:constant_src.find("MEMORY_QUEUE =")]

    for claim in MEMORY_QUEUE_CLAIMS:
        skill_ok, skill_kw = _contains_any(skill_text, claim["skill_keywords"])
        c3_ok, c3_kw = _contains_any(c3_text, claim["c3_keywords"])
        const_ok, const_kw = _contains_any(mq_doc, claim["constant_keywords"])

        if skill_ok and c3_ok and const_ok:
            ok(
                f"{claim['label']}: SKILL({skill_kw}) / c3({c3_kw}) / constant({const_kw}) 一致"
            )
        else:
            parts = []
            if not skill_ok:
                parts.append(f"SKILL 缺 {claim['skill_keywords']}")
            if not c3_ok:
                parts.append(f"c3 缺 {claim['c3_keywords']}")
            if not const_ok:
                parts.append(f"constant 缺 {claim['constant_keywords']}")
            fail(f"{claim['label']} 未三方对齐: {'; '.join(parts)}")

    # c3 强调但 SKILL 简化的点 — 仅 WARN，不算 FAIL
    c3_extra = [
        ("get_aio_future", "get_aio_future", ["get_aio_future"]),
        ("微批处理", "微批", ["微批"]),
        ("celery 对比", "celery", ["celery", "六等公民"]),
    ]
    for label, _, kws in c3_extra:
        _, c3_kw = _contains_any(c3_text, kws)
        skill_has, _ = _contains_any(skill_text, kws)
        if c3_kw and not skill_has:
            warn(f"c3 有「{label}」({c3_kw})，SKILL 未展开（可接受简化）")


def verify_memory_queue_runtime():
    """运行时：零序列化 + get_future + QPS 基本能力"""
    from funboost import boost, BoosterParams, BrokerEnum

    class _UnpickleableConn:
        def ping(self):
            return "pong"

    @boost(BoosterParams(
        queue_name=f"verify_all_r2_03_mq_{_ts}",
        broker_kind=BrokerEnum.MEMORY_QUEUE,
        concurrent_num=3,
        qps=50,
        max_retry_times=2,
        function_timeout=5,
    ))
    def echo_conn(conn, msg):
        return f"{conn.ping()}:{msg}"

    echo_conn.consume()
    conn = _UnpickleableConn()
    future = echo_conn.publisher.get_future(conn, "hi")
    status = future.result(timeout=10)
    if status.success and status.result == "pong:hi":
        ok("MEMORY_QUEUE 运行时: 不可 pickle 对象 + get_future() 成功")
    else:
        fail(f"MEMORY_QUEUE 运行时失败: success={status.success}, result={status.result!r}")

    if hasattr(echo_conn.publisher, "get_aio_future"):
        ok("MEMORY_QUEUE publisher 提供 get_aio_future（c3 提及，SKILL 可补充）")
    else:
        warn("publisher 无 get_aio_future 方法（需确认 c3 描述是否仍准确）")


def verify_broker_map_registration():
    from funboost.constant import BrokerEnum
    from funboost.factories.broker_kind__publsiher_consumer_type_map import (
        broker_kind__publsiher_consumer_type_map,
        regist_to_funboost,
    )

    tested = set()
    unregistered = []
    for name in SKILL_BROKER_NAMES:
        if not hasattr(BrokerEnum, name):
            continue
        val = getattr(BrokerEnum, name)
        if val in tested:
            continue
        tested.add(val)
        if val not in broker_kind__publsiher_consumer_type_map:
            try:
                regist_to_funboost(val)
            except Exception as e:
                unregistered.append(f"{name}({val}): {e}")
                continue
        if val not in broker_kind__publsiher_consumer_type_map:
            unregistered.append(f"{name}({val}): not in map")

    if unregistered:
        fail(f"未注册到映射表的 broker: {unregistered}")
    else:
        ok(f"SKILL 列出的 {len(tested)} 种 broker 均可注册到映射表")


def main():
    print("=" * 60)
    print("verify_all_r2_03 — funboost-broker-selection SKILL 验证")
    print("=" * 60)

    verify_skill_files_exist()
    verify_broker_enum_in_skill()
    verify_memory_queue_sss_vs_c3()
    verify_broker_map_registration()
    verify_memory_queue_runtime()

    print("\n" + "=" * 60)
    print(f"汇总: PASS={len(PASS)}, FAIL={len(FAIL)}, WARN={len(WARN)}")
    if WARN:
        for w in WARN:
            print(f"  [WARN] {w}")
    if FAIL:
        for f in FAIL:
            print(f"  [FAIL] {f}")
        print("OVERALL: FAIL")
        print("=" * 60)
        return 1

    print("OVERALL: PASS")
    print("=" * 60)
    time.sleep(2)
    os._exit(66)


if __name__ == "__main__":
    sys.exit(main())
