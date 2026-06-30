"""round3b / funboost-observability §2 init_opentelemetry — 非框架导出，需用户自行实现"""
import importlib
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"r2_web_obs_05_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"r2_web_obs_05_std_{_ts}"

import funboost

# init_opentelemetry 不在 funboost 框架内，SKILL 提供的是用户侧示例代码
assert not hasattr(funboost, "init_opentelemetry"), "init_opentelemetry should NOT be in funboost top-level"

try:
    importlib.import_module("funboost.contrib.override_publisher_consumer_cls.funboost_otel_mixin")
    otel_mod = importlib.import_module(
        "funboost.contrib.override_publisher_consumer_cls.funboost_otel_mixin"
    )
except ImportError as e:
    raise AssertionError(f"otel mixin import failed: {e}") from e
assert not hasattr(otel_mod, "init_opentelemetry"), "init_opentelemetry should NOT be in otel mixin module"

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter


def init_opentelemetry(service_name: str = "my-funboost-app"):
    """SKILL §2 示例：用户必须在 consume 前自行初始化 OTel"""
    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)
    otlp_exporter = OTLPSpanExporter(endpoint="localhost:4317", insecure=True)
    provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
    trace.set_tracer_provider(provider)


if __name__ == "__main__":
    init_opentelemetry("r2-web-obs-verify")
    tracer = trace.get_tracer("test")
    with tracer.start_as_current_span("verify_span"):
        print("[PASS] init_opentelemetry is user-defined (not in funboost); skill pattern runs ok")
    time.sleep(12)
    os._exit(66)
