"""验证 developing-funboost-broker skill 中的代码示例 — register_custom_broker"""
import os
import time
import queue

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"verify_broker_ext_{int(time.time())}"
os.environ["SYS_STD_FILE_NAME"] = f"verify_broker_ext_std_{int(time.time())}"

from funboost import boost, BoosterParams
from funboost.publishers.base_publisher import AbstractPublisher
from funboost.consumers.base_consumer import AbstractConsumer

_shared_queue = queue.Queue()


class MyCustomPublisher(AbstractPublisher):
    """自定义 Publisher — 使用内存 queue 模拟"""

    def custom_init(self):
        super().custom_init()
        print(f"[OK] MyCustomPublisher.custom_init 执行, queue_name={self._queue_name}")

    def _publish_impl(self, msg):
        _shared_queue.put(msg)
        print(f"[OK] MyCustomPublisher 发布消息")

    def clear(self):
        while not _shared_queue.empty():
            _shared_queue.get_nowait()

    def get_message_count(self):
        return _shared_queue.qsize()

    def close(self):
        pass


class MyCustomConsumer(AbstractConsumer):
    """自定义 Consumer — 从内存 queue 消费"""

    def custom_init(self):
        super().custom_init()
        print(f"[OK] MyCustomConsumer.custom_init 执行, queue_name={self._queue_name}")

    def _dispatch_task(self):
        try:
            msg = _shared_queue.get(timeout=0.5)
            self._submit_task({'body': msg})
        except queue.Empty:
            pass

    def _confirm_consume(self, kw):
        pass

    def _requeue(self, kw):
        _shared_queue.put(kw['body'])

    def _get_msg_count(self):
        return _shared_queue.qsize()


# 验证: register_custom_broker
from funboost.factories.broker_kind__publsiher_consumer_type_map import register_custom_broker

register_custom_broker(
    broker_kind="MY_CUSTOM_BROKER",
    publisher_class=MyCustomPublisher,
    consumer_class=MyCustomConsumer,
)
print("[OK] register_custom_broker 注册成功")


@boost(BoosterParams(
    queue_name="verify_custom_broker_q",
    broker_kind="MY_CUSTOM_BROKER",
    concurrent_num=2,
    qps=5,
))
def custom_broker_task(action: str, value: int):
    result = f"{action}_{value * 2}"
    print(f"[OK] custom_broker_task action={action}, value={value}, result={result}")
    return result


if __name__ == "__main__":
    # 发布消息
    for i in range(5):
        custom_broker_task.push(f"act_{i}", value=i)

    # 启动消费
    custom_broker_task.consume()

    time.sleep(8)
    print("[DONE] verify_broker_extension 完成")
    os._exit(66)
