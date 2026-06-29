"""验证 developing-funboost-testing skill 中的代码示例和模式"""
import os
import sys
import time

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"verify_testing_{int(time.time())}"
os.environ["SYS_STD_FILE_NAME"] = f"verify_testing_std_{int(time.time())}"

from funboost import boost, BoosterParams, BrokerEnum, fct


# 验证1: PYTHONPATH 和配置加载
project_root = r"D:\codes\funboost"
pythonpath_ok = project_root in sys.path or project_root.replace("\\", "/") in sys.path or os.environ.get("PYTHONPATH", "") == project_root
print(f"[OK] PYTHONPATH 包含项目根: {pythonpath_ok}")
print(f"[OK] sys.path[0] = {sys.path[0]}")

# 验证2: funboost_config 已被加载
try:
    import funboost_config
    print(f"[OK] funboost_config 模块加载成功, path={funboost_config.__file__}")
except ImportError:
    print("[WARN] funboost_config 未找到")


# 验证3: fct 上下文在消费函数中可用
@boost(BoosterParams(
    queue_name="verify_testing_fct",
    broker_kind=BrokerEnum.SQLITE_QUEUE,
    concurrent_num=2,
    qps=5,
))
def test_fct_task(value: str):
    task_id = fct.task_id
    queue_name = fct.queue_name
    run_times = fct.function_result_status.run_times
    print(f"[OK] fct.task_id={task_id[:16]}..., fct.queue_name={queue_name}, run_times={run_times}")
    return f"done_{value}"


# 验证4: 环境变量日志路径设置
@boost(BoosterParams(
    queue_name="verify_testing_env",
    broker_kind=BrokerEnum.SQLITE_QUEUE,
    concurrent_num=2,
    qps=5,
))
def test_env_task(name: str):
    log_path = os.environ.get("LOG_PATH", "NOT_SET")
    print(f"[OK] LOG_PATH={log_path}, task name={name}")
    return name


if __name__ == "__main__":
    # 发布消息
    for i in range(3):
        test_fct_task.push(f"item_{i}")
        test_env_task.push(f"env_test_{i}")

    # 启动消费
    test_fct_task.consume()
    test_env_task.consume()

    time.sleep(10)
    print("[DONE] verify_testing_patterns 完成")
    os._exit(66)
