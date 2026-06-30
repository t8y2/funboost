"""round3b / funboost-observability §导入路径速查 — 四个 Consumer Mixin"""
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"r2_web_obs_03_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"r2_web_obs_03_std_{_ts}"

from funboost.contrib.override_publisher_consumer_cls.funboost_promethus_mixin import (
    PrometheusConsumerMixin,
)
from funboost.contrib.override_publisher_consumer_cls.funboost_otel_mixin import (
    AutoOtelConsumerMixin,
)
from funboost.contrib.override_publisher_consumer_cls.alert_notifier_mixin import (
    AlertNotifierConsumerMixin,
)
from funboost.contrib.override_publisher_consumer_cls.periodic_quota_mixin import (
    PeriodicQuotaConsumerMixin,
)

assert all(
    isinstance(cls, type)
    for cls in (
        PrometheusConsumerMixin,
        AutoOtelConsumerMixin,
        AlertNotifierConsumerMixin,
        PeriodicQuotaConsumerMixin,
    )
)

print("[PASS] PrometheusConsumerMixin / AutoOtelConsumerMixin / "
      "AlertNotifierConsumerMixin / PeriodicQuotaConsumerMixin import ok")

if __name__ == "__main__":
    time.sleep(12)
    os._exit(66)
