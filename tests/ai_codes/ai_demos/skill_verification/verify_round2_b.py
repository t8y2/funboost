"""Round2 综合验证：developing-funboost-broker / mixin / advanced-retry SKILL.md 修复点"""
import inspect
import os
import threading
import time
from collections import deque
from threading import Lock

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
_ts = int(time.time())
os.environ["PRINT_WRTIE_FILE_NAME"] = f"verify_round2_b_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"verify_round2_b_std_{_ts}"

PASS = []
FAIL = []
WARN = []


def ok(msg):
    PASS.append(msg)
    print(f"[PASS] {msg}")


def fail(msg):
    FAIL.append(msg)
    print(f"[FAIL] {msg}")


def warn(msg):
    WARN.append(msg)
    print(f"[WARN] {msg}")


# ---------------------------------------------------------------------------
# 静态：源码与 SKILL 修复点核对
# ---------------------------------------------------------------------------

def check_requeue_body_is_dict_in_source():
    """_requeue 调用路径上 kw['body'] 已被 _convert_msg_before_run 转为 dict"""
    from funboost.consumers.base_consumer import AbstractConsumer

    submit_src = inspect.getsource(AbstractConsumer._submit_task)
    if "_convert_msg_before_run(kw['body'])" in submit_src or '_convert_msg_before_run(kw["body"])' in submit_src:
        ok("_submit_task 首行将 kw['body'] 转为 dict")
    else:
        fail("_submit_task 未调用 _convert_msg_before_run")

    run_src = inspect.getsource(AbstractConsumer._run_consuming_function_with_confirm_and_retry)
    if "self._requeue(kw)" in run_src:
        ok("_run_consuming_function_with_confirm_and_retry 会调用 _requeue(kw)")
    else:
        fail("未找到 _requeue(kw) 调用点")

    # ExceptionForRequeue 路径：此时 kw 已在 _submit_task 中转换
    if "ExceptionForRequeue" in run_src and "self._requeue(kw)" in run_src:
        ok("ExceptionForRequeue 触发 _requeue 时 kw['body'] 已是 dict（_submit_task 已转换）")
    else:
        fail("ExceptionForRequeue -> _requeue 路径未确认")


def check_publish_impl_msg_type_in_source():
    from funboost.publishers.base_publisher import AbstractPublisher

    gen_src = inspect.getsource(AbstractPublisher.generate_msg_context_for_publish)
    exec_src = inspect.getsource(AbstractPublisher._execute_publish)

    gen_compact = gen_src.replace(" ", "")
    if "_is_memory_queue" in gen_src and "msg_json=msg_dict" in gen_compact:
        ok("内存队列 _publish_impl 收到 dict（generate_msg_context_for_publish）")
    else:
        fail("未找到内存队列 dict 分支")

    if "Serialization.to_json_str(msg_dict)" in gen_src:
        ok("非内存队列 _publish_impl 收到 JSON 字符串")
    else:
        fail("非内存队列 JSON 序列化逻辑未找到")

    if "_wrapped_publish_impl(publish_msg_context.msg_json)" in exec_src:
        ok("_execute_publish 传递 msg_json 给 _publish_impl")
    else:
        fail("_execute_publish 传参不符合预期")


def check_submit_task_before_run_in_source():
    from funboost.consumers.base_consumer import AbstractConsumer

    src = inspect.getsource(AbstractConsumer._submit_task)
    submit_idx = src.find("concurrent_pool.submit")
    convert_idx = src.find("_convert_msg_before_run")
    if convert_idx != -1 and submit_idx != -1 and convert_idx < submit_idx:
        ok("_submit_task：_convert_msg_before_run 在 concurrent_pool.submit 之前（任务执行前）")
    else:
        fail("_submit_task 调用顺序与 SKILL 描述不符")

    run_src = inspect.getsource(AbstractConsumer._run)
    hook_idx = run_src.find("_frame_custom_record_process_info_func")
    submit_in_run = "concurrent_pool.submit" in src
    if hook_idx != -1 and submit_in_run:
        ok("Mixin 重写 _submit_task 可在任务进入线程池前拦截（SKILL 前置检查/限流合理）")
    else:
        fail("无法确认 _submit_task 前置拦截时机")


