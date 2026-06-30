"""验证 batch4 三个 Skill 的代码示例能否真实运行（MEMORY_QUEUE）"""
import os
import sys
import time
import inspect
from collections import deque
from threading import Lock

os.environ["PYTHONPATH"] = r"D:\codes\funboost"
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = "real_verify_batch4_print.txt"
os.environ["SYS_STD_FILE_NAME"] = "real_verify_batch4_std.txt"

from funboost import (
    boost,
    BoosterParams,
    BrokerEnum,
    MemoryFunboostPool,
    register_custom_broker,
)
from funboost.publishers.base_publisher import AbstractPublisher
from funboost.consumers.base_consumer import AbstractConsumer

PASS_COUNT = 0
FAIL_COUNT = 0

# ---------- 共享状态 ----------
_MIXIN_HOOK_CALLS = []
_BROKER_STORE = {}
_BROKER_STORE_LOCK = Lock()
_BROKER_KIND = "REAL_VERIFY_BATCH4_CUSTOM_BROKER"
_TS = int(time.time())


def ok(msg):
    global PASS_COUNT
    PASS_COUNT += 1
    print(f"[PASS] {msg}")


def fail(msg):
    global FAIL_COUNT
    FAIL_COUNT += 1
    print(f"[FAIL] {msg}")


def _get_broker_queue(name):
    with _BROKER_STORE_LOCK:
        if name not in _BROKER_STORE:
            _BROKER_STORE[name] = deque()
        return _BROKER_STORE[name]


# ========== Skill 1: funboost-memory-queue-pool ==========


def verify_memory_funboost_pool():
    """MemoryFunboostPool: 创建、submit、future.result() 获取结果"""

    def pool_add(x, y):
        return x + y

    try:
        with MemoryFunboostPool(concurrent_num=3, qps=20) as pool:
            ok("MemoryFunboostPool 创建成功（with 上下文）")
            future = pool.submit(pool_add, 10, 20)
            result = future.result(timeout=10)
            if result == 30:
                ok(f"MemoryFunboostPool.submit + future.result() 正确: {result}")
            else:
                fail(f"MemoryFunboostPool 结果错误: 期望 30, 实际 {result!r}")
        ok("MemoryFunboostPool with 上下文退出成功")
    except Exception as e:
        fail(f"MemoryFunboostPool 运行失败: {e}")


@boost(
    BoosterParams(
        queue_name=f"real_verify_batch4_get_future_{_TS}",
        broker_kind=BrokerEnum.MEMORY_QUEUE,
        concurrent_num=5,
        is_auto_start_consuming_message=False,
        create_logger_file=False,
    )
)
def get_future_add(x, y):
    return x + y


def verify_get_future():
    """@boost + publisher.get_future() 获取 FunctionResultStatus"""
    get_future_add.consume()
    ok("get_future 任务 consume() 启动成功")

    try:
        future = get_future_add.publisher.get_future(3, 4)
        status = future.result(timeout=10)
        if status.success and status.result == 7:
            ok(f"get_future() 正确: result={status.result}, success={status.success}")
        else:
            fail(f"get_future() 结果异常: result={status.result}, success={status.success}")
    except Exception as e:
        fail(f"get_future() 失败: {e}")


# ========== Skill 2: developing-funboost-broker ==========

SKILL_PUBLISHER_ABSTRACT = {"_publish_impl", "clear", "get_message_count", "close"}
SKILL_CONSUMER_ABSTRACT = {"_dispatch_task", "_confirm_consume", "_requeue"}


def check_register_custom_broker_api():
    sig = inspect.signature(register_custom_broker)
    params = list(sig.parameters.keys())
    if params == ["broker_kind", "publisher_class", "consumer_class"]:
        ok(f"register_custom_broker 参数正确: {params}")
    else:
        fail(f"register_custom_broker 参数错误: {params}")


def check_abstract_methods():
    pub_abstract = {
        name
        for name, m in inspect.getmembers(AbstractPublisher, predicate=inspect.isfunction)
        if getattr(m, "__isabstractmethod__", False)
    }
    if pub_abstract == SKILL_PUBLISHER_ABSTRACT:
        ok(f"AbstractPublisher 抽象方法: {sorted(pub_abstract)}")
    else:
        fail(f"AbstractPublisher 抽象方法不符: {pub_abstract}")

    con_abstract = {
        name
        for name, m in inspect.getmembers(AbstractConsumer, predicate=inspect.isfunction)
        if getattr(m, "__isabstractmethod__", False)
    }
    if con_abstract == SKILL_CONSUMER_ABSTRACT:
        ok(f"AbstractConsumer 抽象方法: {sorted(con_abstract)}")
    else:
        fail(f"AbstractConsumer 抽象方法不符: {con_abstract}")

    src = inspect.getsource(AbstractConsumer._submit_task)
    if "kw['body']" in src or 'kw["body"]' in src:
        ok("_submit_task 接收 kw['body'] 格式")
    else:
        fail("_submit_task 源码未找到 kw['body']")


