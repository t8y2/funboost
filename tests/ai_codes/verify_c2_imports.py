"""Verify c2_new.md code imports and APIs against funboost source"""
from funboost import boost, BoosterParams, BrokerEnum, ConcurrentModeEnum, fct, BoostersManager

print("All imports OK:")
print(f"  boost: {boost}")
print(f"  BoosterParams: {BoosterParams}")
print(f"  BrokerEnum: {BrokerEnum}")
print(f"  ConcurrentModeEnum: {ConcurrentModeEnum}")
print(f"  fct: imported ok (type={type(fct).__name__})")
print(f"  BoostersManager: {BoostersManager}")

celery_exists = hasattr(BrokerEnum, "CELERY")
redis_exists = hasattr(BrokerEnum, "REDIS")
redis_ack_exists = hasattr(BrokerEnum, "REDIS_ACK_ABLE")
print(f"\nBrokerEnum.CELERY exists: {celery_exists}")
print(f"BrokerEnum.REDIS exists: {redis_exists}")
print(f"BrokerEnum.REDIS_ACK_ABLE exists: {redis_ack_exists}")

import inspect
sig = inspect.signature(BoosterParams)
key_params = ['queue_name', 'broker_kind', 'qps', 'log_level', 'concurrent_mode',
              'should_check_publish_func_params', 'is_using_rpc_mode', 'max_retry_times']
print("\nBoosterParams key fields:")
for p in key_params:
    exists = p in sig.parameters
    print(f"  {p}: {exists}")

# Check fct attributes
print(f"\nfct type: {type(fct)}")
print(f"fct has task_id: {hasattr(fct, 'task_id')}")

# Check booster object methods
@boost(BoosterParams(queue_name='test_verify_c2_q', broker_kind=BrokerEnum.REDIS))
def dummy_func(x):
    return x

print(f"\nBooster methods:")
print(f"  .push: {hasattr(dummy_func, 'push')}")
print(f"  .publish: {hasattr(dummy_func, 'publish')}")
print(f"  .consume: {hasattr(dummy_func, 'consume')}")
print(f"  .multi_process_consume: {hasattr(dummy_func, 'multi_process_consume')}")
print(f"  .mp_consume: {hasattr(dummy_func, 'mp_consume')}")
print(f"  .fabric_deploy: {hasattr(dummy_func, 'fabric_deploy')}")

# Check BoostersManager methods
print(f"\nBoostersManager methods:")
print(f"  .consume_all: {hasattr(BoostersManager, 'consume_all')}")
print(f"  .consume_group: {hasattr(BoostersManager, 'consume_group')}")
