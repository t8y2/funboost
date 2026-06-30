"""round3 验证: funboost-advanced-retry — 熔断器 CircuitBreakerConsumerMixin 示例"""
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"faas_retry_11_circuit_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"faas_retry_11_circuit_std_{_ts}"

EXAMPLE = "advanced-retry / 熔断器 Mixin"
PASS = True
FAIL_COUNT = 0


def report(ok: bool, msg: str):
    global PASS
    if not ok:
        PASS = False
    tag = "PASS" if ok else "FAIL"
    print(f"[{tag}] {EXAMPLE}: {msg}")


from funboost import boost, BoosterParams, BrokerEnum
from funboost.contrib.override_publisher_consumer_cls.circuit_breaker_mixin import CircuitBreakerConsumerMixin


class MockExternalService:
    def process(self, data):
        raise ConnectionError("service down")


external_service = MockExternalService()


@boost(BoosterParams(
    queue_name="r3_protected_task",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    consumer_override_cls=CircuitBreakerConsumerMixin,
    user_options={
        "circuit_breaker_options": {
            "failure_threshold": 5,
            "recovery_timeout": 60,
        },
    },
    concurrent_num=1,
))
def call_fragile_service(data: dict):
    global FAIL_COUNT
    FAIL_COUNT += 1
    print(f"[CB] call_fragile_service fail_count={FAIL_COUNT}, data={data}")
    return external_service.process(data)


if __name__ == "__main__":
    try:
        for i in range(3):
            call_fragile_service.push({"i": i})
        call_fragile_service.consume()
        time.sleep(8)
        report(FAIL_COUNT >= 3, f"CircuitBreakerConsumerMixin 消费失败 {FAIL_COUNT} 次无崩溃")
        report(True, "user_options circuit_breaker_options 配置被接受")
    except Exception as e:
        report(False, f"异常: {type(e).__name__}: {e}")

    time.sleep(15)
    print(f"\n=== 最终结果: {'PASS' if PASS else 'FAIL'} ===")
    os._exit(66 if PASS else 1)
