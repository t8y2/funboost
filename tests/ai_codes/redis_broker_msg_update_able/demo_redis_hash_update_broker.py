# -*- coding: utf-8 -*-
"""
Redis HASH 可覆盖消息 broker 演示
===================================

演示 "dict 强化版" broker 的核心语义：
    相同 msg_key 的消息后发覆盖先发，消费端只拿到最新值。

场景模拟：
    IoT 传感器 device_id 频繁上报温度，只关心最新一次。
    快速连续推送同一 device_id 的多条消息，消费端只消费最终值。

运行方式：
    $env:PYTHONPATH = "D:\\codes\\funboost"
    D:\\ProgramData\\miniconda3\\envs\\py39b\\python.exe tests/ai_codes/redis_broker_msg_update_able/demo_redis_hash_update_broker.py
"""

import sys
import time
import functools

print = functools.partial(print, flush=True)

from funboost import boost, BoosterParams
from funboost.core.func_params_model import TaskOptions
from funboost.contrib.register_custom_broker_contrib.redis_hash_update_broker import (
    BROKER_KIND_REDIS_HASH_UPDATE,
)

consumed_records = []


@boost(BoosterParams(
    queue_name='demo_hash_update_iot_queue',
    broker_kind=BROKER_KIND_REDIS_HASH_UPDATE,
    concurrent_num=2,
    broker_exclusive_config={
        'override_key_fields': ['device_id'],
        'pull_base_interval': 0.05,
        'pull_max_interval': 1,
        'pull_batch_size': 50,
    },
))
def report_temperature(device_id, temperature, timestamp):
    msg = '[消费] device_id={}, temperature={}, timestamp={}'.format(
        device_id, temperature, timestamp)
    print(msg)
    consumed_records.append({
        'device_id': device_id,
        'temperature': temperature,
        'timestamp': timestamp,
    })
    return temperature


if __name__ == '__main__':
    print('=' * 60)
    print('演示：Redis HASH 可覆盖消息 broker（dict 强化版）')
    print('=' * 60)

    # 先清理旧消息
    report_temperature.clear()
    time.sleep(0.5)

    # ------------------------------------------------------------------
    # 阶段 1：先推送，展示覆盖语义
    # ------------------------------------------------------------------
    print('\n>>> 阶段1：快速推送同一 device_id 的多条消息（尚未启动消费者）')
    print('    device_id=sensor_001 推送 5 次，只有最后一次 temperature 会被消费')

    for i in range(5):
        report_temperature.push(
            device_id='sensor_001',
            temperature=20.0 + i,
            timestamp='2025-01-01T00:00:0{}'.format(i),
        )
        print('  [推送] sensor_001, temp={}'.format(20.0 + i))

    print('\n    device_id=sensor_002 推送 3 次')
    for i in range(3):
        report_temperature.push(
            device_id='sensor_002',
            temperature=30.0 + i,
            timestamp='2025-01-01T00:00:0{}'.format(i),
        )
        print('  [推送] sensor_002, temp={}'.format(30.0 + i))

    # 此时 HASH 中应该只有 2 条消息（每个 device_id 各一条最新的）
    from funboost.utils.redis_manager import RedisMixin
    r = RedisMixin().redis_db_frame
    hash_key = 'demo_hash_update_iot_queue:hash_update'
    count = r.hlen(hash_key)
    print('\n  HASH 中的消息数量: {}（预期为 2，因为覆盖了旧消息）'.format(count))

    all_values = r.hvals(hash_key)
    print('  HASH 中的消息内容:')
    import json
    for v in all_values:
        d = json.loads(v)
        d.pop('extra', None)
        d.pop('extra_params', None)
        print('    {}'.format(d))

    # ------------------------------------------------------------------
    # 阶段 2：启动消费者，消费剩余消息
    # ------------------------------------------------------------------
    print('\n>>> 阶段2：启动消费者，消费 HASH 中的消息')
    report_temperature.consume()

    time.sleep(3)

    print('\n>>> 消费结果汇总:')
    for rec in consumed_records:
        print('  device_id={}, temperature={}'.format(rec['device_id'], rec['temperature']))

    expected_temps = {24.0, 32.0}
    actual_temps = {rec['temperature'] for rec in consumed_records}
    if actual_temps == expected_temps:
        print('\n  [PASS] 覆盖语义正确！只消费了每个 device_id 的最新温度')
    else:
        print('\n  [INFO] 实际消费温度: {} (预期: {})'.format(actual_temps, expected_temps))

    # ------------------------------------------------------------------
    # 阶段 3：消费者运行中追加推送，实时消费
    # ------------------------------------------------------------------
    print('\n>>> 阶段3：消费者运行中，实时推送新消息')
    report_temperature.push(
        device_id='sensor_003',
        temperature=99.9,
        timestamp='2025-01-01T00:01:00',
    )
    print('  [推送] sensor_003, temp=99.9')

    time.sleep(3)

    sensor_003_temps = [rec['temperature'] for rec in consumed_records if rec['device_id'] == 'sensor_003']
    if sensor_003_temps and sensor_003_temps[-1] == 99.9:
        print('  [PASS] 实时消费成功！sensor_003 temperature=99.9')
    else:
        print('  [INFO] sensor_003 消费结果: {}'.format(sensor_003_temps))

    # ------------------------------------------------------------------
    # 阶段 4：使用 override_key 自定义覆盖 key
    # ------------------------------------------------------------------
    print('\n>>> 阶段4：通过 TaskOptions(other_extra_params={"for_broker_redis_hash_update": {"override_key": ...}}) 自定义覆盖 key')
    print('    同一个 override_key="config_app_v1" 推送 3 次不同配置，只保留最后一次')

    consumed_before_phase4 = len(consumed_records)

    for i in range(3):
        report_temperature.publish(
            {'device_id': 'complex_device_{}'.format(i),
             'temperature': 100 + i,
             'timestamp': '2025-06-01T00:00:0{}'.format(i)},
            task_options=TaskOptions(other_extra_params={
                'for_broker_redis_hash_update': {'override_key': 'config_app_v1'}
            }),
        )
        print('  [推送] override_key=config_app_v1, device_id=complex_device_{}, temp={}'.format(i, 100 + i))

    time.sleep(3)

    phase4_records = consumed_records[consumed_before_phase4:]
    if len(phase4_records) == 1 and phase4_records[0]['temperature'] == 102:
        print('  [PASS] override_key 覆盖语义正确！只消费了最后一次 temp=102')
    else:
        print('  [INFO] 阶段4 消费结果: {}'.format(
            [(r['device_id'], r['temperature']) for r in phase4_records]))

    print('\n' + '=' * 60)
    print('演示完成！')
    print('=' * 60)

    sys.stdout.flush()
    time.sleep(1)
    import os
    os._exit(0)
