import os, time, sys, asyncio
os.environ['LOG_PATH'] = r'D:\pythonlogs\ai_console_outs'
os.environ['PRINT_WRTIE_FILE_NAME'] = 'deep_verify_b_print.txt'
os.environ['SYS_STD_FILE_NAME'] = 'deep_verify_b_std.txt'
sys.path.insert(0, r'D:\codes\funboost')

from funboost import boost, BoosterParams, BrokerEnum, ConcurrentModeEnum

# === 场景1: 异步消费 ===
async_consumed = []

@boost(BoosterParams(
    queue_name='deep_verify_b_async',
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    concurrent_mode=ConcurrentModeEnum.ASYNC,
    concurrent_num=5,
))
async def async_fetch(url):
    await asyncio.sleep(0.1)
    async_consumed.append(url)
    print(f'[CONSUMED] async_fetch({url})')
    return f'fetched:{url}'

async def push_async_tasks():
    await async_fetch.aio_push('http://example.com/1')
    await async_fetch.aio_push('http://example.com/2')
    await async_fetch.aio_push('http://example.com/3')

asyncio.get_event_loop().run_until_complete(push_async_tasks())
async_fetch.consume()

# === 场景2: Workflow chain ===
from funboost.workflow import chain, group, chord, WorkflowBoosterParams

@boost(WorkflowBoosterParams(
    queue_name='deep_verify_b_step1',
    broker_kind=BrokerEnum.MEMORY_QUEUE,
))
def step1(x):
    result = x + 10
    print(f'[CONSUMED] step1({x}) = {result}')
    return result

@boost(WorkflowBoosterParams(
    queue_name='deep_verify_b_step2',
    broker_kind=BrokerEnum.MEMORY_QUEUE,
))
def step2(x):
    result = x * 2
    print(f'[CONSUMED] step2({x}) = {result}')
    return result

@boost(WorkflowBoosterParams(
    queue_name='deep_verify_b_step3',
    broker_kind=BrokerEnum.MEMORY_QUEUE,
))
def step3(x):
    result = x - 5
    print(f'[CONSUMED] step3({x}) = {result}')
    return result

step1.consume()
step2.consume()
step3.consume()

# chain: step1(3) -> step2(13) -> step3(26) = 21
workflow = chain(step1.s(3), step2.s(), step3.s())
chain_result = workflow.apply()
print(f'[INFO] chain result = {chain_result}')

# group: step1(1), step1(2), step1(3) 并行
g = group(step1.s(1), step1.s(2), step1.s(3))
group_result = g.apply()
print(f'[INFO] group result = {group_result}')

# 等待所有消费完成
time.sleep(15)

# === 最终检查 ===
print(f'\n===== 最终验证 =====')
print(f'[CHECK] async_consumed = {async_consumed}')
if len(async_consumed) == 3:
    print(f'[PASS] 异步消费: 3条消息全部被消费 {async_consumed}')
else:
    print(f'[FAIL] 异步消费: expected 3, got {len(async_consumed)}')

if chain_result == 21:
    print(f'[PASS] workflow chain: step1(3)=13 -> step2(13)=26 -> step3(26)=21')
else:
    print(f'[FAIL] workflow chain: expected 21, got {chain_result}')

if sorted(group_result) == [11, 12, 13]:
    print(f'[PASS] workflow group: step1(1)=11, step1(2)=12, step1(3)=13')
else:
    print(f'[FAIL] workflow group: expected [11,12,13], got {group_result}')

print('\n===== 验证完毕 =====')
os._exit(66)
