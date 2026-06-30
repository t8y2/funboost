"""第2轮深度验证C：fct 上下文 + 自定义 broker + publish TaskOptions + 异构消息"""
import os
import time
import sys
from collections import deque
from threading import Lock

os.environ["PYTHONPATH"] = r"D:\codes\funboost"
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = "real_verify_r2c_print.txt"
os.environ["SYS_STD_FILE_NAME"] = "real_verify_r2c_std.txt"
sys.path.insert(0, r"D:\codes\funboost")

from funboost import boost, BoosterParams, BrokerEnum, TaskOptions, register_custom_broker
from funboost.publishers.base_publisher import AbstractPublisher
from funboost.consumers.base_consumer import AbstractConsumer
from funboost.core.serialization import Serialization

_TS = int(time.time())
PASS_COUNT = 0
FAIL_COUNT = 0

# ---------- 自定义 broker 共享存储 ----------
_BROKER_KIND = f"REAL_VERIFY_R2C_LIST_{_TS}"
_STORE = {}
_STORE_LOCK = Lock()


def _get_q(name):
    with _STORE_LOCK:
        if name not in _STORE:
            _STORE[name] = deque()
        return _STORE[name]


class ListPublisher(AbstractPublisher):
    def _publish_impl(self, msg: str):
        _get_q(self.queue_name).append(msg)

    def clear(self):
        _get_q(self.queue_name).clear()

    def get_message_count(self):
        return len(_get_q(self.queue_name))

    def close(self):
        pass


class ListConsumer(AbstractConsumer):
    def _dispatch_task(self):
        q = _get_q(self.queue_name)
        if q:
            msg_string = q.popleft()
            self._submit_task({"body": msg_string})

    def _confirm_consume(self, kw):
        pass

    def _requeue(self, kw):
        body = Serialization.to_json_str(kw["body"])
        _get_q(self.queue_name).appendleft(body)


register_custom_broker(_BROKER_KIND, ListPublisher, ListConsumer)


def _pass(msg):
    global PASS_COUNT
    PASS_COUNT += 1
    print(f"[PASS] {msg}")


def _fail(msg):
    global FAIL_COUNT
    FAIL_COUNT += 1
    print(f"[FAIL] {msg}")


# ========== 场景1：fct 上下文在消费期间可访问 ==========

context_info = {}


@boost(
    BoosterParams(
        queue_name=f"real_verify_r2c_context_{_TS}",
        broker_kind=BrokerEnum.MEMORY_QUEUE,
        concurrent_num=3,
    )
)
def task_with_context(x):
    from funboost import fct

    context_info["task_id"] = fct.task_id
    context_info["queue_name"] = fct.queue_name
    context_info["run_times"] = fct.function_result_status.run_times
    print(f"[EXEC] task_with_context x={x}, task_id={fct.task_id}")


def scenario1_fct_context():
    print("\n=== 场景1：fct 上下文在消费期间可访问 ===")
    task_with_context.push(42)
    task_with_context.consume()
    time.sleep(12)
    if (
        context_info.get("task_id")
        and context_info.get("queue_name")
        and context_info.get("run_times")
    ):
        _pass(
            f"fct.task_id={context_info['task_id']}, "
            f"queue_name={context_info['queue_name']}, "
            f"run_times={context_info['run_times']}"
        )
    else:
        _fail(f"fct 上下文字段缺失: context_info={context_info}")


# ========== 场景2：自定义 broker register_custom_broker 端到端 ==========

custom_broker_exec = []


@boost(
    BoosterParams(
        queue_name=f"real_verify_r2c_custom_broker_{_TS}",
        broker_kind=_BROKER_KIND,
        concurrent_num=3,
    )
)
def custom_broker_task(x):
    custom_broker_exec.append(x)
    print(f"[EXEC] custom_broker_task x={x}")


def scenario2_custom_broker():
    print("\n=== 场景2：自定义 broker register_custom_broker 端到端 ===")
    custom_broker_task.push(99)
    custom_broker_task.consume()
    time.sleep(12)
    if 99 in custom_broker_exec:
        _pass(f"自定义 broker 消费成功: custom_broker_exec={custom_broker_exec}")
    else:
        _fail(f"自定义 broker 未消费消息: custom_broker_exec={custom_broker_exec}")


# ========== 场景3：publish + TaskOptions(countdown=0, task_id='custom_id') ==========

ordered_task_fct_id = {}


@boost(
    BoosterParams(
        queue_name=f"real_verify_r2c_ordered_{_TS}",
        broker_kind=BrokerEnum.MEMORY_QUEUE,
        concurrent_num=3,
    )
)
def ordered_task(msg):
    from funboost import fct

    ordered_task_fct_id["task_id"] = fct.task_id
    print(f"[EXEC] ordered_task msg={msg!r}, fct.task_id={fct.task_id}")


def scenario3_publish_task_options():
    print("\n=== 场景3：publish + TaskOptions(countdown=0, task_id) ===")
    ordered_task.publish(
        {"msg": "hello"},
        task_options=TaskOptions(task_id="my_custom_id_123", countdown=0),
    )
    ordered_task.consume()
    time.sleep(12)
    actual = ordered_task_fct_id.get("task_id")
    if actual == "my_custom_id_123":
        _pass(f"publish TaskOptions task_id={actual}")
    else:
        _fail(f"publish TaskOptions task_id 错误: 期望 my_custom_id_123, 实际 {actual!r}")


# ========== 场景4：should_check_publish_func_params=False + **kwargs 消费异构消息 ==========

external_kwargs = {}


@boost(
    BoosterParams(
        queue_name=f"real_verify_r2c_external_{_TS}",
        broker_kind=BrokerEnum.MEMORY_QUEUE,
        should_check_publish_func_params=False,
        concurrent_num=3,
    )
)
def handle_external(**kwargs):
    external_kwargs.update(kwargs)
    print(f"[EXEC] handle_external kwargs={kwargs}")


def scenario4_heterogeneous_kwargs():
    print("\n=== 场景4：should_check_publish_func_params=False + **kwargs ===")
    handle_external.publish(
        {"user_id": 100, "action": "login", "extra_field": "unknown"}
    )
    handle_external.consume()
    time.sleep(12)
    if (
        external_kwargs.get("user_id") == 100
        and external_kwargs.get("action") == "login"
        and external_kwargs.get("extra_field") == "unknown"
    ):
        _pass(
            f"**kwargs 消费异构消息: user_id={external_kwargs.get('user_id')}, "
            f"action={external_kwargs.get('action')!r}, "
            f"extra_field={external_kwargs.get('extra_field')!r}"
        )
    else:
        _fail(f"**kwargs 消费异构消息失败: external_kwargs={external_kwargs}")


if __name__ == "__main__":
    print("=== real_verify_round2c: 第2轮深度验证C ===")

    scenario1_fct_context()
    scenario2_custom_broker()
    scenario3_publish_task_options()
    scenario4_heterogeneous_kwargs()

    print(f"\n=== 第2轮验证C结果 ===")
    print(f"PASS: {PASS_COUNT}")
    print(f"FAIL: {FAIL_COUNT}")
    os._exit(66)
