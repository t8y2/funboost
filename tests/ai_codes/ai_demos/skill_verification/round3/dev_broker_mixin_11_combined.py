"""验证 developing-funboost-mixin SKILL.md §组合多个 Mixin (201-214)"""
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"dev_broker_mixin_11_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"dev_broker_mixin_11_std_{_ts}"

from funboost import boost, BoosterParams, BrokerEnum
from funboost.contrib.override_publisher_consumer_cls.circuit_breaker_mixin import (
    CircuitBreakerConsumerMixin,
)
from funboost.contrib.override_publisher_consumer_cls.funboost_promethus_mixin import (
    PrometheusConsumerMixin,
)

RESULTS = []


class CombinedMixin(CircuitBreakerConsumerMixin, PrometheusConsumerMixin):
    """MRO 确保两个 mixin 的方法都能执行"""
    pass


@boost(BoosterParams(
    queue_name=f"combined_task_r3_{_ts}",
    broker_kind=BrokerEnum.SQLITE_QUEUE,
    consumer_override_cls=CombinedMixin,
    user_options={
        "circuit_breaker_options": {"failure_threshold": 5},
    },
    concurrent_num=1,
    create_logger_file=False,
    is_send_consumer_heartbeat_to_redis=False,
))
def my_task(x):
    RESULTS.append(x)
    print(f"[OK] combined my_task x={x}")
    return x


if __name__ == "__main__":
    print("[START] dev_broker_mixin_11_combined")
    try:
        my_task.push(7)
        my_task.consume()
        time.sleep(15)
        if RESULTS == [7]:
            print("[PASS] CombinedMixin(CircuitBreaker, Prometheus) 组合运行成功")
        else:
            print(f"[FAIL] RESULTS={RESULTS!r}")
    except Exception as e:
        print(f"[FAIL] 组合 Mixin 异常: {type(e).__name__}: {e}")
    os._exit(66)
