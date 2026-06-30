"""验证 developing-funboost-broker SKILL.md 的技术准确性（r1）"""
import abc
import inspect
import json
import os
import sys
import time
from collections import deque
from threading import Lock

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
_ts = int(time.time())
os.environ["PRINT_WRTIE_FILE_NAME"] = f"verify_broker_ext_r1_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"verify_broker_ext_r1_std_{_ts}"

PASS = []
FAIL = []
WARN = []

# SKILL.md 声明的抽象方法集合
SKILL_PUBLISHER_ABSTRACT = {"_publish_impl", "clear", "get_message_count", "close"}
SKILL_CONSUMER_ABSTRACT = {"_dispatch_task", "_confirm_consume", "_requeue"}


def ok(msg):
    PASS.append(msg)
    print(f"[PASS] {msg}")


def fail(msg):
    FAIL.append(msg)
    print(f"[FAIL] {msg}")


def warn(msg):
    WARN.append(msg)
    print(f"[WARN] {msg}")


def check_register_custom_broker_import_and_signature():
    """SKILL: from funboost import register_custom_broker"""
    from funboost import register_custom_broker
    from funboost.factories.broker_kind__publsiher_consumer_type_map import (
        register_custom_broker as register_from_factory,
    )

    ok("register_custom_broker 可从 funboost 顶层导入")

    sig = inspect.signature(register_custom_broker)
    params = list(sig.parameters.keys())
    expected = ["broker_kind", "publisher_class", "consumer_class"]
    if params == expected:
        ok(f"register_custom_broker 参数名正确: {params}")
    else:
        fail(f"register_custom_broker 参数名错误: 期望 {expected}, 实际 {params}")

    if register_custom_broker is register_from_factory:
        ok("funboost.__init__ 导出的是工厂模块同一函数对象")
    else:
        warn("funboost.__init__ 与工厂模块的 register_custom_broker 不是同一对象（可能做了包装）")


def check_abstract_publisher_methods():
    from funboost.publishers.base_publisher import AbstractPublisher

    abstract_methods = set()
    for name, method in inspect.getmembers(AbstractPublisher, predicate=inspect.isfunction):
        if getattr(method, "__isabstractmethod__", False):
            abstract_methods.add(name)

    if abstract_methods == SKILL_PUBLISHER_ABSTRACT:
        ok(f"AbstractPublisher 抽象方法: {sorted(abstract_methods)}")
    else:
        missing = SKILL_PUBLISHER_ABSTRACT - abstract_methods
        extra = abstract_methods - SKILL_PUBLISHER_ABSTRACT
        if missing:
            fail(f"SKILL 列出但源码不是抽象方法: {missing}")
        if extra:
            fail(f"源码有额外抽象方法 SKILL 未列出: {extra}")

    # _publish_impl 签名
    sig = inspect.signature(AbstractPublisher._publish_impl)
    param_names = list(sig.parameters.keys())
    if param_names == ["self", "msg"]:
        ok("AbstractPublisher._publish_impl(self, msg) 签名正确")
    else:
        fail(f"_publish_impl 签名异常: {param_names}")

    ann = AbstractPublisher._publish_impl.__annotations__.get("msg")
    if ann is str:
        ok("_publish_impl 类型注解 msg: str")
    else:
        warn(f"_publish_impl msg 类型注解为 {ann!r}，SKILL 写 JSON 字符串")


