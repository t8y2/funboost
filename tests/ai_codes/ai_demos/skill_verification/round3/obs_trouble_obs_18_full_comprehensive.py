"""验证 round3 / funboost-observability SKILL §7 完整综合示例"""
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"obs_trouble_obs_18_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"obs_trouble_obs_18_std_{_ts}"

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

from funboost import boost, BoosterParams, BrokerEnum, FunctionResultStatusPersistanceConfig
from funboost.contrib.override_publisher_consumer_cls.funboost_promethus_mixin import (
    PrometheusConsumerMixin, PrometheusPublisherMixin, start_prometheus_http_server,
)
from funboost.contrib.override_publisher_consumer_cls.funboost_otel_mixin import (
    AutoOtelConsumerMixin,
    AutoOtelPublisherMixin,
)
from funboost.contrib.override_publisher_consumer_cls.alert_notifier_mixin import (
    AlertNotifierConsumerMixin,
)


def init_opentelemetry():
    provider = TracerProvider(resource=Resource.create({"service.name": "demo-app"}))
    provider.add_span_processor(BatchSpanProcessor(
        OTLPSpanExporter(endpoint="localhost:4317", insecure=True)
    ))
    trace.set_tracer_provider(provider)


class FullObservabilityConsumer(PrometheusConsumerMixin, AutoOtelConsumerMixin, AlertNotifierConsumerMixin):
    pass


class FullObservabilityPublisher(PrometheusPublisherMixin, AutoOtelPublisherMixin):
    pass


init_opentelemetry()
start_prometheus_http_server(port=18318)

@boost(BoosterParams(
    queue_name=f"obs_trouble_obs_full_{_ts}",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    consumer_override_cls=FullObservabilityConsumer,
    publisher_override_cls=FullObservabilityPublisher,
    concurrent_num=2,
    function_result_status_persistance_conf=FunctionResultStatusPersistanceConfig(
        is_save_status=True,
        is_save_result=True,
    ),
    user_options={
        'alert_options': {
            'failure_threshold': 5,
            'alert_app': 'wechat',
            'webhook_url': 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=YOUR_KEY',
        },
    },
))
def full_observable_task(order_id: int):
    print(f"full_observable_task order_id={order_id}")
    return {"order_id": order_id, "status": "ok"}


if __name__ == "__main__":
    consumer_mro = [c.__name__ for c in FullObservabilityConsumer.__mro__]
    publisher_mro = [c.__name__ for c in FullObservabilityPublisher.__mro__]
    print(f"[OK] Consumer MRO head: {consumer_mro[:6]}")
    print(f"[OK] Publisher MRO head: {publisher_mro[:5]}")
    full_observable_task.consume()
    full_observable_task.push(order_id=1001)
    time.sleep(15)
    os._exit(66)
