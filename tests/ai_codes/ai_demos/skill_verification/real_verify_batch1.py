"""验证 batch1 三个 Skill 的代码示例能否真实运行（MEMORY_QUEUE）"""
import os
import sys
import time
import inspect
import asyncio

os.environ["PYTHONPATH"] = r"D:\codes\funboost"
os.environ["LOG_PATH"] = r"D:\pythonlogs"
os.environ["PRINT_WRTIE_FILE_NAME"] = "real_verify_batch1_print.txt"
os.environ["SYS_STD_FILE_NAME"] = "real_verify_batch1_std.txt"

from funboost import (
    boost,
    BoosterParams,
    BrokerEnum,
    ConcurrentModeEnum,
    TaskOptions,
    fct,
    enable_ctrl_c_quit_on_windows,
)
from funboost.core.func_params_model import BoosterParams as BoosterParamsModel
from pydantic import ValidationError

PASS_COUNT = 0
FAIL_COUNT = 0
EXEC_RESULTS = []
FCT_CAPTURE = {}


def ok(msg):
    global PASS_COUNT
    PASS_COUNT += 1
    print(f"[PASS] {msg}")


def fail(msg):
    global FAIL_COUNT
    FAIL_COUNT += 1
    print(f"[FAIL] {msg}")


# ========== Skill 1: using-funboost-basics ==========

def check_basics_exports():
    import funboost

    for name in (
        "boost",
        "BoosterParams",
        "BrokerEnum",
        "ConcurrentModeEnum",
        "TaskOptions",
        "fct",
        "enable_ctrl_c_quit_on_windows",
    ):
        if hasattr(funboost, name):
            ok(f"funboost 导出 {name}")
        else:
            fail(f"funboost 未导出 {name}")


def check_booster_params_model():
    fields = [
        "queue_name",
        "broker_kind",
        "concurrent_num",
        "concurrent_mode",
        "qps",
        "max_retry_times",
        "function_timeout",
        "log_level",
        "is_using_rpc_mode",
        "should_check_publish_func_params",
    ]
    model_fields = set(BoosterParamsModel.model_fields.keys())
    for field in fields:
        if field in model_fields:
            ok(f"BoosterParams.{field} 存在")
        else:
            fail(f"BoosterParams.{field} 不存在")

    try:
        BoosterParamsModel()
        fail("queue_name 应为必填但未校验")
    except ValidationError:
        ok("queue_name 为必填字段（Pydantic 校验）")

    try:
        BoosterParamsModel(queue_name="x", timeout=30)
        fail("臆造字段 timeout 应被拒绝")
    except ValidationError:
        ok("Pydantic extra=forbid 生效，臆造 timeout 被拒绝")


def check_task_options():
    for field in ("countdown", "task_id", "eta"):
        if field in TaskOptions.model_fields:
            ok(f"TaskOptions.{field} 存在")
        else:
            fail(f"TaskOptions.{field} 不存在")


@boost(
    BoosterParams(
        queue_name="real_verify_batch1_add",
        broker_kind=BrokerEnum.MEMORY_QUEUE,
        concurrent_num=5,
        qps=10,
        max_retry_times=3,
        log_level=20,
    )
)
def add_task(x: int, y: int):
    """Skill basics: 普通业务函数"""
    result = x + y
    EXEC_RESULTS.append(("add_task", result))
    print(f"[EXEC] add_task({x}, {y}) = {result}")
    return result


@boost(
    BoosterParams(
        queue_name="real_verify_batch1_publish",
        broker_kind=BrokerEnum.MEMORY_QUEUE,
        concurrent_num=3,
    )
)
def publish_demo(url: str, depth: int = 1):
    EXEC_RESULTS.append(("publish_demo", (url, depth)))
    print(f"[EXEC] publish_demo url={url}, depth={depth}")
    return depth