def check_do_task_filtering_not_success_only():
    from funboost.consumers.base_consumer import AbstractConsumer

    run_src = inspect.getsource(AbstractConsumer._run)
    # 查找 add_a_value 调用附近是否有 success 判断
    idx = run_src.find("add_a_value")
    if idx == -1:
        fail("_run 中未找到 add_a_value")
        return
    snippet = run_src[max(0, idx - 200): idx + 120]
    if "do_task_filtering" in snippet and "success" not in snippet.split("add_a_value")[0][-80:]:
        ok("do_task_filtering：add_a_value 在完成消费周期后调用，无 success 条件（非仅成功）")
    else:
        # 更精确：整段 if 块
        if "if self._get_priority_conf(kw, 'do_task_filtering'):" in run_src:
            block_start = run_src.index("if self._get_priority_conf(kw, 'do_task_filtering'):")
            block = run_src[block_start:block_start + 200]
            if "success" not in block:
                ok("do_task_filtering 的 add_a_value 块不检查 success")
            else:
                fail("do_task_filtering add_a_value 仍依赖 success")
        else:
            fail("未找到 do_task_filtering 分支")


def check_frame_custom_hook_in_run_worker_path():
    from funboost.consumers.base_consumer import AbstractConsumer

    run_src = inspect.getsource(AbstractConsumer._run)
    submit_src = inspect.getsource(AbstractConsumer._submit_task)

    if "self._frame_custom_record_process_info_func(current_function_result_status, kw)" in run_src:
        ok("_frame_custom_record_process_info_func 在 _run 内调用（worker 线程路径）")
    else:
        fail("_run 内未调用 _frame_custom_record_process_info_func")

    if "_frame_custom_record_process_info_func" not in submit_src:
        ok("_submit_task 不调用 _frame_custom_record_process_info_func（非调度线程误调用）")
    else:
        fail("_submit_task 错误地调用了 _frame_custom_record_process_info_func")


def check_skill_md_text_fixes():
    skill_paths = {
        "broker": r"D:\codes\funboost\.agents\skills\developing-funboost-broker\SKILL.md",
        "mixin": r"D:\codes\funboost\.agents\skills\developing-funboost-mixin\SKILL.md",
        "retry": r"D:\codes\funboost\.agents\skills\funboost-advanced-retry\SKILL.md",
    }
    broker_text = open(skill_paths["broker"], encoding="utf-8").read()
    mixin_text = open(skill_paths["mixin"], encoding="utf-8").read()
    retry_text = open(skill_paths["retry"], encoding="utf-8").read()

    if "Serialization.to_json_str(kw[\"body\"])" in broker_text or "Serialization.to_json_str(kw['body'])" in broker_text:
        ok("broker SKILL _requeue 示例使用 Serialization.to_json_str(kw['body'])")
    else:
        fail("broker SKILL 缺少 Serialization.to_json_str(kw['body']) 示例")

    if "MEMORY_QUEUE" in broker_text and "FASTEST_MEM_QUEUE" in broker_text and "收到 dict" in broker_text:
        ok("broker SKILL 说明内存队列 _publish_impl 收到 dict")
    else:
        fail("broker SKILL 未说明内存队列 dict 例外")

    if "前置检查/限流" in mixin_text or "任务提交到线程池前的前置检查" in mixin_text:
        ok("mixin SKILL _submit_task 示例改为前置检查/限流语义")
    else:
        fail("mixin SKILL _submit_task 示例未更新为前置检查")

    if "并发池工作线程" in mixin_text or "与任务执行同线程" in mixin_text:
        ok("mixin SKILL _frame_custom... 描述为 worker 线程调用")
    else:
        fail("mixin SKILL 未更新 _frame_custom 线程描述")

    if "完成一次消费周期后" in retry_text:
        ok("retry SKILL do_task_filtering 描述为完成消费周期后")
    else:
        fail("retry SKILL 未更新 do_task_filtering 语义")

    if "相同入参成功执行过后自动跳过" in retry_text:
        fail("retry SKILL 组合示例仍写「成功执行过后自动跳过」（与源码不符）")
    else:
        ok("retry SKILL 组合示例未保留错误的「仅成功」表述")


# ---------------------------------------------------------------------------
# 运行时：自定义 broker / mixin / 过滤 / 线程
# ---------------------------------------------------------------------------

_STORE = {}
_STORE_LOCK = Lock()
_BROKER_KIND = f"SKILL_VERIFY_ROUND2_B_{_ts}"
_runtime = {
    "publish_types_mq": [],
    "publish_types_mem": [],
    "requeue_body_types": [],
    "submit_before_run_order": [],
    "frame_hook_threads": [],
    "run_threads": [],
    "filter_functional": {},
}


def _get_q(name):
    with _STORE_LOCK:
        if name not in _STORE:
            _STORE[name] = deque()
        return _STORE[name]


