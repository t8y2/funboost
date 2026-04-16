import time
from funboost import FunboostPool, concurrent_pool

from funboost import BoosterParams, BrokerEnum,ConcurrentModeEnum
from funboost import RedisMixin


import os

from funboost.core import broker_kind__exclusive_config_default_define

redis_key_pids_process_data = 'pids_process_data'
RedisMixin().redis_db_frame.delete(redis_key_pids_process_data)

def process_data(data_id):
    RedisMixin().redis_db_frame.sadd(redis_key_pids_process_data, os.getpid())
    return f"处理结果: {data_id}"

# 配置 Redis 分布式任务池
params = BoosterParams(
    queue_name="distributed_pool",
    broker_kind=BrokerEnum.REDIS_ACK_ABLE,  # 使用 Redis 作为消息队列
    # concurrent_num=10,
    concurrent_mode=ConcurrentModeEnum.SOLO,
    qps=5,
    max_retry_times=3,
    # do_task_filtering=True
    publish_msg_log_use_full_msg = True,
    broker_exclusive_config = {
         "pull_msg_batch_size": 1,
    }
)

pool = FunboostPool(params, is_need_result=True, is_auto_start_consuming_message=False)

if __name__ == "__main__":
    pool.booster.mp_consume(2)
    
    time.sleep(10)
    for i in range(100):
        future = pool.submit(process_data, i)
        # print(future.result()) # 即使用分布式中间件，结果也能通过 future.result()来获取。

    # 此时任务已发布到 Redis，可由任意数量的消费者进程共同处理
    time.sleep(10)
    print(RedisMixin().redis_db_frame.smembers(redis_key_pids_process_data))
