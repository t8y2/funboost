# -*- coding: utf-8 -*-
import json
import os
import time
import uuid
import threading

from flask import Blueprint, request, jsonify
from flask_login import login_required

from funboost.utils.redis_manager import RedisMixin
from funboost.utils.notify_util import Notifier
from funboost.core.active_cousumer_info_getter import QueuesConusmerParamsGetter
from funboost.funweb.flask_bps.web_helper import LOCAL_IP
from funboost.core.loggers import logger_notify

logger = logger_notify

alert_bp = Blueprint('queue_alerts', __name__)

_redis = RedisMixin().redis_db_frame

_RULES_KEY = 'funboost:funweb:alert:rules'
_ALERT_LOG_KEY = 'funboost:funweb:alert:log'
_ALERT_LOG_MAX = 500
_ALERT_LOG_TTL = 30 * 24 * 3600


def _gen_rule_id():
    return str(uuid.uuid4())[:8]


def _load_rules():
    raw = _redis.hgetall(_RULES_KEY)
    rules = []
    for k, v in raw.items():
        try:
            rule = json.loads(v.decode() if isinstance(v, bytes) else v)
            rule['_id'] = k.decode() if isinstance(k, bytes) else k
            rules.append(rule)
        except (json.JSONDecodeError, TypeError):
            pass
    return rules


def _save_rule(rule_id, rule_dict):
    _redis.hset(_RULES_KEY, rule_id, json.dumps(rule_dict, ensure_ascii=False))


def _delete_rule(rule_id):
    _redis.hdel(_RULES_KEY, rule_id)


def _append_alert_log(entry):
    ts = time.time()
    entry['ts'] = ts
    member = json.dumps(entry, ensure_ascii=False)
    _redis.zadd(_ALERT_LOG_KEY, {member: ts})
    _redis.zremrangebyrank(_ALERT_LOG_KEY, 0, -(_ALERT_LOG_MAX + 50))
    _redis.expire(_ALERT_LOG_KEY, _ALERT_LOG_TTL)


def _send_notification(alert_app, webhook_url, message):
    try:
        notifier_kwargs = {}
        if alert_app == 'dingtalk':
            notifier_kwargs['dingtalk_webhook'] = webhook_url
        elif alert_app == 'wechat':
            notifier_kwargs['wechat_webhook'] = webhook_url
        elif alert_app == 'feishu':
            notifier_kwargs['feishu_webhook'] = webhook_url
        notifier = Notifier(**notifier_kwargs)

        if alert_app == 'dingtalk':
            notifier.send_dingtalk(message, add_caller_info=False)
        elif alert_app == 'wechat':
            notifier.send_wechat(message, add_caller_info=False)
        elif alert_app == 'feishu':
            notifier.send_feishu(message, add_caller_info=False)
        elif alert_app == 'webhook' and webhook_url:
            import requests
            requests.post(webhook_url, headers={'Content-Type': 'application/json'},
                          data=json.dumps({'content': message}), timeout=10)
    except Exception as e:
        logger.error(f'FunboostAlert send notification failed: {e}')