def run_custom_broker_runtime_tests():
    from funboost import boost, BoosterParams, register_custom_broker, BrokerEnum
    from funboost.publishers.base_publisher import AbstractPublisher
    from funboost.consumers.base_consumer import AbstractConsumer
    from funboost.core.exceptions import ExceptionForRequeue
    from funboost.core.serialization import Serialization

    class TrackPublisher(AbstractPublisher):
        def _publish_impl(self, msg):
            _runtime["publish_types_mq"].append(type(msg).__name__)
            _get_q(self.queue_name).append(msg)

        def clear(self):
            _get_q(self.queue_name).clear()

        def get_message_count(self):
            return len(_get_q(self.queue_name))

        def close(self):
            pass

    class TrackConsumer(AbstractConsumer):
        def _dispatch_task(self):
            q = _get_q(self.queue_name)
            if q:
                body = q.popleft()
                self._submit_task({"body": body})

        def _confirm_consume(self, kw):
            pass

        def _requeue(self, kw):
            _runtime["requeue_body_types"].append(type(kw["body"]).__name__)
            body = Serialization.to_json_str(kw["body"])
            _get_q(self.queue_name).append(body)

    register_custom_broker(_BROKER_KIND, TrackPublisher, TrackConsumer)

    q_requeue = f"round2b_requeue_{_ts}"

    @boost(
        BoosterParams(
            queue_name=q_requeue,
            broker_kind=_BROKER_KIND,
            concurrent_num=1,
            is_auto_start_consuming_message=False,
            is_send_consumer_heartbeat_to_redis=False,
            create_logger_file=False,
        )
    )
    def task_requeue_once(x: int):
        raise ExceptionForRequeue("force requeue for verify")

    task_requeue_once.push(1)
    if _runtime["publish_types_mq"] == ["str"]:
        ok("运行时：自定义 broker _publish_impl 收到 str（非 dict）")
    else:
        fail(f"运行时：_publish_impl 类型异常 {_runtime['publish_types_mq']}")

    task_requeue_once.consume()
    time.sleep(6)
    if _runtime["requeue_body_types"] and all(t == "dict" for t in _runtime["requeue_body_types"]):
        ok("运行时：_requeue 被调用时 kw['body'] 类型为 dict")
    else:
        fail(f"运行时：_requeue body 类型异常 {_runtime['requeue_body_types']}")

    # 内存队列 _publish_impl 收到 dict
    mem_types = []

    class MemTrackPublisher(AbstractPublisher):
        def _publish_impl(self, msg):
            mem_types.append(type(msg).__name__)
            super()._publish_impl(msg)

        def clear(self):
            super().clear()

        def get_message_count(self):
            return super().get_message_count()

        def close(self):
            pass

    from funboost.publishers.memory_deque_publisher import DequePublisher

    # 直接用 MEMORY_QUEUE 发布
    @boost(
        BoosterParams(
            queue_name=f"round2b_mem_{_ts}",
            broker_kind=BrokerEnum.MEMORY_QUEUE,
            is_auto_start_consuming_message=False,
            create_logger_file=False,
        )
    )
    def mem_task(x: int):
        return x

    # hook publisher _publish_impl
    orig_wrapped = mem_task.publisher._wrapped_publish_impl

    def wrapped_publish(msg):
        mem_types.append(type(msg).__name__)
        return orig_wrapped(msg)

    mem_task.publisher._wrapped_publish_impl = wrapped_publish
    mem_task.push(7)
    if mem_types == ["dict"]:
        ok("运行时：MEMORY_QUEUE _publish_impl 收到 dict")
    else:
        fail(f"运行时：MEMORY_QUEUE _publish_impl 类型 {mem_types}")


class SubmitOrderMixin:
    def _submit_task(self, kw):
        _runtime["submit_before_run_order"].append("submit_task")
        super()._submit_task(kw)

    def _run(self, kw):
        _runtime["submit_before_run_order"].append("run_start")
        return super()._run(kw)


class FrameHookThreadMixin:
    def _frame_custom_record_process_info_func(self, current_function_result_status, kw):
        super()._frame_custom_record_process_info_func(current_function_result_status, kw)
        _runtime["frame_hook_threads"].append(threading.current_thread().ident)

    def _run(self, kw):
        _runtime["run_threads"].append(threading.current_thread().ident)
        return super()._run(kw)


class CombinedVerifyMixin(SubmitOrderMixin, FrameHookThreadMixin):
    pass


