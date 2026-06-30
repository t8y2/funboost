import os, time, sys
os.environ['LOG_PATH'] = r'D:\pythonlogs\ai_console_outs'
os.environ['PRINT_WRTIE_FILE_NAME'] = 'deep_verify_a_print.txt'
os.environ['SYS_STD_FILE_NAME'] = 'deep_verify_a_std.txt'
sys.path.insert(0, r'D:\codes\funboost')

from funboost import boost, BoosterParams, BrokerEnum, ConcurrentModeEnum, fct

# === 场景1: 基础 push + consume ===
consumed_messages = []

@boost(BoosterParams(
    queue_name='deep_verify_a_basic',
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    concurrent_num=1,
    qps=0,
))
def basic_add(a, b):
    result = a + b
    consumed_messages.append(result)
    print(f'[CONSUMED] basic_add({a}, {b}) = {result}')
    return result

basic_add.push(1, 2)
basic_add.push(10, 20)
basic_add.push(100, 200)
basic_add.consume()

# === 场景2: RPC 模式 ===
@boost(BoosterParams(
    queue_name='deep_verify_a_rpc',
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    is_using_rpc_mode=True,
    concurrent_num=1,
))
def rpc_multiply(a, b):
    result = a * b
    print(f'[CONSUMED] rpc_multiply({a}, {b}) = {result}')
    return result

rpc_multiply.consume()
async_result = rpc_multiply.push(6, 7)
print(f'[INFO] async_result.task_id = {async_result.task_id}')

# === 场景3: fct 上下文 ===
fct_captured = {}

@boost(BoosterParams(
    queue_name='deep_verify_a_fct',
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    concurrent_num=1,
))
def fct_demo(x):
    fct_captured['task_id'] = fct.task_id
    fct_captured['queue_name'] = fct.queue_name
    fct_captured['run_times'] = fct.function_result_status.run_times
    print(f'[CONSUMED] fct_demo({x}): task_id={fct.task_id}, queue_name={fct.queue_name}, run_times={fct.function_result_status.run_times}')

fct_demo.push(42)
fct_demo.consume()

# === 场景4: 重试机制 ===
retry_counter = [0]

@boost(BoosterParams(
    queue_name='deep_verify_a_retry',
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    max_retry_times=5,
    concurrent_num=1,
))
def retry_task(x):
    retry_counter[0] += 1
    print(f'[CONSUMED] retry_task 第{retry_counter[0]}次执行')
    if retry_counter[0] < 3:
        raise ValueError(f'模拟失败 第{retry_counter[0]}次')
    print(f'[CONSUMED] retry_task 最终成功, x={x}')

retry_task.push(99)
retry_task.consume()

# 等待消费完成
time.sleep(15)

# === 最终检查 ===
print(f'\n===== 最终验证 =====')
print(f'[CHECK] consumed_messages = {consumed_messages}')
if sorted(consumed_messages) == [3, 30, 300]:
    print('[PASS] 基础消费: 3条消息全部被消费且结果正确')
else:
    print(f'[FAIL] 基础消费: expected [3,30,300], got {consumed_messages}')

rpc_result = async_result.result
print(f'[CHECK] rpc_multiply result = {rpc_result}')
if rpc_result == 42:
    print('[PASS] RPC: result=42 正确')
else:
    print(f'[FAIL] RPC: expected 42, got {rpc_result}')

print(f'[CHECK] fct_captured = {fct_captured}')
if fct_captured.get('task_id') and fct_captured.get('queue_name') == 'deep_verify_a_fct' and fct_captured.get('run_times') == 1:
    print('[PASS] fct 上下文: task_id/queue_name/run_times 全部正确')
else:
    print(f'[FAIL] fct 上下文: {fct_captured}')

print(f'[CHECK] retry_counter = {retry_counter[0]}')
if retry_counter[0] >= 3:
    print(f'[PASS] 重试: 执行了{retry_counter[0]}次(失败2次+成功1次)')
else:
    print(f'[FAIL] 重试: 只执行了{retry_counter[0]}次')

print('\n===== 验证完毕 =====')
os._exit(66)
