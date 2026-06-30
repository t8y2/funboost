"""验证 funboost-timing-jobs SKILL — args 位置参数传递"""
import os
import time

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
_ts = int(time.time())
os.environ["PRINT_WRTIE_FILE_NAME"] = f"v2_timing_args_positional_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"v2_timing_args_positional_std_{_ts}"

from funboost import boost, BoosterParams, BrokerEnum, ApsJobAdder


@boost(BoosterParams(
    queue_name="v2_my_interval_task",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    concurrent_num=3,
))
def my_task(x: int, y: int):
    print(f"my_task x={x}, y={y}, sum={x + y}")


if __name__ == "__main__":
    print("[START] v2_timing_args_positional")
    my_task.consume()

    ApsJobAdder(my_task).add_push_job(
        trigger="interval",
        seconds=3,
        args=(1, 2),
        id="my_interval_job",
        replace_existing=True,
    )
    print("[OK] args=(1, 2) 注册成功")

    time.sleep(20)
    print("[DONE] v2_timing_args_positional")
    os._exit(66)
