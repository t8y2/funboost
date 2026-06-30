import os, time, sys, threading, json
os.environ['LOG_PATH'] = r'D:\pythonlogs\ai_console_outs'
os.environ['PRINT_WRTIE_FILE_NAME'] = 'deep_verify_c_print.txt'
os.environ['SYS_STD_FILE_NAME'] = 'deep_verify_c_std.txt'
sys.path.insert(0, r'D:\codes\funboost')

from funboost import boost, BoosterParams, BrokerEnum
from funboost.consumers.base_consumer import AbstractConsumer
from funboost.publishers.base_publisher import AbstractPublisher
from funboost.core.serialization import Serialization
from funboost import register_custom_broker

# === 场景1: Mixin 钩子验证 ===
mixin_events = []

class MyMonitorMixin:
    def custom_init(self):
        mixin_events.append('custom_init')
        print(f'[MIXIN] custom_init 被调用')

    def _both_sync_and_aio_frame_custom_record_process_info_func(self, current_function_result_status, kw):
        super()._both_sync_and_aio_frame_custom_record_process_info_func(current_function_result_status, kw)
        success = current_function_result_status.success
        mixin_events.append(f'record:{success}')
        print(f'[MIXIN] _both_sync_and_aio_frame_custom_record_process_info_func: success={success}')

@boost(BoosterParams(
    queue_name='deep_verify_c_mixin',
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    concurrent_num=1,
    consumer_override_cls=MyMonitorMixin,
))
def mixin_task(x):
    print(f'[CONSUMED] mixin_task({x})')
    return x * 10

mixin_task.push(1)
mixin_task.push(2)
mixin_task.push(3)
mixin_task.consume()

# === 场景2: 自定义 Broker ===
_custom_queue = []

class MyPublisher(AbstractPublisher):
    def _publish_impl(self, msg):
        _custom_queue.append(msg)
        print(f'[CUSTOM_BROKER] _publish_impl 收到: type={type(msg).__name__}, len={len(_custom_queue)}')

    def clear(self):
        _custom_queue.clear()

    def get_message_count(self):
        return len(_custom_queue)

    def close(self):
        pass

class MyConsumer(AbstractConsumer):
    def _dispatch_task(self):
        if _custom_queue:
            msg = _custom_queue.pop(0)
            print(f'[CUSTOM_BROKER] _dispatch_task 取出消息')
            self._submit_task({'body': msg})
        else:
            time.sleep(0.1)

    def _confirm_consume(self, kw):
        print(f'[CUSTOM_BROKER] _confirm_consume')

    def _requeue(self, kw):
        _custom_queue.append(Serialization.to_json_str(kw['body']))
        print(f'[CUSTOM_BROKER] _requeue')

register_custom_broker(broker_kind='DEEP_VERIFY_C_BROKER', publisher_class=MyPublisher, consumer_class=MyConsumer)

custom_broker_results = []

@boost(BoosterParams(
    queue_name='deep_verify_c_custom',
    broker_kind='DEEP_VERIFY_C_BROKER',
    concurrent_num=1,
))
def custom_broker_task(value):
    custom_broker_results.append(value)
    print(f'[CONSUMED] custom_broker_task({value})')
    return value

custom_broker_task.push(100)
custom_broker_task.push(200)
custom_broker_task.consume()

# 等待消费
time.sleep(15)

# === 最终检查 ===
print(f'\n===== 最终验证 =====')
print(f'[CHECK] mixin_events = {mixin_events}')
if 'custom_init' in mixin_events:
    print('[PASS] Mixin: custom_init 被调用')
else:
    print('[FAIL] Mixin: custom_init 未被调用')

record_events = [e for e in mixin_events if e.startswith('record:')]
if len(record_events) == 3:
    print(f'[PASS] Mixin: _both_sync_and_aio_frame_custom_record_process_info_func 被调用 3 次')
else:
    print(f'[FAIL] Mixin: record 事件数={len(record_events)}, expected 3')

print(f'[CHECK] custom_broker_results = {custom_broker_results}')
if sorted(custom_broker_results) == [100, 200]:
    print('[PASS] 自定义 Broker: 2条消息全部被消费')
else:
    print(f'[FAIL] 自定义 Broker: expected [100,200], got {custom_broker_results}')

print('\n===== 验证完毕 =====')
os._exit(66)
