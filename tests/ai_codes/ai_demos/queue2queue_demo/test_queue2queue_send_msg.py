import os
import time
import json
import logging

os.environ['LOG_PATH'] = 'D:/pythonlogs'
os.environ['PRINT_WRTIE_FILE_NAME'] = 'queue2queue_test_demo3'
os.environ['SYS_STD_FILE_NAME'] = 'queue2queue_test_demo3'

from funboost import get_publisher, BrokerEnum
from funboost.core.func_params_model import PublisherParams
from funboost.contrib.queue2queue_helper import queue2queue
from funboost.queues.memory_queues_map import PythonQueues

SOURCE_QUEUE = 'test_q2q_source_001'
TARGET_QUEUE = 'test_q2q_target_001'

source_pub = get_publisher(PublisherParams(queue_name=SOURCE_QUEUE, broker_kind=BrokerEnum.MEMORY_QUEUE, log_level=logging.WARNING))

for i in range(5):
    source_pub.publish({'x': i, 'y': i * 2}, task_id=f'preserved_task_{i}')

print(f'Pushed 5 messages to source queue. Source queue size: {source_pub.get_message_count()}')

queue2queue(
    SOURCE_QUEUE, BrokerEnum.MEMORY_QUEUE,
    TARGET_QUEUE, BrokerEnum.MEMORY_QUEUE,
    log_level=logging.WARNING,
    exit_script_when_finish=False
)

print('Waiting for transfer to complete...')
for _ in range(50):
    if source_pub.get_message_count() == 0:
        break
    time.sleep(0.1)

source_remaining = source_pub.get_message_count()
target_pub = get_publisher(PublisherParams(queue_name=TARGET_QUEUE, broker_kind=BrokerEnum.MEMORY_QUEUE, log_level=logging.WARNING))
target_count = target_pub.get_message_count()

print(f'Source queue remaining: {source_remaining}')
print(f'Target queue size: {target_count}')

assert source_remaining == 0, f'Expected source queue empty, got {source_remaining}'
assert target_count == 5, f'Expected 5 messages in target, got {target_count}'

target_queue = PythonQueues.get_queue(TARGET_QUEUE)
received_task_ids = []
for _ in range(target_count):
    msg_json = target_queue.get()
    msg_dict = json.loads(msg_json)
    task_id = msg_dict.get('extra', {}).get('task_id')
    received_task_ids.append(task_id)
    print(f'  task_id={task_id}, x={msg_dict.get("x")}, y={msg_dict.get("y")}')

expected_task_ids = [f'preserved_task_{i}' for i in range(5)]
assert received_task_ids == expected_task_ids, f'Task IDs not preserved!\nExpected: {expected_task_ids}\nGot: {received_task_ids}'

print('\n=== ALL TESTS PASSED ===')
print('Task IDs preserved correctly, no _set_do_not_delete_extra_from_msg needed!')

time.sleep(2)
os._exit(66)