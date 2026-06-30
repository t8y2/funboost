"""验证 skill: funboost-memory-queue-pool §6 broker_kind 切换模式（MemoryFunboostPool / FunboostPool）"""
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"v2_broker_switch_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"v2_broker_switch_std_{_ts}"

from funboost import boost, BoosterParams, BrokerEnum, MemoryFunboostPool, FunboostPool


def my_task(url):
    return f"done:{url}"


@boost(BoosterParams(queue_name=f"my_task_mem_v2_{_ts}", broker_kind=BrokerEnum.MEMORY_QUEUE, qps=10))
def my_task_mem(url):
    return my_task(url)


@boost(BoosterParams(queue_name=f"my_task_sqlite_v2_{_ts}", broker_kind=BrokerEnum.SQLITE_QUEUE, qps=10))
def my_task_sqlite(url):
    return my_task(url)


def process_item(item):
    return item * 2


if __name__ == "__main__":
    my_task_mem.consume()
    my_task_sqlite.consume()
    my_task_mem.push("http://local")
    my_task_sqlite.push("http://remote")

    pool_dev = MemoryFunboostPool(concurrent_num=10, qps=5)
    f1 = pool_dev.submit(process_item, 3)
    assert f1.result(timeout=10) == 6

    pool_prod = FunboostPool(
        BoosterParams(
            queue_name=f"pool_v2_{_ts}",
            broker_kind=BrokerEnum.MEMORY_QUEUE,
            concurrent_num=10,
            qps=5,
        ),
        is_need_result=True,
    )
    f2 = pool_prod.submit(process_item, 4)
    assert f2.result(timeout=10) == 8

    print("[PASS] broker switch pattern")
    time.sleep(15)
    os._exit(66)
