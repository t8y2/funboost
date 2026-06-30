"""验证 developing-funboost-mixin SKILL.md §MonitorMixin 后置钩子 (125-172)"""
import os
import time
from unittest.mock import MagicMock, patch

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"v2_mixin_03_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"v2_mixin_03_std_{_ts}"

from funboost import boost, BoosterParams, BrokerEnum
from funboost.consumers.base_consumer import AbstractConsumer

HOOK_STATS = {"total": 0, "failures": 0, "sync_io": 0, "async_io": 0}


class MonitorMixin(AbstractConsumer):
    def custom_init(self):
        super().custom_init()
        self._total = 0
        self._failures = 0

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
        HOOK_STATS["total"] = self._total
        HOOK_STATS["failures"] = self._failures

    def _frame_custom_record_process_info_func(
        self, current_function_result_status, kw
    ):
        """同步 IO 允许 — 如写数据库、发告警"""
        super()._frame_custom_record_process_info_func(
            current_function_result_status, kw
        )
        if not current_function_result_status.success:
            import requests

            requests.post("http://alert.example.com/notify", json={
                "queue": self.queue_name,
                "error": str(current_function_result_status.exception),
                "total": self._total,
            })
            HOOK_STATS["sync_io"] += 1

    async def _aio_frame_custom_record_process_info_func(
        self, current_function_result_status, kw
    ):
        """异步 IO 允许 — 异步消费模式下使用"""
        await super()._aio_frame_custom_record_process_info_func(
            current_function_result_status, kw
        )
        if not current_function_result_status.success:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                await session.post("http://alert.example.com/notify", json={
                    "queue": self.queue_name,
                    "error": str(current_function_result_status.exception),
                })
            HOOK_STATS["async_io"] += 1


@boost(BoosterParams(
    queue_name=f"monitor_mixin_v2_{_ts}",
    broker_kind=BrokerEnum.SQLITE_QUEUE,
    consumer_override_cls=MonitorMixin,
    concurrent_num=1,
    create_logger_file=False,
    is_send_consumer_heartbeat_to_redis=False,
))
def monitor_task(x: int):
    if x == 0:
        raise ValueError("模拟失败")
    return x


if __name__ == "__main__":
    print("[START] v2_mixin_03_monitor_hooks")
    mock_post = MagicMock(return_value=MagicMock(status_code=200))
    with patch("requests.post", mock_post):
        monitor_task.push(1)
        monitor_task.push(0)
        monitor_task.consume()
        time.sleep(15)

    ok = HOOK_STATS["total"] >= 2 and HOOK_STATS["failures"] >= 1 and HOOK_STATS["sync_io"] >= 1
    if ok:
        print(f"[PASS] MonitorMixin 三种后置钩子签名正确且同步 IO 钩子触发: {HOOK_STATS}")
    else:
        print(f"[FAIL] HOOK_STATS={HOOK_STATS!r}, requests.post calls={mock_post.call_count}")
    os._exit(66)