@boost(
    BoosterParams(
        queue_name="real_verify_batch1_fct",
        broker_kind=BrokerEnum.MEMORY_QUEUE,
        concurrent_num=2,
    )
)
def fct_demo(x):
    """Skill basics + concepts: fct 上下文"""
    FCT_CAPTURE["task_id"] = fct.task_id
    FCT_CAPTURE["queue_name"] = fct.queue_name
    FCT_CAPTURE["run_times"] = fct.function_result_status.run_times
    FCT_CAPTURE["full_msg"] = fct.full_msg
    FCT_CAPTURE["logger"] = fct.logger
    EXEC_RESULTS.append(("fct_demo", x))
    print(f"[EXEC] fct_demo x={x}, task_id={fct.task_id}")
    return x


@boost(
    BoosterParams(
        queue_name="real_verify_batch1_external",
        broker_kind=BrokerEnum.MEMORY_QUEUE,
        should_check_publish_func_params=False,
    )
)
def handle_external(**kwargs):
    EXEC_RESULTS.append(("handle_external", kwargs))
    print(f"[EXEC] handle_external kwargs={kwargs}")


@boost(
    BoosterParams(
        queue_name="real_verify_batch1_async",
        broker_kind=BrokerEnum.MEMORY_QUEUE,
        concurrent_num=2,
    )
)
def async_demo(x: int):
    result = x * 2
    EXEC_RESULTS.append(("async_demo", result))
    print(f"[EXEC] async_demo({x}) = {result}")
    return result


@boost(
    BoosterParams(
        queue_name="real_verify_batch1_direct",
        broker_kind=BrokerEnum.MEMORY_QUEUE,
        concurrent_num=1,
    )
)
def direct_call_demo(a, b=1):
    return a + b


# ========== Skill 2: funboost-broker-selection ==========

SKILL_BROKER_NAMES = [
    "REDIS",
    "REDIS_ACK_ABLE",
    "REDIS_ACK_USING_TIMEOUT",
    "REDIS_STREAM",
    "REDIS_PRIORITY",
    "REDIS_BRPOP_LPUSH",
    "REDIS_PUBSUB",
    "REDIS_ZSET_PRIORITY",
    "REDIS_ZSET_DELAY",
    "RABBITMQ_AMQPSTORM",
    "RABBITMQ",
    "RABBITMQ_COMPLEX_ROUTING",
    "RABBITMQ_AMQP",
    "RABBITMQ_PIKA",
    "RABBITMQ_RABBITPY",
    "KAFKA",
    "KAFKA_CONFLUENT",
    "CONFLUENT_KAFKA",
    "KAFKA_CONFLUENT_SASlPlAIN",
    "ROCKETMQ",
    "ROCKETMQ5",
    "PULSAR",
    "NSQ",
    "MQTT",
    "NATS_CORE",
    "NATS_JETSTREAM",
    "ZEROMQ",
    "SQS",
    "HTTPSQS",
    "TCP",
    "UDP",
    "HTTP",
    "GRPC",
    "WEBSOCKET",
    "CELERY",
    "DRAMATIQ",
    "HUEY",
    "RQ",
    "NAMEKO",
    "KOMBU",
    "MONGOMQ",
    "SQLACHEMY",
    "POSTGRES",
    "PEEWEE",
    "MEMORY_QUEUE",
    "FASTEST_MEM_QUEUE",
    "SQLITE_QUEUE",
    "TXT_FILE",
    "MYSQL_CDC",
    "WATCHDOG",
    "EMPTY",
]


def check_broker_enum():
    missing = [n for n in SKILL_BROKER_NAMES if not hasattr(BrokerEnum, n)]
    if missing:
        fail(f"BrokerEnum 缺少 SKILL 列出的名称: {missing}")
    else:
        ok(f"BrokerEnum 全部 {len(SKILL_BROKER_NAMES)} 个 SKILL 名称均存在")

    if BrokerEnum.RABBITMQ == BrokerEnum.RABBITMQ_AMQPSTORM:
        ok("BrokerEnum.RABBITMQ == RABBITMQ_AMQPSTORM 别名正确")
    else:
        fail("BrokerEnum.RABBITMQ 别名不正确")

    if BrokerEnum.KAFKA_CONFLUENT == BrokerEnum.CONFLUENT_KAFKA:
        ok("BrokerEnum.KAFKA_CONFLUENT == CONFLUENT_KAFKA 别名正确")
    else:
        fail("BrokerEnum.KAFKA_CONFLUENT 别名不正确")

    if isinstance(BrokerEnum.MEMORY_QUEUE, str):
        ok(f"BrokerEnum.MEMORY_QUEUE 值为字符串: {BrokerEnum.MEMORY_QUEUE!r}")
    else:
        fail("BrokerEnum.MEMORY_QUEUE 不是字符串")


