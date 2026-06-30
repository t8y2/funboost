
import os, time
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
from funboost import boost, BoosterParams, BrokerEnum

@boost(BoosterParams(queue_name="subprocess_child_q", broker_kind=BrokerEnum.SQLITE_QUEUE, concurrent_num=1))
def child_task(x):
    print(f"child {x}")

if __name__ == "__main__":
    child_task.push(0)
    child_task.consume()
    time.sleep(60)
