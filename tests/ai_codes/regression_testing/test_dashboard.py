# -*- coding: utf-8 -*-
"""
Dashboard 功能回归测试
测试内容：
1. dashboard_bp 蓝图可正常导入
2. app 注册了 /api/dashboard/summary 路由
3. 未登录访问 dashboard API 返回重定向到 login
4. 登录后访问 dashboard API 返回正确结构
5. dashboard.html 模板可正常渲染
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

import pytest


def test_dashboard_blueprint_import():
    """测试 dashboard 蓝图可正常导入"""
    from funboost.funweb.flask_bps.dashboard import dashboard_bp
    assert dashboard_bp is not None
    assert dashboard_bp.name == 'dashboard'


def test_dashboard_route_registered():
    """测试 /api/dashboard/summary 路由已注册"""
    from funboost.funweb.app import app
    rules = [r.rule for r in app.url_map.iter_rules()]
    assert '/api/dashboard/summary' in rules


def test_dashboard_api_requires_login():
    """测试未登录访问 dashboard API 返回重定向"""
    from funboost.funweb.app import app
    app.config['TESTING'] = True
    with app.test_client() as client:
        resp = client.get('/api/dashboard/summary')
        assert resp.status_code in (302, 401)


def test_dashboard_template_accessible_after_login():
    """测试登录后可访问 dashboard 模板"""
    from funboost.funweb.app import app
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as client:
        client.post('/login', data={
            'user_name': 'admin',
            'password': '123456',
        }, follow_redirects=True)

        resp = client.get('/tpl/dashboard.html')
        assert resp.status_code == 200
        assert b'Dashboard' in resp.data


def test_dashboard_api_after_login():
    """测试登录后访问 dashboard API 返回正确结构"""
    from funboost.funweb.app import app
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as client:
        client.post('/login', data={
            'user_name': 'admin',
            'password': '123456',
        }, follow_redirects=True)

        resp = client.get('/api/dashboard/summary')
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'succ' in data
        if data['succ']:
            d = data['data']
            assert 'total_queues' in d
            assert 'total_consumers' in d
            assert 'total_backlog' in d
            assert 'total_qps' in d
            assert 'total_consumer_ips' in d
            assert 'queue_backlog_top' in d
            assert 'queue_throughput_top' in d
            assert 'system_resources' in d


def test_index_default_page_is_dashboard():
    """测试首页默认加载 dashboard"""
    from funboost.funweb.app import app
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as client:
        client.post('/login', data={
            'user_name': 'admin',
            'password': '123456',
        }, follow_redirects=True)

        resp = client.get('/')
        assert resp.status_code == 200
        assert b'dashboard' in resp.data.lower()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