def check_broker_conn_config():
    from funboost.funboost_config_deafult import BrokerConnConfig

    fields = [
        "REDIS_HOST",
        "REDIS_PORT",
        "REDIS_PASSWORD",
        "REDIS_DB",
        "RABBITMQ_HOST",
        "RABBITMQ_PORT",
        "RABBITMQ_USER",
        "RABBITMQ_PASS",
        "RABBITMQ_VIRTUAL_HOST",
        "KAFKA_BOOTSTRAP_SERVERS",
    ]
    missing = [f for f in fields if not hasattr(BrokerConnConfig, f)]
    if missing:
        fail(f"BrokerConnConfig 缺少字段: {missing}")
    else:
        ok(f"BrokerConnConfig 示例 {len(fields)} 个字段均存在")


def check_broker_exclusive_config():
    from funboost.core.broker_kind__exclusive_config_default_define import (
        broker_kind__exclusive_config_default_map,
    )

    defaults = broker_kind__exclusive_config_default_map.get(BrokerEnum.RABBITMQ_AMQPSTORM, {})
    for key in ("queue_durable", "no_ack"):
        if key in defaults:
            ok(f"broker_exclusive_config 键 {key!r} 对 RABBITMQ_AMQPSTORM 有效")
        else:
            fail(f"broker_exclusive_config 键 {key!r} 不在 RABBITMQ 默认配置中")


# ========== Skill 3: understanding-funboost-concepts ==========

def check_concurrent_modes():
    for name in ("THREADING", "GEVENT", "EVENTLET", "ASYNC", "SINGLE_THREAD"):
        if hasattr(ConcurrentModeEnum, name):
            ok(f"ConcurrentModeEnum.{name} 存在")
        else:
            fail(f"ConcurrentModeEnum.{name} 不存在")


def check_direct_call_vs_push():
    """concepts: func() 直接调用 vs func.push() 发队列"""
    direct_result = direct_call_demo(10, 20)
    if direct_result == 30:
        ok("直接调用 func(x, y) 同步执行，结果=30")
    else:
        fail(f"直接调用结果错误: {direct_result}")

    if hasattr(direct_call_demo, "push") and callable(direct_call_demo.push):
        ok("push() 方法存在且可调用")
    else:
        fail("push() 方法不存在或不可调用")


def check_method_signatures(booster_obj):
    pub = booster_obj.publisher
    for name in ("consume", "multi_process_consume", "mp_consume", "push", "publish"):
        if hasattr(booster_obj, name) and callable(getattr(booster_obj, name)):
            ok(f"Booster.{name} 方法存在")
        else:
            fail(f"Booster.{name} 方法不存在")

    push_sig = inspect.signature(pub.push)
    if list(push_sig.parameters.keys()) == ["func_args", "func_kwargs"]:
        ok("push(*func_args, **func_kwargs) 签名正确")
    else:
        fail(f"push 签名不符: {push_sig}")


async def run_async_publish():
    r1 = await async_demo.aio_push(5)
    ok(f"aio_push 返回 task_id={r1.task_id[:8]}...")
    r2 = await async_demo.aio_publish({"x": 7}, task_options=TaskOptions(countdown=0))
    ok(f"aio_publish 返回 task_id={r2.task_id[:8]}...")


