# -*- coding: utf-8 -*-
"""
回归测试：告警系统 TimeSeriesEvaluator / AlertRuleStore / AlertLogStore
"""
import json
import sys
import os
from unittest.mock import patch, MagicMock, call

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from funboost.funweb.flask_bps.queue_alerts import (
    TimeSeriesEvaluator, AlertRuleStore, AlertLogStore,
)


def _make_series(overrides_list):
    """生成时序数据列表，每项可覆盖默认值"""
    base = {
        'msg_num_in_broker': 0,
        'all_consumers_last_x_s_execute_count': 100,
        'all_consumers_last_x_s_execute_count_fail': 0,
        'all_consumers_last_x_s_avarage_function_spend_time': 0.5,
        'active_consumer_count': 2,
        'report_ts': 1700000000,
    }
    series = []
    for overrides in overrides_list:
        item = dict(base)
        item.update(overrides)
        series.append(item)
    return series


def _mock_evaluator(overrides_list):
    """创建一个 mock 了 Redis 取数的 TimeSeriesEvaluator 实例"""
    series = _make_series(overrides_list)
    with patch.object(TimeSeriesEvaluator, '_fetch_series', return_value=series):
        return TimeSeriesEvaluator('test_queue', count=len(overrides_list))


class TestEvaluateBacklog:
    def test_empty_series(self):
        ev = _mock_evaluator([])
        triggered, _ = ev.evaluate_backlog(threshold=100)
        assert not triggered

    def test_all_over_threshold(self):
        ev = _mock_evaluator([{'msg_num_in_broker': 200}] * 3)
        triggered, detail = ev.evaluate_backlog(threshold=100)
        assert triggered
        assert '200' in detail
        assert '连续 3' in detail
        assert '30s' in detail

    def test_one_below_threshold(self):
        ev = _mock_evaluator([
            {'msg_num_in_broker': 200},
            {'msg_num_in_broker': 50},
            {'msg_num_in_broker': 200},
        ])
        triggered, _ = ev.evaluate_backlog(threshold=100)
        assert not triggered

    def test_exact_threshold(self):
        ev = _mock_evaluator([{'msg_num_in_broker': 100}] * 3)
        triggered, _ = ev.evaluate_backlog(threshold=100)
        assert triggered

    def test_all_zero(self):
        ev = _mock_evaluator([{'msg_num_in_broker': 0}] * 3)
        triggered, _ = ev.evaluate_backlog(threshold=100)
        assert not triggered


class TestEvaluateQpsDrop:
    def test_empty_series(self):
        ev = _mock_evaluator([])
        triggered, _ = ev.evaluate_qps_drop(threshold=5)
        assert not triggered

    def test_no_consumers(self):
        ev = _mock_evaluator([{'active_consumer_count': 0, 'all_consumers_last_x_s_execute_count': 0}] * 3)
        triggered, _ = ev.evaluate_qps_drop(threshold=5)
        assert not triggered

    def test_qps_below_threshold(self):
        ev = _mock_evaluator([{'all_consumers_last_x_s_execute_count': 10}] * 3)
        triggered, detail = ev.evaluate_qps_drop(threshold=5)
        assert triggered
        assert 'QPS=1.0' in detail

    def test_qps_above_threshold(self):
        ev = _mock_evaluator([{'all_consumers_last_x_s_execute_count': 200}] * 3)
        triggered, _ = ev.evaluate_qps_drop(threshold=5)
        assert not triggered

    def test_mixed_with_some_consumers(self):
        ev = _mock_evaluator([
            {'all_consumers_last_x_s_execute_count': 10, 'active_consumer_count': 2},
            {'all_consumers_last_x_s_execute_count': 0, 'active_consumer_count': 0},
            {'all_consumers_last_x_s_execute_count': 20, 'active_consumer_count': 1},
        ])
        triggered, _ = ev.evaluate_qps_drop(threshold=5)
        assert triggered


