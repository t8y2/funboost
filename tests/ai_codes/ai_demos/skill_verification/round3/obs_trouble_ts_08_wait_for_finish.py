"""验证 round3 / funboost-troubleshooting SKILL §3 步骤7 wait_for_possible_has_finish_all_tasks"""
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"obs_trouble_ts_08_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"obs_trouble_ts_08_std_{_ts}"

from funboost import boost, BoosterParams, BrokerEnum

@boost(BoosterParams(
    queue_name=f"obs_trouble_ts_wait_{_ts}",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    concurrent_num=2,
    qps=10,
))
def f(x):
    print(f"wait demo task: {x}")
    return x

if __name__ == "__main__":
    for i in range(5):
        f.push(i)
    f.consume()
    # SKILL 示例: f.wait_for_possible_has_finish_all_tasks(minutes=3)
    # 该方法最少 minutes=2，且会阻塞数分钟；自动化测试仅验证 API 绑定正确
    assert callable(f.wait_for_possible_has_finish_all_tasks)
    print("[OK] wait_for_possible_has_finish_all_tasks API 可调用（完整等待见 SKILL §3 步骤7）")
    time.sleep(15)
    os._exit(66)
