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
from funboost.constant import RedisKeys

logger = logger_notify

alert_bp = Blueprint('queue_alerts', __name__)

_redis = RedisMixin().redis_db_frame

_RULES_KEY = 'funboost:funweb:alert:rules'
_ALERT_LOG_KEY = 'funboost:funweb:alert:log'
_ALERT_LOG_MAX = 500
_ALERT_LOG_TTL = 30 * 24 * 3600

_DEFAULT_CHECK_WINDOW_COUNT = 3


class AlertRuleStore:
    """告警规则存储管理器，封装规则的 CRUD 操作"""

    def __init__(self, redis_client=None):
        self._redis = redis_client or _redis

    @staticmethod
    def gen_id():
        return str(uuid.uuid4())[:8]

    def load_all(self):
        raw = self._redis.hgetall(_RULES_KEY)
        rules = []
        for k, v in raw.items():
            try:
                rule = json.loads(v.decode() if isinstance(v, bytes) else v)
                rule['_id'] = k.decode() if isinstance(k, bytes) else k
                rules.append(rule)
            except (json.JSONDecodeError, TypeError):
                pass
        return rules

    def get(self, rule_id):
        raw = self._redis.hget(_RULES_KEY, rule_id)
        if not raw:
            return None
        try:
            return json.loads(raw.decode() if isinstance(raw, bytes) else raw)
        except (json.JSONDecodeError, TypeError):
            return None

    def save(self, rule_id, rule_dict):
        self._redis.hset(_RULES_KEY, rule_id, json.dumps(rule_dict, ensure_ascii=False))

    def delete(self, rule_id):
        self._redis.hdel(_RULES_KEY, rule_id)


class AlertLogStore:
    """告警日志存储管理器"""

    def __init__(self, redis_client=None):
        self._redis = redis_client or _redis

    def append(self, entry):
        ts = time.time()
        entry['ts'] = ts
        member = json.dumps(entry, ensure_ascii=False)
        self._redis.zadd(_ALERT_LOG_KEY, {member: ts})
        self._redis.zremrangebyrank(_ALERT_LOG_KEY, 0, -(_ALERT_LOG_MAX + 50))
        self._redis.expire(_ALERT_LOG_KEY, _ALERT_LOG_TTL)

    def query(self, start_ts, end_ts, limit=200):
        raw_list = self._redis.zrevrangebyscore(_ALERT_LOG_KEY, end_ts, start_ts)
        logs = []
        for raw in raw_list[:limit]:
            try:
                logs.append(json.loads(raw.decode() if isinstance(raw, bytes) else raw))
            except (json.JSONDecodeError, TypeError):
                pass
        return logs


_rule_store = AlertRuleStore()
_log_store = AlertLogStore()


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


