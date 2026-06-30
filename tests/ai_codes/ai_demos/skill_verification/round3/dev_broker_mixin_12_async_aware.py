"""验证 developing-funboost-mixin SKILL.md §异步兼容 MyAsyncAwareMixin (222-238)"""
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"dev_broker_mixin_12_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"dev_broker_mixin_12_std_{_ts}"

from funboost import boost, BoosterParams, BrokerEnum
from funboost.consumers.base_consumer import AbstractConsumer
from funboost.concurrent_pool.async_helper import simple_run_in_executor
from funboost.constant import ConcurrentModeEnum

DB_SAVES = []


class MyAsyncAwareMixin(AbstractConsumer):

    def _save_to_db(self, status):
        DB_SAVES.append({"success": status.success, "result": status.result})

    def _frame_custom_record_process_info_func(self, status, kw):
        """同步版本（含 IO）"""
        super()._frame_custom_record_process_info_func(status, kw)
        self._save_to_db(status)

    async def _aio_frame_custom_record_process_info_func(self, status, kw):
        """异步版本 — 通过 executor 复用同步逻辑"""
        await super()._aio_frame_custom_record_process_info_func(status, kw)
        await simple_run_in_executor(
            self._frame_custom_record_process_info_func, status, kw
        )


@boost(BoosterParams(
    queue_name=f"async_aware_r3_{_ts}",
    broker_kind=BrokerEnum.SQLITE_QUEUE,
    consumer_override_cls=MyAsyncAwareMixin,
    concurrent_mode=ConcurrentModeEnum.ASYNC,
    concurrent_num=2,
    create_logger_file=False,
    is_send_consumer_heartbeat_to_redis=False,
))
async def async_task(x):
    print(f"[OK] async_task x={x}")
    return x * 2


if __name__ == "__main__":
    import asyncio

    print("[START] dev_broker_mixin_12_async_aware")

    async def _main():
        await async_task.aio_push(8)
        async_task.consume()
        await asyncio.sleep(15)

    asyncio.run(_main())
    if len(DB_SAVES) >= 1:
        print(f"[PASS] MyAsyncAwareMixin 异步钩子运行成功, DB_SAVES={DB_SAVES}")
    else:
        print(f"[FAIL] DB_SAVES 为空")
    os._exit(66)