def check_abstract_consumer_methods_and_submit_task():
    from funboost.consumers.base_consumer import AbstractConsumer

    abstract_methods = set()
    for name, method in inspect.getmembers(AbstractConsumer, predicate=inspect.isfunction):
        if getattr(method, "__isabstractmethod__", False):
            abstract_methods.add(name)

    if abstract_methods == SKILL_CONSUMER_ABSTRACT:
        ok(f"AbstractConsumer 抽象方法: {sorted(abstract_methods)}")
    else:
        missing = SKILL_CONSUMER_ABSTRACT - abstract_methods
        extra = abstract_methods - SKILL_CONSUMER_ABSTRACT
        if missing:
            fail(f"SKILL 列出但源码不是抽象方法: {missing}")
        if extra:
            fail(f"源码有额外抽象方法 SKILL 未列出: {extra}")

    if hasattr(AbstractConsumer, "_submit_task") and callable(AbstractConsumer._submit_task):
        ok("AbstractConsumer._submit_task 方法存在")
    else:
        fail("AbstractConsumer._submit_task 不存在")

    sig = inspect.signature(AbstractConsumer._submit_task)
    params = list(sig.parameters.keys())
    if params == ["self", "kw"]:
        ok("AbstractConsumer._submit_task(self, kw) 签名正确")
    else:
        fail(f"_submit_task 签名异常: {params}")

    # 源码 _submit_task 首行使用 kw['body']
    src = inspect.getsource(AbstractConsumer._submit_task)
    if "kw['body']" in src or 'kw["body"]' in src:
        ok("_submit_task 内部读取 kw['body']（与 SKILL kw 字典结构一致）")
    else:
        fail("_submit_task 源码中未找到 kw['body'] 访问")

    for method_name in ("_confirm_consume", "_requeue"):
        sig = inspect.signature(getattr(AbstractConsumer, method_name))
        if list(sig.parameters.keys()) == ["self", "kw"]:
            ok(f"AbstractConsumer.{method_name}(self, kw) 签名正确")
        else:
            fail(f"{method_name} 签名异常: {list(sig.parameters.keys())}")


def check_publish_impl_msg_type_behavior():
    """核对 _publish_impl 实际收到的 msg 类型：非内存队列是 JSON 字符串，内存队列可能是 dict"""
    from funboost.constant import BrokerEnum
    from funboost.publishers.base_publisher import AbstractPublisher, PublishMsgContext

    src_execute = inspect.getsource(AbstractPublisher._execute_publish)
    if "_wrapped_publish_impl(publish_msg_context.msg_json)" in src_execute:
        ok("_execute_publish 将 publish_msg_context.msg_json 传给 _publish_impl")
    else:
        fail("_execute_publish 传参方式与 SKILL 描述不一致")

    gen_src = inspect.getsource(AbstractPublisher.generate_msg_context_for_publish)
    if "_is_memory_queue" in gen_src and "msg_json = msg_dict" in gen_src.replace(" ", ""):
        warn(
            "内存队列(MEMORY_QUEUE/FASTEST_MEM_QUEUE) 时 _publish_impl 收到 dict 而非 JSON 字符串；"
            "SKILL 仅强调 JSON 字符串，未说明内存队列例外"
        )
    else:
        ok("generate_msg_context_for_publish 对非内存队列序列化为 JSON 字符串")


def check_dispatch_task_two_modes():
    """核对 _dispatch_task 两种模式：框架 keep_circulating 包装 vs 自循环"""
    from funboost.consumers.base_consumer import AbstractConsumer, ConcurrentModeDispatcher

    sched_src = inspect.getsource(ConcurrentModeDispatcher.schedulal_task_with_no_block)
    if "keep_circulating" in sched_src and "_dispatch_task" in sched_src:
        ok("框架通过 keep_circulating 重复调用 _dispatch_task（模式 B 支持）")
    else:
        fail("未找到 keep_circulating 包装 _dispatch_task 的逻辑")

    start_src = inspect.getsource(AbstractConsumer.start_consuming_message)
    if "schedule_tasks_on_main_thread" in start_src:
        ok("start_consuming_message 支持 schedule_tasks_on_main_thread 分支")
    else:
        warn("start_consuming_message 中未找到 schedule_tasks_on_main_thread")


def check_kw_body_type_after_submit():
    """核对 _submit_task 会将 kw['body'] 转为 dict（SKILL 说传入时必须是字符串）"""
    from funboost.consumers.base_consumer import AbstractConsumer

    src = inspect.getsource(AbstractConsumer._submit_task)
    if "_convert_msg_before_run(kw['body'])" in src or '_convert_msg_before_run(kw["body"])' in src:
        ok("_submit_task 调用 _convert_msg_before_run 处理 body")
    else:
        fail("_submit_task 未调用 _convert_msg_before_run")

    convert_src = inspect.getsource(AbstractConsumer._convert_msg_before_run)
    if "Serialization.to_dict(msg)" in convert_src:
        warn(
            "_convert_msg_before_run 接受 str 或 dict；"
            "传给 _submit_task 的 body 推荐 JSON 字符串，但 dict 也可被框架接受"
        )


