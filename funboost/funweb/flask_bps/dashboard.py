# -*- coding: utf-8 -*-
import json
import traceback

from flask import Blueprint, jsonify
from flask_login import login_required

from funboost.utils.redis_manager import RedisMixin
from funboost.core.active_cousumer_info_getter import QueuesConusmerParamsGetter

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/api/dashboard/summary')
@login_required
def dashboard_summary():
    """
    Dashboard 聚合接口，返回全局概览数据：
    - 队列总数、活跃消费者数、总消息积压量
    - 各队列积压 Top N
    - 系统资源快照（CPU/内存/磁盘）
    - 消费者心跳汇总
    """
    try:
        result = _build_summary()
        return jsonify({'succ': True, 'data': result})
    except Exception as e:
        return jsonify({'succ': False, 'error': str(e), 'traceback': traceback.format_exc()})


def _build_summary():
    data = {}

    getter = QueuesConusmerParamsGetter()
    queues_and_consumers = getter.get_queues_params_and_active_consumers()

    total_queues = len(queues_and_consumers)
    total_consumers = 0
    consumer_ips = set()
    queue_backlog_list = []
    queue_throughput_list = []

    for queue_name, info in queues_and_consumers.items():
        active_consumers = info.get('active_consumers', [])
        for consumer_info in active_consumers:
            total_consumers += 1
            ip = consumer_info.get('computer_ip', '')
            if ip:
                consumer_ips.add(ip)

        backlog = info.get('msg_num_in_broker', 0) or 0
        qps = info.get('all_consumers_last_x_s_execute_count', 0) or 0
        qps_fail = info.get('all_consumers_last_x_s_execute_count_fail', 0) or 0

        queue_backlog_list.append({
            'queue_name': queue_name,
            'backlog': backlog,
        })
        queue_throughput_list.append({
            'queue_name': queue_name,
            'qps': qps,
            'qps_fail': qps_fail,
            'total_run': info.get('history_run_count', 0) or 0,
            'total_fail': info.get('history_run_fail_count', 0) or 0,
            'avg_time': info.get('all_consumers_avarage_function_spend_time_from_start', 0) or 0,
        })

    queue_backlog_list.sort(key=lambda x: x['backlog'], reverse=True)
    queue_throughput_list.sort(key=lambda x: x['qps'], reverse=True)

    total_backlog = sum(item['backlog'] for item in queue_backlog_list)
    total_qps = sum(item['qps'] for item in queue_throughput_list)

    data['total_queues'] = total_queues
    data['total_consumers'] = total_consumers
    data['total_consumer_ips'] = len(consumer_ips)
    data['total_backlog'] = total_backlog
    data['total_qps'] = total_qps
    data['queue_backlog_top'] = queue_backlog_list[:15]
    data['queue_throughput_top'] = queue_throughput_list[:15]

    # 系统资源（复用 system_monitor 的 Redis 数据）
    data['system_resources'] = _get_system_resources()

    return data


def _get_system_resources():
    """
    从 Redis 获取最近一次系统资源监控数据。
    通过 FUNBOOST_ALL_IPS Set 获取 IP 列表（O(N) 仅限已知 IP），
    再逐个获取 funboost:funweb:monitor:{ip}:metrics 的最新数据，避免 SCAN 全库。
    """
    resources = []
    try:
        redis_client = RedisMixin().redis_db_frame
        from funboost.constant import RedisKeys
        from funboost.funweb.flask_bps.web_helper import LOCAL_IP

        # 从已知 IP 集合获取候选列表，加上本机 IP
        ips = set(redis_client.smembers(RedisKeys.FUNBOOST_ALL_IPS))
        ips.add(LOCAL_IP)

        for ip_raw in ips:
            ip = ip_raw.decode() if isinstance(ip_raw, bytes) else ip_raw
            zkey = f'funboost:funweb:monitor:{ip}:metrics'
            items = redis_client.zrevrange(zkey, 0, 0, withscores=True)
            if not items:
                continue
            raw, ts = items[0]
            try:
                entry = json.loads(raw.decode() if isinstance(raw, bytes) else raw)
                entry['ip'] = ip
                entry['ts'] = ts
                resources.append(entry)
            except Exception:
                pass
    except Exception:
        pass
    return resources