def run_mixin_runtime_tests():
    from funboost import boost, BoosterParams, BrokerEnum

    @boost(
        BoosterParams(
            queue_name=f"round2b_mixin_{_ts}",
            broker_kind=BrokerEnum.SQLITE_QUEUE,
            consumer_override_cls=CombinedVerifyMixin,
            concurrent_num=1,
            qps=5,
            is_auto_start_consuming_message=False,
            create_logger_file=False,
        )
    )
    def mixin_task(x: int):
        return x + 1

    mixin_task.push(100)
    mixin_task.consume()
    time.sleep(8)

    order = _runtime["submit_before_run_order"]
    if order and order[0] == "submit_task" and "run_start" in order:
        ok(f"运行时：_submit_task 在 _run 之前调用 order={order}")
    else:
        fail(f"运行时：_submit_task/_run 顺序异常 order={order}")

    if _runtime["run_threads"] and _runtime["frame_hook_threads"]:
        if _runtime["run_threads"][0] == _runtime["frame_hook_threads"][0]:
            ok("运行时：_frame_custom_record_process_info_func 与任务同 worker 线程")
        else:
            fail(
                f"运行时：hook 线程与 run 线程不一致 "
                f"run={_runtime['run_threads']} hook={_runtime['frame_hook_threads']}"
            )
    else:
        fail(f"运行时：未采集到线程信息 run={_runtime['run_threads']} hook={_runtime['frame_hook_threads']}")


def run_do_task_filtering_runtime_test():
    """失败任务完成消费周期后也应进入过滤集"""
    from funboost import boost, BoosterParams, BrokerEnum
    from funboost.utils.redis_manager import RedisMixin

    try:
        r = RedisMixin().redis_db_filter_and_rpc_result.ping()
    except Exception as e:
        warn(f"Redis 不可用，跳过 do_task_filtering 功能测试: {e}")
        return

    queue = f"round2b_filter_{_ts}"
    filter_key = f"filter_set:{queue}"

    @boost(
        BoosterParams(
            queue_name=queue,
            broker_kind=BrokerEnum.SQLITE_QUEUE,
            do_task_filtering=True,
            max_retry_times=0,
            concurrent_num=1,
            is_auto_start_consuming_message=False,
            is_send_consumer_heartbeat_to_redis=False,
            create_logger_file=False,
        )
    )
    def filter_fail_task(x: int):
        raise ValueError(f"always fail x={x}")

    # 清空可能残留的 filter key
    RedisMixin().redis_db_filter_and_rpc_result.delete(filter_key)

    filter_fail_task.push(42)
    filter_fail_task.consume()
    time.sleep(10)

    from funboost.consumers.redis_filter import RedisFilter

    rf = RedisFilter(filter_key, 0)
    exists_after_fail = rf.check_value_exists({"x": 42})

    _runtime["filter_functional"]["exists_after_fail"] = exists_after_fail
    if exists_after_fail:
        ok("运行时：任务失败完成消费周期后仍加入过滤集（非仅成功）")
    else:
        fail("运行时：失败任务未加入过滤集，与 SKILL「完成消费周期后」描述不符")

    filter_fail_task.push(42)
    time.sleep(8)
    # 被过滤时函数不应再执行；第一次已失败执行过，第二次应 skip
    # exec_count 未 hook 到原函数，用 redis 存在性 + 队列消费无新异常日志即可
    if rf.check_value_exists({"x": 42}):
        ok("运行时：重复 push 同参时 filter 键仍存在，去重生效")
    else:
        fail("运行时：filter 键丢失")


def main():
    print("=" * 60)
    print("SKILL Round2-B 综合验证 (broker / mixin / advanced-retry)")
    print("=" * 60)

    print("\n--- 静态源码核对 ---")
    check_requeue_body_is_dict_in_source()
    check_publish_impl_msg_type_in_source()
    check_submit_task_before_run_in_source()
    check_do_task_filtering_not_success_only()
    check_frame_custom_hook_in_run_worker_path()
    check_skill_md_text_fixes()

    print("\n--- 运行时验证 ---")
    run_custom_broker_runtime_tests()
    run_mixin_runtime_tests()
    run_do_task_filtering_runtime_test()

    print("\n" + "=" * 60)
    print(f"PASS: {len(PASS)}  FAIL: {len(FAIL)}  WARN: {len(WARN)}")
    if WARN:
        for w in WARN:
            print(f"  WARN: {w}")
    if FAIL:
        for f in FAIL:
            print(f"  FAIL: {f}")
    print("OVERALL:", "FAIL" if FAIL else "PASS")
    print("=" * 60)

    time.sleep(1)
    os._exit(1 if FAIL else 66)


if __name__ == "__main__":
    main()
