"""round3 验证 using-funboost-basics 示例2: Redis 任务配置（broker 改用 MEMORY_QUEUE）"""
import os
import time

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
_ts = int(time.time())
os.environ["PRINT_WRTIE_FILE_NAME"] = f"r3_basics_02_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"r3_basics_02_std_{_ts}"

from funboost import boost, BoosterParams, BrokerEnum


@boost(BoosterParams(
    queue_name="my_task_queue",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    concurrent_num=30,
    qps=10,
    max_retry_times=3,
    log_level=20,
))
def my_task(url: str, depth: int = 1):
    """你的业务逻辑——保持为普通函数"""
    print(f"[OK] my_task url={url}, depth={depth}, status=200")
    return 200


if __name__ == "__main__":
    for i in range(5):
        my_task.push(f"https://example.com/page/{i}", depth=2)
    my_task.consume()
    import time, os
    time.sleep(12)
    os._exit(66)