def run_runtime_verification():
    """实际 push / consume / 验证函数执行"""
    # push 业务参数
    add_task.push(10, 20)
    ok("add_task.push(10, 20) 发布成功")

    publish_demo.push("https://example.com", depth=3)
    ok("publish_demo.push(url, depth=...) 发布成功")

    publish_demo.publish(
        {"url": "https://example.com", "depth": 3},
        task_options=TaskOptions(countdown=0, task_id="custom-id-batch1"),
    )
    ok("publish + TaskOptions(countdown, task_id) 发布成功")

    fct_demo.push("ctx_value")
    ok("fct_demo.push 发布成功")

    handle_external.push(name="from_java", value=99)
    ok("handle_external(**kwargs) push 发布成功")

    async_demo.push(3)
    asyncio.run(run_async_publish())

    # 启动消费
    add_task.consume()
    publish_demo.consume()
    fct_demo.consume()
    handle_external.consume()
    async_demo.consume()
    ok("多个 consume() 顺序启动成功")

    if callable(enable_ctrl_c_quit_on_windows):
        ok("enable_ctrl_c_quit_on_windows 可调用")
    else:
        fail("enable_ctrl_c_quit_on_windows 不可调用")

    # 等待消费完成
    time.sleep(8)

    # 验证执行结果
    add_done = any(name == "add_task" and val == 30 for name, val in EXEC_RESULTS)
    if add_done:
        ok("任务函数 add_task 被执行，结果=30")
    else:
        fail(f"add_task 未被执行，EXEC_RESULTS={EXEC_RESULTS}")

    pub_done = any(name == "publish_demo" for name, _ in EXEC_RESULTS)
    if pub_done:
        ok("publish_demo 任务被消费执行")
    else:
        fail("publish_demo 未被消费执行")

    fct_done = any(name == "fct_demo" for name, _ in EXEC_RESULTS)
    if fct_done:
        ok("fct_demo 任务被消费执行")
    else:
        fail("fct_demo 未被消费执行")

    if FCT_CAPTURE.get("task_id"):
        ok(f"fct.task_id 可访问: {FCT_CAPTURE['task_id'][:8]}...")
    else:
        fail("fct.task_id 未能访问")

    if FCT_CAPTURE.get("queue_name") == "real_verify_batch1_fct":
        ok(f"fct.queue_name 正确: {FCT_CAPTURE['queue_name']}")
    else:
        fail(f"fct.queue_name 错误: {FCT_CAPTURE.get('queue_name')}")

    if FCT_CAPTURE.get("run_times") is not None and FCT_CAPTURE["run_times"] >= 1:
        ok(f"fct.function_result_status.run_times={FCT_CAPTURE['run_times']}")
    else:
        fail("fct.function_result_status.run_times 未能访问")

    if FCT_CAPTURE.get("full_msg") is not None:
        ok(f"fct.full_msg 可访问，类型={type(FCT_CAPTURE['full_msg']).__name__}")
    else:
        fail("fct.full_msg 未能访问")

    if FCT_CAPTURE.get("logger") is not None:
        ok("fct.logger 可访问")
    else:
        fail("fct.logger 未能访问")

    ext_done = any(name == "handle_external" for name, _ in EXEC_RESULTS)
    if ext_done:
        ok("handle_external(**kwargs) 被消费执行")
    else:
        fail("handle_external 未被消费执行")

    async_exec = sum(1 for name, _ in EXEC_RESULTS if name == "async_demo")
    if async_exec >= 3:
        ok(f"async_demo 被消费 {async_exec} 次（push + aio_push + aio_publish）")
    else:
        fail(f"async_demo 消费次数不足: {async_exec}/3, EXEC_RESULTS={EXEC_RESULTS}")


if __name__ == "__main__":
    print("=== real_verify_batch1: 静态校验 ===")
    check_basics_exports()
    check_booster_params_model()
    check_task_options()
    check_broker_enum()
    check_broker_conn_config()
    check_broker_exclusive_config()
    check_concurrent_modes()
    check_direct_call_vs_push()
    check_method_signatures(add_task)

    print("\n=== real_verify_batch1: 运行时验证 ===")
    run_runtime_verification()

    print(f"\n=== 汇总: PASS={PASS_COUNT}, FAIL={FAIL_COUNT} ===")
    time.sleep(15)
    os._exit(66)
