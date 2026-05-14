"""
极简测试：验证 python -c "from funboost import xxx" 是否正常
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
print('1. 开始导入', flush=True)
from funboost import boost, BoosterParams
print('2. 导入成功', flush=True)
print('3. 完成', flush=True)
