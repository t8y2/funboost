"""round3b r2: developing-funboost-mixin — Mixin 钩子方法签名 vs base_consumer/base_publisher"""
import inspect
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"r2_mixin_sig_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"r2_mixin_sig_std_{_ts}"

EXAMPLE = "developing-funboost-mixin / method signatures"
PASS = True

# SKILL 文档中列出的 Consumer 重写点及参数名（不含 self）
CONSUMER_METHODS = {
    "custom_init": [],
    "_submit_task": ["kw"],
    "_before_start_consuming_message_hook": [],
    "_both_sync_and_aio_frame_custom_record_process_info_func": [
        "current_function_result_status",
        "kw",
    ],
    "_frame_custom_record_process_info_func": [
        "current_function_result_status",
        "kw",
    ],
    "_aio_frame_custom_record_process_info_func": [
        "current_function_result_status",
        "kw",
    ],
    "_run": ["kw"],
    "_async_run": ["kw"],
}

PUBLISHER_METHODS = {
    "_publish_impl": ["msg"],
    "_after_publish": ["publish_msg_context"],
}


def report(ok: bool, msg: str):
    global PASS
    if not ok:
        PASS = False
    tag = "PASS" if ok else "FAIL"
    print(f"[{tag}] {EXAMPLE}: {msg}")


def param_names(method):
    sig = inspect.signature(method)
    return [p for p in sig.parameters if p != "self"]


def check_methods(base_cls, expected: dict, label: str):
    for name, exp_params in expected.items():
        if not hasattr(base_cls, name):
            report(False, f"{label}.{name} 不存在")
            continue
        method = getattr(base_cls, name)
        actual = param_names(method)
        if actual == exp_params:
            is_async = inspect.iscoroutinefunction(method)
            extra = " (async)" if is_async else ""
            report(True, f"{label}.{name}({', '.join(actual)}) 与 SKILL 一致{extra}")
        else:
            report(
                False,
                f"{label}.{name} 参数不符: SKILL={exp_params}, 源码={actual}",
            )


try:
    from funboost.consumers.base_consumer import AbstractConsumer
    from funboost.publishers.base_publisher import AbstractPublisher

    check_methods(AbstractConsumer, CONSUMER_METHODS, "AbstractConsumer")

    # async 方法必须是 coroutine function
    report(
        inspect.iscoroutinefunction(AbstractConsumer._aio_frame_custom_record_process_info_func),
        "AbstractConsumer._aio_frame_custom_record_process_info_func 是 async def",
    )
    report(
        inspect.iscoroutinefunction(AbstractConsumer._async_run),
        "AbstractConsumer._async_run 是 async def",
    )

    check_methods(AbstractPublisher, PUBLISHER_METHODS, "AbstractPublisher")

    # SKILL 模板类若按文档签名定义，应能通过 inspect 绑定
    from funboost.consumers.base_consumer import AbstractConsumer as AC

    class SkillTemplateMixin(AC):
        def custom_init(self):
            super().custom_init()

        def _submit_task(self, kw):
            super()._submit_task(kw)

        def _before_start_consuming_message_hook(self):
            super()._before_start_consuming_message_hook()

        def _both_sync_and_aio_frame_custom_record_process_info_func(
            self, current_function_result_status, kw
        ):
            super()._both_sync_and_aio_frame_custom_record_process_info_func(
                current_function_result_status, kw
            )

        def _frame_custom_record_process_info_func(self, current_function_result_status, kw):
            super()._frame_custom_record_process_info_func(current_function_result_status, kw)

        async def _aio_frame_custom_record_process_info_func(self, current_function_result_status, kw):
            await super()._aio_frame_custom_record_process_info_func(
                current_function_result_status, kw
            )

        def _run(self, kw):
            super()._run(kw)

        async def _async_run(self, kw):
            await super()._async_run(kw)

    for name in CONSUMER_METHODS:
        report(hasattr(SkillTemplateMixin, name), f"SKILL 模板 Mixin 可定义 {name}")

    from funboost.publishers.base_publisher import AbstractPublisher as AP

    class SkillPublisherMixin(AP):
        def _publish_impl(self, msg):
            pass

        def _after_publish(self, publish_msg_context):
            super()._after_publish(publish_msg_context)

        def clear(self):
            pass

        def get_message_count(self):
            return 0

        def close(self):
            pass

    report(hasattr(SkillPublisherMixin, "_publish_impl"), "SKILL Publisher Mixin 可定义 _publish_impl")
    report(hasattr(SkillPublisherMixin, "_after_publish"), "SKILL Publisher Mixin 可定义 _after_publish")

except Exception as e:
    report(False, f"异常: {type(e).__name__}: {e}")

if __name__ == "__main__":
    time.sleep(15)
    print(f"\n=== 最终结果: {'PASS' if PASS else 'FAIL'} ===")
    os._exit(66 if PASS else 1)
