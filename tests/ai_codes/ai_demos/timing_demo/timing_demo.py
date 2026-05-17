"""
定时任务 demo: 使用 ApsJobAdder 调度 interval 任务
"""
import os
import time

os.environ["LOG_PATH"] = 'd:/pythonlogs/ai_console_outs'
os.environ['PRINT_WRTIE_FILE_NAME'] = 'timing_demo_print_20260516.print'
os.environ['SYS_STD_FILE_NAME'] = 'timing_demo_std_20260516.std'

from funboost import boost, BrokerEnum, BoosterParams, ApsJobAdder


@boost(BoosterParams(
    queue_name="test_timing_queue_v1",
    broker_kind=BrokerEnum.REDIS_ACK_ABLE,
    concurrent_num=10,
))
def sum_task(x, y):
    result = x + y
    print(f"定时任务执行: {x} + {y} = {result}")
    return result


if __name__ == '__main__':
    ApsJobAdder(sum_task, job_store_kind='memory').add_push_job(
        trigger='interval',
        seconds=3,
        args=(1, 2),
        id='job_every_3s',
        replace_existing=True,
    )

    ApsJobAdder(sum_task, job_store_kind='memory').add_push_job(
        trigger='interval',
        seconds=5,
        kwargs={"x": 10, "y": 20},
        id='job_every_5s',
        replace_existing=True,
    )

    print("定时调度器已启动，开始消费消息...")
    sum_task.consume()

    time.sleep(18)
    print("18秒到了，退出程序")
    os._exit(66)
