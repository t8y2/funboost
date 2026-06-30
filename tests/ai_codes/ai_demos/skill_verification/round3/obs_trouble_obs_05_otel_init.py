"""验证 round3 / funboost-observability SKILL §2 init_opentelemetry 前置初始化"""
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"obs_trouble_obs_05_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"obs_trouble_obs_05_std_{_ts}"

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter


def init_opentelemetry(service_name: str = "my-funboost-app"):
    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)
    otlp_exporter = OTLPSpanExporter(endpoint="localhost:4317", insecure=True)
    provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
    trace.set_tracer_provider(provider)


if __name__ == "__main__":
    init_opentelemetry("skill-verify-otel-init")
    tracer = trace.get_tracer("test")
    with tracer.start_as_current_span("verify_span"):
        print("[OK] init_opentelemetry 执行成功，span 已创建")
    time.sleep(15)
    os._exit(66)
