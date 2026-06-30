"""验证 developing-funboost-mixin SKILL.md §Mixin 模板 (38-76)"""
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"v2_mixin_01_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"v2_mixin_01_std_{_ts}"

from funboost.consumers.base_consumer import AbstractConsumer

MIXIN_STATE = {"counter": None, "threshold": None, "hook_calls": 0}


class MyConsumerMixin(AbstractConsumer):
    """
    继承 AbstractConsumer 是可选的（仅为 IDE 自动补全）。
    不继承也能正常工作——运行时 mixin 通过动态多重继承合并 MRO。
    """

    def custom_init(self):
        super().custom_init()
        opts = self.consumer_params.user_options.get("my_mixin_options", {})
        self._threshold = opts.get("threshold", 10)
        self._counter = 0
        MIXIN_STATE["counter"] = self._counter
        MIXIN_STATE["threshold"] = self._threshold

    def _submit_task(self, kw):
        """任务提交到线程池前的前置检查/限流"""
        if self._counter > self._threshold:
            print(f"[WARN] 已提交 {self._counter} 次，超过阈值 {self._threshold}，可进行限流")
        super()._submit_task(kw)

    def _both_sync_and_aio_frame_custom_record_process_info_func(
        self, current_function_result_status, kw
    ):
        super()._both_sync_and_aio_frame_custom_record_process_info_func(
            current_function_result_status, kw
        )
        if current_function_result_status.success:
            self._counter = 0
        else:
            self._counter += 1
        MIXIN_STATE["hook_calls"] += 1
        MIXIN_STATE["counter"] = self._counter


if __name__ == "__main__":
    from funboost import boost, BoosterParams, BrokerEnum

    @boost(BoosterParams(
        queue_name=f"mixin_tpl_v2_{_ts}",
        broker_kind=BrokerEnum.SQLITE_QUEUE,
        consumer_override_cls=MyConsumerMixin,
        concurrent_num=1,
        create_logger_file=False,
        is_send_consumer_heartbeat_to_redis=False,
        user_options={"my_mixin_options": {"threshold": 10}},
    ))
    def tpl_task(x):
        print(f"[OK] tpl_task x={x}")
        return x

    print("[START] v2_mixin_01_template")
    tpl_task.push(5)
    tpl_task.consume()
    time.sleep(15)
    if MIXIN_STATE["threshold"] == 10 and MIXIN_STATE["hook_calls"] >= 1:
        print("[PASS] MyConsumerMixin 模板类定义与钩子正常")
    else:
        print(f"[FAIL] MIXIN_STATE={MIXIN_STATE!r}")
    os._exit(66)