class TimeSeriesEvaluator:
    """
    通用时序数据评估器，不依赖告警规则。
    实例化时传入 queue_name 和 count，自动从 Redis 时序数据中读取。
    所有 evaluate_* 方法返回 (triggered: bool, detail: str)。
    可被告警系统、Dashboard 健康检查、API 等复用。

    用法：
        evaluator = TimeSeriesEvaluator('my_queue', count=3)
        triggered, detail = evaluator.evaluate_backlog(threshold=100)
    """

    def __init__(self, queue_name, count=3):
        self.queue_name = queue_name
        self.count = count
        self.series = self._fetch_series(queue_name, count)

    @staticmethod
    def _fetch_series(queue_name, count):
        key = RedisKeys.gen_funboost_queue_time_series_data_key_by_queue_name(queue_name)
        raw_list = _redis.zrevrange(key, 0, count - 1)
        series = []
        for raw in raw_list:
            try:
                data = json.loads(raw.decode() if isinstance(raw, bytes) else raw)
                series.append(data)
            except (json.JSONDecodeError, TypeError):
                pass
        return series

    def evaluate_backlog(self, threshold=0):
        """积压告警：窗口内全部超阈值才触发"""
        if not self.series:
            return False, ''
        for s in self.series:
            backlog = s.get('msg_num_in_broker', 0) or 0
            if backlog < threshold:
                return False, ''
        latest = self.series[0].get('msg_num_in_broker', 0) or 0
        n = len(self.series)
        return True, f'积压 {latest} >= {threshold}（连续 {n} 个周期/{n * 10}s）'

    def evaluate_qps_drop(self, threshold=0):
        """QPS 骤降：平均 QPS <= 阈值且有消费者在线"""
        if not self.series:
            return False, ''
        has_consumer = any(s.get('active_consumer_count', 0) > 0 for s in self.series)
        if not has_consumer:
            return False, ''
        counts = [s.get('all_consumers_last_x_s_execute_count', 0) or 0 for s in self.series]
        avg_qps = sum(c / 10.0 for c in counts) / len(counts)
        if avg_qps <= threshold:
            n = len(self.series)
            return True, f'平均QPS={avg_qps:.1f} <= {threshold}（近 {n} 个周期/{n * 10}s）'
        return False, ''

    def evaluate_consumer_lost(self, now=0):
        """
        消费者掉线：
        1. 先检查最新时序数据是否已过期（采集线程在 active_consumer_count==0 时不存数据，
           所以消费者全停后时序数据会停止更新，需通过 report_ts 检测）
        2. 再检查窗口内 active_consumer_count 是否全部为 0（兼容旧数据或采集逻辑变更后）
        """
        if now <= 0:
            return False, ''
        if self.series:
            latest_ts = self.series[0].get('report_ts', 0)
            if latest_ts and now - latest_ts > 60:
                return True, f'无活跃消费者（时序数据已停止更新 {int(now - latest_ts)}s）'
            all_lost = all(s.get('active_consumer_count', 0) == 0 for s in self.series)
            if all_lost:
                n = len(self.series)
                return True, f'无活跃消费者（连续 {n} 个周期/{n * 10}s）'
            return False, ''
        return False, ''

    def evaluate_fail_spike(self, threshold=0, min_calls=5):
        """失败率飙升：汇总近 N 个周期的总成功/失败数计算失败率"""
        if not self.series:
            return False, ''
        total_exec = sum(s.get('all_consumers_last_x_s_execute_count', 0) or 0 for s in self.series)
        total_fail = sum(s.get('all_consumers_last_x_s_execute_count_fail', 0) or 0 for s in self.series)
        total = total_exec
        if total < min_calls or total == 0:
            return False, ''
        fail_rate = total_fail / total
        fail_threshold = threshold / 100.0
        if fail_rate >= fail_threshold:
            n = len(self.series)
            return True, f'失败率 {fail_rate:.0%} >= {fail_threshold:.0%}（近 {n} 个周期/{n * 10}s 共 {total} 次调用）'
        return False, ''

    def evaluate_avg_time_high(self, threshold=0):
        """耗时过高：近 N 个周期的平均耗时 >= 阈值"""
        if not self.series:
            return False, ''
        times = [s.get('all_consumers_last_x_s_avarage_function_spend_time') for s in self.series]
        valid = [t for t in times if t is not None]
        if not valid:
            return False, ''
        avg_time = sum(valid) / len(valid)
        if avg_time >= threshold:
            n = len(self.series)
            return True, f'平均耗时 {avg_time:.1f}s >= {threshold}s（近 {n} 个周期/{n * 10}s）'
        return False, ''


