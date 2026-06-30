"""验证 funboost-observability SKILL §导入路径速查"""
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"v2_obs_01_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"v2_obs_01_std_{_ts}"

from funboost import (
    boost, BoosterParams, BrokerEnum,
    FunctionResultStatusPersistanceConfig,
)
from funboost.contrib.override_publisher_consumer_cls.funboost_promethus_mixin import (
    PrometheusConsumerMixin,
    PrometheusPublisherMixin,
    PrometheusBoosterParams,
    PrometheusPushGatewayBoosterParams,
    start_prometheus_http_server,
)
from funboost.contrib.override_publisher_consumer_cls.funboost_otel_mixin import (
    AutoOtelConsumerMixin,
    AutoOtelPublisherMixin,
    OtelBoosterParams,
)
from funboost.contrib.override_publisher_consumer_cls.alert_notifier_mixin import (
    AlertNotifierConsumerMixin,
    AlertNotifierBoosterParams,
)
from funboost.contrib.override_publisher_consumer_cls.periodic_quota_mixin import (
    PeriodicQuotaConsumerMixin,
    PeriodicQuotaBoosterParams,
)
from funboost.core.mongo_alert_monitor import MongoAlertMonitor

print("[OK] 所有 observability 导入路径验证通过")

if __name__ == "__main__":
    time.sleep(15)
    os._exit(66)