class TestEvaluateFailSpike:
    def test_empty_series(self):
        ev = _mock_evaluator([])
        triggered, _ = ev.evaluate_fail_spike(threshold=20, min_calls=5)
        assert not triggered

    def test_below_min_calls(self):
        ev = _mock_evaluator([
            {'all_consumers_last_x_s_execute_count': 1, 'all_consumers_last_x_s_execute_count_fail': 1},
        ])
        triggered, _ = ev.evaluate_fail_spike(threshold=20, min_calls=5)
        assert not triggered

    def test_high_fail_rate(self):
        ev = _mock_evaluator([
            {'all_consumers_last_x_s_execute_count': 100, 'all_consumers_last_x_s_execute_count_fail': 50},
            {'all_consumers_last_x_s_execute_count': 100, 'all_consumers_last_x_s_execute_count_fail': 60},
        ])
        triggered, detail = ev.evaluate_fail_spike(threshold=20, min_calls=5)
        assert triggered
        assert '55%' in detail
        assert '20s' in detail

    def test_low_fail_rate(self):
        ev = _mock_evaluator([
            {'all_consumers_last_x_s_execute_count': 100, 'all_consumers_last_x_s_execute_count_fail': 5},
        ] * 3)
        triggered, _ = ev.evaluate_fail_spike(threshold=20, min_calls=5)
        assert not triggered

    def test_exact_threshold(self):
        ev = _mock_evaluator([
            {'all_consumers_last_x_s_execute_count': 100, 'all_consumers_last_x_s_execute_count_fail': 20},
        ])
        triggered, _ = ev.evaluate_fail_spike(threshold=20, min_calls=5)
        assert triggered


class TestEvaluateAvgTimeHigh:
    def test_empty_series(self):
        ev = _mock_evaluator([])
        triggered, _ = ev.evaluate_avg_time_high(threshold=5)
        assert not triggered

    def test_all_none(self):
        ev = _mock_evaluator([{'all_consumers_last_x_s_avarage_function_spend_time': None}] * 3)
        triggered, _ = ev.evaluate_avg_time_high(threshold=5)
        assert not triggered

    def test_above_threshold(self):
        ev = _mock_evaluator([
            {'all_consumers_last_x_s_avarage_function_spend_time': 8.0},
            {'all_consumers_last_x_s_avarage_function_spend_time': 6.0},
            {'all_consumers_last_x_s_avarage_function_spend_time': 7.0},
        ])
        triggered, detail = ev.evaluate_avg_time_high(threshold=5)
        assert triggered
        assert '7.0s' in detail

    def test_below_threshold(self):
        ev = _mock_evaluator([
            {'all_consumers_last_x_s_avarage_function_spend_time': 1.0},
            {'all_consumers_last_x_s_avarage_function_spend_time': 2.0},
        ])
        triggered, _ = ev.evaluate_avg_time_high(threshold=5)
        assert not triggered

    def test_partial_none(self):
        ev = _mock_evaluator([
            {'all_consumers_last_x_s_avarage_function_spend_time': 10.0},
            {'all_consumers_last_x_s_avarage_function_spend_time': None},
            {'all_consumers_last_x_s_avarage_function_spend_time': 8.0},
        ])
        triggered, detail = ev.evaluate_avg_time_high(threshold=5)
        assert triggered
        assert '9.0s' in detail


class TestEvaluateConsumerLost:
    def test_all_lost_via_active_count(self):
        ev = _mock_evaluator([{'active_consumer_count': 0, 'report_ts': 1700000000}] * 3)
        triggered, detail = ev.evaluate_consumer_lost(now=1700000000)
        assert triggered
        assert '连续 3' in detail

    def test_has_consumers(self):
        ev = _mock_evaluator([{'active_consumer_count': 2, 'report_ts': 1700000000}] * 3)
        triggered, _ = ev.evaluate_consumer_lost(now=1700000000)
        assert not triggered

    def test_stale_data_triggers(self):
        """消费者停了之后时序数据不再更新，report_ts 过期应触发告警"""
        ev = _mock_evaluator([{'active_consumer_count': 2, 'report_ts': 1700000000}] * 3)
        triggered, detail = ev.evaluate_consumer_lost(now=1700000000 + 120)
        assert triggered
        assert '停止更新' in detail
        assert '120s' in detail

    def test_fresh_data_with_consumers_not_triggered(self):
        """数据新鲜且有消费者在线，不应触发"""
        ev = _mock_evaluator([{'active_consumer_count': 5, 'report_ts': 1700000000}] * 3)
        triggered, _ = ev.evaluate_consumer_lost(now=1700000000 + 5)
        assert not triggered

    def test_empty_series(self):
        ev = _mock_evaluator([])
        triggered, _ = ev.evaluate_consumer_lost(now=1700000000)
        assert not triggered

    def test_now_zero_returns_false(self):
        ev = _mock_evaluator([{'active_consumer_count': 0, 'report_ts': 1700000000}] * 3)
        triggered, _ = ev.evaluate_consumer_lost(now=0)
        assert not triggered


