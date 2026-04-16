

import datetime
from funboost import boost, BoosterParams, TaskOptions, BrokerEnum


# 定义延时任务（使用专用延时队列）
@boost(BoosterParams(queue_name="delay_add", broker_kind=BrokerEnum.REDIS_ZSET_DELAY))
def add(x, y):
    print(f"{x} + {y} = {x + y}")



if __name__ == '__main__':
    # 启动消费
    add.consume()

    # 1. 相对延时（60秒后执行 3+5）
    add.publish(
        {"x": 3, "y": 5},
        task_options=TaskOptions(
            other_extra_params={
                'for_broker_redis_zset_delay': {'delay_seconds': 20}
            }
        )
    )

    # 2. 绝对定时（2026年10月1日 08:00:00 执行 10+20）
    target_time = datetime.datetime(2026, 4, 16, 11, 49, 40)
    eta_timestamp = target_time.timestamp()

    add.publish(
        {"x": 10, "y": 20},
        task_options=TaskOptions(
            other_extra_params={
                'for_broker_redis_zset_delay': {'eta_timestamp': eta_timestamp}
            }
        )
    )
    