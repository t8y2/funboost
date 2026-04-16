import time
from funboost import FunboostPool

from funboost import BoosterParams, BrokerEnum

def process_data(data_id):
    return f"处理结果: {data_id}"

# 配置 Redis 分布式任务池
params = BoosterParams(
    queue_name="distributed_pool",
    broker_kind=BrokerEnum.REDIS_ACK_ABLE,  # 使用 Redis 作为消息队列
    concurrent_num=10,
    qps=50,
    max_retry_times=3,
    # do_task_filtering=True
    publish_msg_log_use_full_msg = True,
)

pool = FunboostPool(params, is_need_result=True)

if __name__ == "__main__":

    for i in range(10):
        future = pool.submit(process_data, i)
        print(future.result()) # 即使用分布式中间件，结果也能通过 future.result()来获取。

    # 此时任务已发布到 Redis，可由任意数量的消费者进程共同处理