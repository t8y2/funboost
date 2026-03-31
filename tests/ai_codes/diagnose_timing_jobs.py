# -*- coding: utf-8 -*-
"""
定时任务诊断脚本 - 检查 APScheduler Redis JobStore 状态
"""

from funboost.core.active_cousumer_info_getter import SingleQueueConusmerParamsGetter, QueuesConusmerParamsGetter
from funboost.timing_job.timing_push import ApsJobAdder
from funboost.utils import redis_manager
from funboost.constant import RedisKeys
import json

def diagnose_timing_jobs(queue_name=None):
    """诊断定时任务状态"""
    
    print("="*60)
    print("定时任务诊断报告")
    print("="*60)
    
    # 1. 检查所有队列
    all_queues = list(QueuesConusmerParamsGetter().get_all_queue_names())
    print(f"\n📋 已注册的队列数量: {len(all_queues)}")
    print(f"队列列表: {all_queues}")
    
    # 2. 检查 Redis 中的任务
    redis_conn = redis_manager.get_redis_connection()
    
    if queue_name:
        queues_to_check = [queue_name]
    else:
        queues_to_check = all_queues
    
    print(f"\n🔍 检查队列: {queues_to_check}\n")
    
    for q_name in queues_to_check:
        print(f"\n{'─'*60}")
        print(f"队列: {q_name}")
        print(f"{'─'*60}")
        
        # 检查 Redis 中的 jobs_key
        jobs_key = RedisKeys.gen_funboost_redis_apscheduler_jobs_key_by_queue_name(q_name)
        run_times_key = RedisKeys.gen_funboost_redis_apscheduler_run_times_key_by_queue_name(q_name)
        lock_key = RedisKeys.gen_funboost_apscheduler_redis_lock_key_by_queue_name(q_name)
        
        print(f"📌 Redis Keys:")
        print(f"   Jobs Key: {jobs_key}")
        print(f"   Run Times Key: {run_times_key}")
        print(f"   Lock Key: {lock_key}")
        
        # 检查 Redis 中是否有任务
        jobs_in_redis = redis_conn.hgetall(jobs_key)
        run_times_in_redis = redis_conn.zrange(run_times_key, 0, -1, withscores=True)
        
        print(f"\n📊 Redis 存储状态:")
        print(f"   Jobs 数量: {len(jobs_in_redis)}")
        print(f"   Run Times 数量: {len(run_times_in_redis)}")
        
        if jobs_in_redis:
            print(f"\n   Jobs 详情:")
            for job_id, job_data in jobs_in_redis.items():
                print(f"     - Job ID: {job_id.decode() if isinstance(job_id, bytes) else job_id}")
                try:
                    import pickle
                    job_obj = pickle.loads(job_data)
                    print(f"       触发器: {job_obj.trigger}")
                    print(f"       下次执行: {job_obj.next_run_time}")
                except Exception as e:
                    print(f"       (无法解析: {e})")
        
        # 3. 检查通过 ApsJobAdder 能否获取任务
        try:
            booster = SingleQueueConusmerParamsGetter(q_name).gen_booster_for_faas()
            job_adder = ApsJobAdder(booster, job_store_kind='redis', is_auto_start=True)
            
            jobs = job_adder.aps_obj.get_jobs()
            
            print(f"\n🔄 APScheduler 获取的任务:")
            print(f"   任务数量: {len(jobs)}")
            
            for job in jobs:
                print(f"\n   ➤ Job ID: {job.id}")
                print(f"     触发器: {job.trigger}")
                print(f"     下次执行: {job.next_run_time}")
                print(f"     状态: {'已暂停' if job.next_run_time is None else '运行中'}")
                if hasattr(job, 'kwargs') and job.kwargs:
                    print(f"     参数: {job.kwargs}")
            
            # 检查调度器状态
            print(f"\n⚙️  APScheduler 状态:")
            print(f"   是否运行: {job_adder.aps_obj.running}")
            print(f"   State: {job_adder.aps_obj.state}")
            
        except Exception as e:
            print(f"\n❌ 获取任务失败: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'='*60}")
    print("诊断完成")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    # 诊断所有队列
    diagnose_timing_jobs()
    
    # 或者诊断指定队列
    # diagnose_timing_jobs('test_funboost_task3')
