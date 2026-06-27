"""
pytest 共享配置与 fixture。

将项目根目录加入 sys.path,使得 test_frame/pytests/ 下的测试
既可以 `pytest test_frame/pytests/` 运行,也可以 `python test_xxx.py` 独立运行。
"""
import os
import sys
import uuid

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import pytest


@pytest.fixture
def fresh_queue_name():
    """每次测试生成一个唯一队列名,避免相互污染。"""
    return f'test_pytest_{uuid.uuid4().hex[:12]}'


@pytest.fixture
def unique_id():
    """每次测试生成一个唯一标识,用于校验消息没串。"""
    return uuid.uuid4().hex[:10]