class TestAlertRuleStore:
    def _make_store(self):
        mock_redis = MagicMock()
        return AlertRuleStore(redis_client=mock_redis), mock_redis

    def test_gen_id_length(self):
        rid = AlertRuleStore.gen_id()
        assert isinstance(rid, str)
        assert len(rid) == 8

    def test_load_all_empty(self):
        store, mock_redis = self._make_store()
        mock_redis.hgetall.return_value = {}
        assert store.load_all() == []

    def test_load_all_returns_rules_with_id(self):
        store, mock_redis = self._make_store()
        rule_dict = {'rule_name': 'test', 'alert_type': 'backlog'}
        mock_redis.hgetall.return_value = {
            b'abc123': json.dumps(rule_dict).encode(),
        }
        rules = store.load_all()
        assert len(rules) == 1
        assert rules[0]['_id'] == 'abc123'
        assert rules[0]['rule_name'] == 'test'

    def test_load_all_skips_corrupted(self):
        store, mock_redis = self._make_store()
        mock_redis.hgetall.return_value = {
            b'good': json.dumps({'rule_name': 'ok'}).encode(),
            b'bad': b'not-json{{{',
        }
        rules = store.load_all()
        assert len(rules) == 1
        assert rules[0]['rule_name'] == 'ok'

    def test_get_existing(self):
        store, mock_redis = self._make_store()
        rule_dict = {'rule_name': 'found', 'threshold': 100}
        mock_redis.hget.return_value = json.dumps(rule_dict).encode()
        result = store.get('xyz')
        assert result['rule_name'] == 'found'
        assert result['threshold'] == 100

    def test_get_not_found(self):
        store, mock_redis = self._make_store()
        mock_redis.hget.return_value = None
        assert store.get('missing') is None

    def test_get_corrupted_returns_none(self):
        store, mock_redis = self._make_store()
        mock_redis.hget.return_value = b'bad-json'
        assert store.get('corrupt') is None

    def test_save(self):
        store, mock_redis = self._make_store()
        rule = {'rule_name': 'test'}
        store.save('r1', rule)
        mock_redis.hset.assert_called_once()
        args = mock_redis.hset.call_args
        assert args[0][1] == 'r1'
        assert json.loads(args[0][2]) == rule

    def test_delete(self):
        store, mock_redis = self._make_store()
        store.delete('r1')
        mock_redis.hdel.assert_called_once_with('funboost:funweb:alert:rules', 'r1')


class TestAlertLogStore:
    def _make_store(self):
        mock_redis = MagicMock()
        return AlertLogStore(redis_client=mock_redis), mock_redis

    def test_append_calls_zadd(self):
        store, mock_redis = self._make_store()
        entry = {'rule_id': 'r1', 'detail': 'test'}
        store.append(entry)
        mock_redis.zadd.assert_called_once()
        mock_redis.zremrangebyrank.assert_called_once()
        mock_redis.expire.assert_called_once()

    def test_query_returns_logs(self):
        store, mock_redis = self._make_store()
        log1 = json.dumps({'rule_id': 'r1', 'ts': 100.0}).encode()
        log2 = json.dumps({'rule_id': 'r2', 'ts': 200.0}).encode()
        mock_redis.zrevrangebyscore.return_value = [log2, log1]
        logs = store.query(start_ts=50.0, end_ts=300.0)
        assert len(logs) == 2
        assert logs[0]['rule_id'] == 'r2'

    def test_query_empty(self):
        store, mock_redis = self._make_store()
        mock_redis.zrevrangebyscore.return_value = []
        logs = store.query(start_ts=0, end_ts=999)
        assert logs == []

    def test_query_skips_corrupted(self):
        store, mock_redis = self._make_store()
        mock_redis.zrevrangebyscore.return_value = [
            json.dumps({'rule_id': 'ok'}).encode(),
            b'not-json',
        ]
        logs = store.query(start_ts=0, end_ts=999)
        assert len(logs) == 1

    def test_query_respects_limit(self):
        store, mock_redis = self._make_store()
        entries = [json.dumps({'i': i}).encode() for i in range(10)]
        mock_redis.zrevrangebyscore.return_value = entries
        logs = store.query(start_ts=0, end_ts=999, limit=3)
        assert len(logs) == 3


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])