def _check_rules_once():
    rules = _load_rules()
    if not rules:
        return

    enabled_rules = [r for r in rules if r.get('enabled', True)]
    if not enabled_rules:
        return

    try:
        getter = QueuesConusmerParamsGetter()
        queues_info = getter.get_queues_params_and_active_consumers()
    except Exception as e:
        logger.error(f'FunboostAlert get queues info failed: {e}')
        return

    now = time.time()
    now_str = time.strftime('%Y-%m-%d %H:%M:%S')

    for rule in enabled_rules:
        rule_id = rule['_id']
        alert_type = rule.get('alert_type', 'backlog')
        queue_name_raw = rule.get('queue_name', '*')
        rule_queue_names = [q.strip() for q in queue_name_raw.split(',') if q.strip()] if queue_name_raw != '*' else ['*']
        threshold = rule.get('threshold', 0)
        alert_interval = rule.get('alert_interval', 300)
        alert_app = rule.get('alert_app', 'wechat')
        webhook_url = rule.get('webhook_url', '')

        for q_name, info in queues_info.items():
            if '*' not in rule_queue_names and q_name not in rule_queue_names:
                continue

            triggered = False
            detail = ''

            if alert_type == 'backlog':
                backlog = info.get('msg_num_in_broker', 0) or 0
                if backlog >= threshold:
                    triggered = True
                    detail = f'队列 {q_name} 积压 {backlog} >= {threshold}'

            elif alert_type == 'qps_drop':
                last_x_s_count = info.get('all_consumers_last_x_s_execute_count', 0) or 0
                consumers = info.get('active_consumers', [])
                if len(consumers) > 0 and last_x_s_count > 0:
                    qps = last_x_s_count / 10.0
                    if qps <= threshold:
                        triggered = True
                        detail = f'队列 {q_name} QPS={qps:.1f} <= {threshold} (近10秒执行{last_x_s_count}次, {len(consumers)}个消费者)'
                elif len(consumers) > 0 and last_x_s_count == 0 and threshold >= 0:
                    triggered = True
                    detail = f'队列 {q_name} QPS=0 <= {threshold} (近10秒无执行, {len(consumers)}个消费者)'

            elif alert_type == 'consumer_lost':
                consumers = info.get('active_consumers', [])
                if len(consumers) == 0:
                    triggered = True
                    detail = f'队列 {q_name} 无活跃消费者!'

            elif alert_type == 'fail_spike':
                qps = info.get('all_consumers_last_x_s_execute_count', 0) or 0
                qps_fail = info.get('all_consumers_last_x_s_execute_count_fail', 0) or 0
                total = qps + qps_fail
                min_calls = rule.get('min_calls', 5)
                if total >= min_calls and total > 0:
                    fail_rate = qps_fail / total
                    fail_threshold = threshold / 100.0
                    if fail_rate >= fail_threshold:
                        triggered = True
                        detail = f'队列 {q_name} 失败率 {fail_rate:.0%} >= {fail_threshold:.0%} (近{total}次调用)'

            elif alert_type == 'avg_time_high':
                avg_time = info.get('all_consumers_last_x_s_avarage_function_spend_time') or 0
                if avg_time >= threshold:
                    triggered = True
                    detail = f'队列 {q_name} 平均耗时 {avg_time:.1f}s >= {threshold}s'

            if triggered:
                last_alert_ts_key = f'funboost:funweb:alert:last:{rule_id}:{q_name}'
                last_ts = _redis.get(last_alert_ts_key)
                if last_ts and now - float(last_ts) < alert_interval:
                    continue

                _redis.set(last_alert_ts_key, str(now), ex=alert_interval * 2)

                message = '\n'.join([
                    '🚨 [Funboost 告警]',
                    detail,
                    f'告警时间: {now_str}',
                    f'告警规则: {rule.get("rule_name", rule_id)}',
                    f'告警来源: {LOCAL_IP} (PID: {os.getpid()})',
                ])
                _send_notification(alert_app, webhook_url, message)

                _append_alert_log({
                    'rule_id': rule_id,
                    'rule_name': rule.get('rule_name', ''),
                    'queue_name': q_name,
                    'alert_type': alert_type,
                    'detail': detail,
                    'time': now_str,
                    'status': 'alerting',
                })
                logger.warning(f'FunboostAlert triggered: {detail}')


def _checker_loop():
    while True:
        try:
            _check_rules_once()
        except Exception as e:
            logger.error(f'FunboostAlert checker error: {e}')
        time.sleep(10)


_checker_thread = threading.Thread(target=_checker_loop, daemon=True)
_checker_thread.start()


@alert_bp.route('/alert/rules', methods=['GET'])
@login_required
def get_rules():
    rules = _load_rules()
    return jsonify({'succ': True, 'data': rules})


