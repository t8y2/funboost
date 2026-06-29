"""验证 developing-funboost-mixin skill 中的代码示例"""
import os
import time

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"verify_mixin_{int(time.time())}"
os.environ["SYS_STD_FILE_NAME"] = f"verify_mixin_std_{int(time.time())}"

from funboost import boost, BoosterParams, BrokerEnum
from funboost.consumers.base_consumer import AbstractConsumer


class MyMonitorMixin(AbstractConsumer):
    """验证 mixin 的 custom_init + 后置钩子"""

    def custom_init(self):
        super().custom_init()
        opts = self.consumer_params.user_options.get("monitor_options", {})
        self._threshold = opts.get("threshold", 5)
        self._total = 0
        self._failures = 0
        print(f"[OK] MyMonitorMixin.custom_init 执行, threshold={self._threshold}")

    def _both_sync_and_aio_frame_custom_record_process_info_func(
        self, current_function_result_status, kw
    ):
        """纯内存操作 — 禁止 IO"""
        super()._both_sync_and_aio_frame_custom_record_process_info_func(
            current_function_result_status, kw
        )
        self._total += 1
        if not current_function_result_status.success:
            self._failures += 1
        print(f"[OK] 钩子触发: total={self._total}, failures={self._failures}, success={current_function_result_status.success}")


@boost(BoosterParams(
    queue_name="verify_mixin_task",
    broker_kind=BrokerEnum.SQLITE_QUEUE,
    consumer_override_cls=MyMonitorMixin,
    concurrent_num=2,
    qps=5,
    user_options={
        "monitor_options": {
            "threshold": 3,
        }
    },
))
def mixin_task(x: int):
    if x % 3 == 0:
        raise ValueError(f"模拟失败 x={x}")
    print(f"[OK] mixin_task x={x}, result={x*2}")
    return x * 2


if __name__ == "__main__":
    # 发布测试消息
    for i in range(6):
        mixin_task.push(i)

    # 启动消费
    mixin_task.consume()

    time.sleep(15)
    print("[DONE] verify_mixin 完成")
    os._exit(66)
