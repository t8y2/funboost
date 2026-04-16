import logging
import time
print(111)
from funboost import MemoryFunboostPool,FunboostPool,BoosterParams,BrokerEnum
from funboost.concurrent_pool.flexible_thread_pool import FlexibleThreadPool

print(222)

def add(a, b):
    if a % 10000 == 0:
        print(a)
    return a + b

# 实例化任务池
booster_params = params = BoosterParams(
    queue_name="distributed_pool",
    broker_kind=BrokerEnum.REDIS,  # 使用 Redis 作为消息队列
    concurrent_num=10,
    log_level = logging.INFO,
    # qps=50,
    max_retry_times=3,
    # do_task_filtering=True
)
pool = FunboostPool(booster_params, is_need_result=False)

# ANNOYING_WARNING = "msg 中包含不能json序列化的键:"  # 👈 改成你真实的那句

# # 过滤器：只屏蔽这一条
# pool.booster.publisher.logger.addFilter(lambda record: not (
#     record.levelno == logging.WARNING 
#     and 
#     ANNOYING_WARNING in record.getMessage()
# ))

# pool = FlexibleThreadPool(10)
t1= time.time()

for i  in range(200000):
    pool.submit(add, i,i*2)

print(time.time() - t1)