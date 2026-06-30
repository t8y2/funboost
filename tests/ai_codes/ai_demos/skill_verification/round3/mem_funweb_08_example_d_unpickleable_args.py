"""验证 skill: funboost-memory-queue-pool §7 示例 D 不可序列化对象入参"""
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"mem_funweb_08_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"mem_funweb_08_std_{_ts}"

from funboost import boost, BoosterParams, BrokerEnum


class DBConnection:
    def query(self, sql):
        return f"result of {sql}"


@boost(BoosterParams(queue_name=f"nosql_demo_r3_{_ts}", broker_kind=BrokerEnum.MEMORY_QUEUE))
def run_query(conn: DBConnection, sql: str):
    return conn.query(sql)


if __name__ == "__main__":
    run_query.consume()
    conn = DBConnection()
    run_query.push(conn, "SELECT 1")
    future = run_query.publisher.get_future(conn, "SELECT 2")
    status = future.result(timeout=10)
    assert status.success
    print(f"push ok, get_future result={status.result}")
    print("[PASS] example D unpickleable args")
    time.sleep(15)
    os._exit(66)
