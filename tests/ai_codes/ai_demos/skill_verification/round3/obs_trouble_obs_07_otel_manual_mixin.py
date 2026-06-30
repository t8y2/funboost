"""验证 round3 / funboost-observability SKILL §2 手动指定 OTel Mixin"""
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"obs_trouble_obs_07_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"obs_trouble_obs_07_std_{_ts}"

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

from funboost import boost, BoosterParams, BrokerEnum
from funboost.contrib.override_publisher_consumer_cls.funboost_otel_mixin import (
    AutoOtelConsumerMixin,
    AutoOtelPublisherMixin,
)

provider = TracerProvider(resource=Resource.create({"service.name": "otel-manual"}))
provider.add_span_processor(BatchSpanProcessor(
    OTLPSpanExporter(endpoint="localhost:4317", insecure=True)
))
trace.set_tracer_provider(provider)

@boost(BoosterParams(
    queue_name=f"obs_trouble_obs_otel_manual_{_ts}",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    consumer_override_cls=AutoOtelConsumerMixin,
    publisher_override_cls=AutoOtelPublisherMixin,
    concurrent_num=2,
))
def my_otel_task(x):
    print(f"otel manual: {x + 1}")
    return x + 1

if __name__ == "__main__":
    my_otel_task.consume()
    my_otel_task.push(7)
    time.sleep(15)
    os._exit(66)