def check_super_rules_and_exports():
    from funboost import AbstractPublisher, AbstractConsumer, register_broker_exclusive_config_default

    ok("funboost 导出 AbstractPublisher / AbstractConsumer")
    ok("funboost 导出 register_broker_exclusive_config_default（SKILL broker_exclusive_config 节）")


# ---------- 集成：用内存 deque 模拟自定义 broker ----------
_BROKER_KIND = "SKILL_VERIFY_MEM_BROKER_R1"
_STORE = {}
_STORE_LOCK = Lock()


def _get_queue(name):
    with _STORE_LOCK:
        if name not in _STORE:
            _STORE[name] = deque()
        return _STORE[name]


def run_custom_broker_integration():
    from funboost import boost, BoosterParams, register_custom_broker
    from funboost.publishers.base_publisher import AbstractPublisher
    from funboost.consumers.base_consumer import AbstractConsumer

    received = {"values": [], "publish_msg_types": []}

    class MemPublisher(AbstractPublisher):
        def _publish_impl(self, msg):
            received["publish_msg_types"].append(type(msg).__name__)
            _get_queue(self.queue_name).append(msg)

        def clear(self):
            _get_queue(self.queue_name).clear()

        def get_message_count(self):
            return len(_get_queue(self.queue_name))

        def close(self):
            pass

    class MemConsumer(AbstractConsumer):
        def _dispatch_task(self):
            q = _get_queue(self.queue_name)
            if q:
                body = q.popleft()
                self._submit_task({"body": body})

        def _confirm_consume(self, kw):
            pass

        def _requeue(self, kw):
            from funboost.core.serialization import Serialization

            body = kw["body"]
            if isinstance(body, dict):
                body = Serialization.to_json_str(body)
            _get_queue(self.queue_name).append(body)

    register_custom_broker(_BROKER_KIND, MemPublisher, MemConsumer)

    @boost(
        BoosterParams(
            queue_name=f"skill_verify_broker_ext_{_ts}",
            broker_kind=_BROKER_KIND,
            concurrent_num=1,
            is_auto_start_consuming_message=False,
            is_send_consumer_heartbeat_to_redis=False,
            create_logger_file=False,
        )
    )
    def add_one(x):
        received["values"].append(x)
        return x + 1

    add_one.push(10)
    add_one.push(20)
    if add_one.publisher.get_message_count() == 2:
        ok("自定义 broker 发布成功，get_message_count=2")
    else:
        fail(f"发布后队列深度异常: {add_one.publisher.get_message_count()}")

    if received["publish_msg_types"] and all(t == "str" for t in received["publish_msg_types"]):
        ok("自定义 broker _publish_impl 收到 str 类型（JSON 字符串）")
    else:
        warn(f"_publish_impl 收到类型: {received['publish_msg_types']}")

    add_one.consume()
    time.sleep(8)
    if received["values"] == [10, 20]:
        ok("自定义 broker 消费成功: values=[10, 20]")
    else:
        fail(f"消费结果异常: {received['values']!r}")


def main():
    print("=" * 60)
    print("developing-funboost-broker SKILL.md 验证报告 (r1)")
    print("=" * 60)

    check_register_custom_broker_import_and_signature()
    check_abstract_publisher_methods()
    check_abstract_consumer_methods_and_submit_task()
    check_publish_impl_msg_type_behavior()
    check_dispatch_task_two_modes()
    check_kw_body_type_after_submit()
    check_super_rules_and_exports()
    run_custom_broker_integration()

    print("\n" + "=" * 60)
    print(f"PASS: {len(PASS)}  FAIL: {len(FAIL)}  WARN: {len(WARN)}")
    print("OVERALL:", "FAIL" if FAIL else "PASS")
    print("=" * 60)

    time.sleep(1)
    os._exit(66 if FAIL else 0)


if __name__ == "__main__":
    main()
