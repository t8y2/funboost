"""验证 round3 / funboost-observability SKILL §2 OTel 链式任务示例"""
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"obs_trouble_obs_06_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"obs_trouble_obs_06_std_{_ts}"

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

from funboost import boost, BrokerEnum, fct
from funboost.contrib.override_publisher_consumer_cls.funboost_otel_mixin import OtelBoosterParams


def init_opentelemetry(service_name: str = "order-service"):
    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)
    otlp_exporter = OTLPSpanExporter(endpoint="localhost:4317", insecure=True)
    provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
    trace.set_tracer_provider(provider)


init_opentelemetry("order-service")

@boost(OtelBoosterParams(
    queue_name=f"obs_trouble_obs_otel_entry_{_ts}",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    concurrent_num=2,
))
def task_entry(order_id: int):
    fct.logger.info(f"处理订单 {order_id}")
    task_process.push(order_id=order_id)
    return order_id

@boost(OtelBoosterParams(
    queue_name=f"obs_trouble_obs_otel_process_{_ts}",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    concurrent_num=2,
))
def task_process(order_id: int):
    print(f"processed {order_id}")
    return f"processed {order_id}"

if __name__ == "__main__":
    task_process.consume()
    task_entry.consume()
    task_entry.push(order_id=1001)
    time.sleep(15)
    os._exit(66)