@alert_bp.route('/alert/rules', methods=['POST'])
@login_required
def add_rule():
    data = request.get_json(force=True)
    rule_id = _gen_rule_id()
    rule = {
        'rule_name': data.get('rule_name', ''),
        'queue_name': data.get('queue_name', '*'),
        'alert_type': data.get('alert_type', 'backlog'),
        'threshold': data.get('threshold', 0),
        'min_calls': data.get('min_calls', 5),
        'alert_app': data.get('alert_app', 'wechat'),
        'webhook_url': data.get('webhook_url', ''),
        'alert_interval': data.get('alert_interval', 300),
        'enabled': data.get('enabled', True),
    }
    _save_rule(rule_id, rule)
    return jsonify({'succ': True, 'data': {'_id': rule_id, **rule}})


@alert_bp.route('/alert/rules/<rule_id>', methods=['PUT'])
@login_required
def update_rule(rule_id):
    data = request.get_json(force=True)
    raw = _redis.hget(_RULES_KEY, rule_id)
    if not raw:
        return jsonify({'succ': False, 'error': '规则不存在'}), 404
    rule = json.loads(raw.decode() if isinstance(raw, bytes) else raw)
    for k in ('rule_name', 'queue_name', 'alert_type', 'threshold', 'min_calls',
              'alert_app', 'webhook_url', 'alert_interval', 'enabled'):
        if k in data:
            rule[k] = data[k]
    _save_rule(rule_id, rule)
    return jsonify({'succ': True, 'data': {'_id': rule_id, **rule}})


@alert_bp.route('/alert/rules/<rule_id>', methods=['DELETE'])
@login_required
def delete_rule(rule_id):
    _delete_rule(rule_id)
    return jsonify({'succ': True})


@alert_bp.route('/alert/rules/<rule_id>/toggle', methods=['POST'])
@login_required
def toggle_rule(rule_id):
    raw = _redis.hget(_RULES_KEY, rule_id)
    if not raw:
        return jsonify({'succ': False, 'error': '规则不存在'}), 404
    rule = json.loads(raw.decode() if isinstance(raw, bytes) else raw)
    rule['enabled'] = not rule.get('enabled', True)
    _save_rule(rule_id, rule)
    return jsonify({'succ': True, 'data': {'_id': rule_id, **rule}})


@alert_bp.route('/alert/log', methods=['GET'])
@login_required
def get_alert_log():
    now = time.time()
    start_ts = float(request.args.get('start_ts', now - 7 * 24 * 3600))
    end_ts = float(request.args.get('end_ts', now))
    raw_list = _redis.zrevrangebyscore(_ALERT_LOG_KEY, end_ts, start_ts)
    logs = []
    for raw in raw_list[:200]:
        try:
            logs.append(json.loads(raw.decode() if isinstance(raw, bytes) else raw))
        except (json.JSONDecodeError, TypeError):
            pass
    return jsonify({'succ': True, 'data': logs})


@alert_bp.route('/alert/queues', methods=['GET'])
@login_required
def get_queue_names():
    try:
        getter = QueuesConusmerParamsGetter()
        queues_info = getter.get_queues_params_and_active_consumers()
        queue_names = sorted(queues_info.keys())
        return jsonify({'succ': True, 'data': queue_names})
    except Exception as e:
        return jsonify({'succ': False, 'error': str(e)})


@alert_bp.route('/alert/test_notify', methods=['POST'])
@login_required
def test_notify():
    data = request.get_json(force=True)
    alert_app = data.get('alert_app', 'wechat')
    webhook_url = data.get('webhook_url', '')
    message = f'🔔 [测试] Funboost 告警通知测试 - 如果您看到此消息，说明通知通道配置正确。\n告警来源: {LOCAL_IP} (PID: {os.getpid()})'
    try:
        _send_notification(alert_app, webhook_url, message)
        return jsonify({'succ': True})
    except Exception as e:
        return jsonify({'succ': False, 'error': str(e)})