def _check_rules_once():
    rules = _rule_store.load_all()
    if not rules:
        return

    enabled_rules = [r for r in rules if r.get('enabled', True)]
    if not enabled_rules:
        return

    now = time.time()
    now_str = time.strftime('%Y-%m-%d %H:%M:%S')

    try:
        getter = QueuesConusmerParamsGetter()
        all_queue_names = sorted(getter.get_queues_params().keys())
    except Exception as e:
        logger.error(f'FunboostAlert get queue names failed: {e}')
        return

    evaluator_cache = {}

    for rule in enabled_rules:
        rule_id = rule['_id']
        alert_type = rule.get('alert_type', 'backlog')
        queue_name_raw = rule.get('queue_name', '*')
        rule_queue_names = [q.strip() for q in queue_name_raw.split(',') if q.strip()] if queue_name_raw != '*' else ['*']
        threshold = rule.get('threshold', 0)
        alert_interval = rule.get('alert_interval', 300)
        alert_app = rule.get('alert_app', 'wechat')
        webhook_url = rule.get('webhook_url', '')
        check_window = rule.get('check_window_count', _DEFAULT_CHECK_WINDOW_COUNT)
        min_calls = rule.get('min_calls', 5)

        target_queues = all_queue_names if '*' in rule_queue_names else [q for q in rule_queue_names if q in all_queue_names]

        for q_name in target_queues:
            cache_key = (q_name, check_window)
            if cache_key not in evaluator_cache:
                evaluator_cache[cache_key] = TimeSeriesEvaluator(q_name, count=check_window)
            ev = evaluator_cache[cache_key]

            triggered = False
            detail = ''

            if alert_type == 'backlog':
                triggered, detail = ev.evaluate_backlog(threshold=threshold)
            elif alert_type == 'qps_drop':
                triggered, detail = ev.evaluate_qps_drop(threshold=threshold)
            elif alert_type == 'consumer_lost':
                triggered, detail = ev.evaluate_consumer_lost(now=now)
            elif alert_type == 'fail_spike':
                triggered, detail = ev.evaluate_fail_spike(threshold=threshold, min_calls=min_calls)
            elif alert_type == 'avg_time_high':
                triggered, detail = ev.evaluate_avg_time_high(threshold=threshold)

            if triggered:
                detail = f'队列 {q_name} {detail}'

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

                _log_store.append({
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
    rules = _rule_store.load_all()
    return jsonify({'succ': True, 'data': rules})


@alert_bp.route('/alert/rules', methods=['POST'])
@login_required
def add_rule():
    data = request.get_json(force=True)
    rule_id = _rule_store.gen_id()
    rule = {
        'rule_name': data.get('rule_name', ''),
        'queue_name': data.get('queue_name', '*'),
        'alert_type': data.get('alert_type', 'backlog'),
        'threshold': data.get('threshold', 0),
        'min_calls': data.get('min_calls', 5),
        'check_window_count': data.get('check_window_count', _DEFAULT_CHECK_WINDOW_COUNT),
        'alert_app': data.get('alert_app', 'wechat'),
        'webhook_url': data.get('webhook_url', ''),
        'alert_interval': data.get('alert_interval', 300),
        'enabled': data.get('enabled', True),
    }
    _rule_store.save(rule_id, rule)
    return jsonify({'succ': True, 'data': {'_id': rule_id, **rule}})


@alert_bp.route('/alert/rules/<rule_id>', methods=['PUT'])
@login_required
def update_rule(rule_id):
    data = request.get_json(force=True)
    rule = _rule_store.get(rule_id)
    if not rule:
        return jsonify({'succ': False, 'error': '规则不存在'}), 404
    for k in ('rule_name', 'queue_name', 'alert_type', 'threshold', 'min_calls',
              'check_window_count', 'alert_app', 'webhook_url', 'alert_interval', 'enabled'):
        if k in data:
            rule[k] = data[k]
    _rule_store.save(rule_id, rule)
    return jsonify({'succ': True, 'data': {'_id': rule_id, **rule}})


@alert_bp.route('/alert/rules/<rule_id>', methods=['DELETE'])
@login_required
def delete_rule(rule_id):
    _rule_store.delete(rule_id)
    return jsonify({'succ': True})


@alert_bp.route('/alert/rules/<rule_id>/toggle', methods=['POST'])
@login_required
def toggle_rule(rule_id):
    rule = _rule_store.get(rule_id)
    if not rule:
        return jsonify({'succ': False, 'error': '规则不存在'}), 404
    rule['enabled'] = not rule.get('enabled', True)
    _rule_store.save(rule_id, rule)
    return jsonify({'succ': True, 'data': {'_id': rule_id, **rule}})


@alert_bp.route('/alert/log', methods=['GET'])
@login_required
def get_alert_log():
    now = time.time()
    start_ts = float(request.args.get('start_ts', now - 7 * 24 * 3600))
    end_ts = float(request.args.get('end_ts', now))
    logs = _log_store.query(start_ts, end_ts)
    return jsonify({'succ': True, 'data': logs})


@alert_bp.route('/alert/queues', methods=['GET'])
@login_required
def get_queue_names():
    try:
        getter = QueuesConusmerParamsGetter()
        queue_names = sorted(getter.get_queues_params().keys())
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