class Batch4MemPublisher(AbstractPublisher):
    def _publish_impl(self, msg):
        self._last_msg_type = type(msg).__name__
        _get_broker_queue(self.queue_name).append(msg)

    def clear(self):
        _get_broker_queue(self.queue_name).clear()

    def get_message_count(self):
        return len(_get_broker_queue(self.queue_name))

    def close(self):
        pass


class Batch4MemConsumer(AbstractConsumer):
    def _dispatch_task(self):
        q = _get_broker_queue(self.queue_name)
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
        _get_broker_queue(self.queue_name).append(body)


_BROKER_RECEIVED = {"values": [], "msg_types": []}


def verify_custom_broker_runtime():
    register_custom_broker(_BROKER_KIND, Batch4MemPublisher, Batch4MemConsumer)
    ok(f"register_custom_broker('{_BROKER_KIND}', ...) 注册成功")

    @boost(
        BoosterParams(
            queue_name=f"real_verify_batch4_broker_{_TS}",
            broker_kind=_BROKER_KIND,
            concurrent_num=1,
            is_auto_start_consuming_message=False,
            is_send_consumer_heartbeat_to_redis=False,
            create_logger_file=False,
        )
    )
    def broker_task(x):
        _BROKER_RECEIVED["values"].append(x)
        return x * 2

    broker_task.push(10)
    broker_task.push(20)
    if broker_task.publisher.get_message_count() == 2:
        ok("自定义 broker 发布成功，get_message_count=2")
    else:
        fail(f"发布后队列深度异常: {broker_task.publisher.get_message_count()}")

    pub = broker_task.publisher
    if hasattr(pub, "_last_msg_type") and pub._last_msg_type == "str":
        ok("自定义 Publisher._publish_impl 收到 JSON 字符串 (str)")
    else:
        fail(f"_publish_impl 收到类型异常: {getattr(pub, '_last_msg_type', None)}")

    broker_task.consume()
    ok("自定义 broker consume() 启动成功")


# ========== Skill 3: developing-funboost-mixin ==========


class Batch4VerifyMixin(AbstractConsumer):
    def custom_init(self):
        super().custom_init()
        opts = self.consumer_params.user_options.get("batch4_mixin_options", {})
        self._flag = opts.get("flag", "default")
        _MIXIN_HOOK_CALLS.append(("custom_init", self._flag))

    def _both_sync_and_aio_frame_custom_record_process_info_func(
        self, current_function_result_status, kw
    ):
        super()._both_sync_and_aio_frame_custom_record_process_info_func(
            current_function_result_status, kw
        )
        body = kw.get("body", {})
        x_val = body.get("x") if isinstance(body, dict) else None
        _MIXIN_HOOK_CALLS.append(
            ("hook", current_function_result_status.success, x_val)
        )


@boost(
    BoosterParams(
        queue_name=f"real_verify_batch4_mixin_{_TS}",
        broker_kind=BrokerEnum.MEMORY_QUEUE,
        consumer_override_cls=Batch4VerifyMixin,
        concurrent_num=2,
        qps=10,
        is_auto_start_consuming_message=False,
        create_logger_file=False,
        user_options={"batch4_mixin_options": {"flag": "batch4"}},
    )
)
def mixin_task(x: int):
    print(f"[EXEC] mixin_task x={x}")
    return x * 3


def verify_mixin_runtime():
    for i in range(3):
        mixin_task.push(i)
    ok("Mixin 任务 push 3 条消息成功")
    mixin_task.consume()
    ok("consumer_override_cls Mixin consume() 启动成功")


def main():
    print("=== real_verify_batch4: Memory Queue Pool ===")
    verify_memory_funboost_pool()
    verify_get_future()

    print("\n=== real_verify_batch4: Broker Extension ===")
    check_register_custom_broker_api()
    check_abstract_methods()
    verify_custom_broker_runtime()

    print("\n=== real_verify_batch4: Mixin ===")
    verify_mixin_runtime()

    print("\n=== real_verify_batch4: 等待消费完成 ===")
    time.sleep(10)

    # Broker 消费结果
    if _BROKER_RECEIVED["values"] == [10, 20]:
        ok("自定义 broker 消费成功: values=[10, 20]")
    else:
        fail(f"自定义 broker 消费结果异常: {_BROKER_RECEIVED['values']!r}")

    # Mixin 钩子结果
    init_calls = [c for c in _MIXIN_HOOK_CALLS if c[0] == "custom_init"]
    if init_calls:
        ok(f"Mixin custom_init 被调用: {init_calls}")
    else:
        fail("Mixin custom_init 未被调用")

    hook_calls = [c for c in _MIXIN_HOOK_CALLS if c[0] == "hook"]
    if len(hook_calls) >= 3:
        ok(f"_both_sync_and_aio_frame_custom_record_process_info_func 被调用 {len(hook_calls)} 次")
    else:
        fail(f"后置钩子调用不足: {hook_calls}, all={_MIXIN_HOOK_CALLS}")

    print(f"\n=== 汇总: PASS={PASS_COUNT}, FAIL={FAIL_COUNT} ===")


if __name__ == "__main__":
    main()
    time.sleep(15)
    os._exit(66)
