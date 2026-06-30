"""round3b r2: developing-funboost-mixin — 运行时验证 Mixin 钩子可被调用（MEMORY_QUEUE）"""
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"r2_mixin_runtime_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"r2_mixin_runtime_std_{_ts}"

EXAMPLE = "developing-funboost-mixin / runtime hooks"
PASS = True
HOOKS = {
    "custom_init": 0,
    "submit_task": 0,
    "both_hook": 0,
    "frame_hook": 0,
}


def report(ok: bool, msg: str):
    global PASS
    if not ok:
        PASS = False
    tag = "PASS" if ok else "FAIL"
    print(f"[{tag}] {EXAMPLE}: {msg}")


try:
    from funboost import boost, BoosterParams, BrokerEnum
    from funboost.consumers.base_consumer import AbstractConsumer

    class VerifyMixin(AbstractConsumer):
        def custom_init(self):
            super().custom_init()
            HOOKS["custom_init"] += 1

        def _submit_task(self, kw):
            HOOKS["submit_task"] += 1
            super()._submit_task(kw)

        def _both_sync_and_aio_frame_custom_record_process_info_func(
            self, current_function_result_status, kw
        ):
            HOOKS["both_hook"] += 1
            super()._both_sync_and_aio_frame_custom_record_process_info_func(
                current_function_result_status, kw
            )

        def _frame_custom_record_process_info_func(self, current_function_result_status, kw):
            HOOKS["frame_hook"] += 1
            super()._frame_custom_record_process_info_func(current_function_result_status, kw)

    q = f"r2_mixin_runtime_{_ts}"

    @boost(
        BoosterParams(
            queue_name=q,
            broker_kind=BrokerEnum.MEMORY_QUEUE,
            consumer_override_cls=VerifyMixin,
            concurrent_num=2,
            qps=10,
            create_logger_file=False,
            is_send_consumer_heartbeat_to_redis=False,
        )
    )
    def add_one(x: int):
        return x + 1

    add_one.push(1)
    add_one.push(2)
    add_one.consume()

    time.sleep(3)

    report(HOOKS["custom_init"] >= 1, f"custom_init 被调用 {HOOKS['custom_init']} 次")
    report(HOOKS["submit_task"] >= 2, f"_submit_task 被调用 {HOOKS['submit_task']} 次（前置钩子）")
    report(HOOKS["both_hook"] >= 2, f"_both_sync_and_aio... 被调用 {HOOKS['both_hook']} 次")
    report(HOOKS["frame_hook"] >= 2, f"_frame_custom... 被调用 {HOOKS['frame_hook']} 次（worker 线程）")

except Exception as e:
    report(False, f"异常: {type(e).__name__}: {e}")

if __name__ == "__main__":
    time.sleep(15)
    print(f"\n=== 最终结果: {'PASS' if PASS else 'FAIL'} ===")
    os._exit(66 if PASS else 1)
