"""验证 funboost-spider-crawling SKILL — SimpleSpiderClient 同步客户端"""
import os
import sys
import time

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
_ts = int(time.time())
os.environ["PRINT_WRTIE_FILE_NAME"] = f"v2_spider_simple_client_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"v2_spider_simple_client_std_{_ts}"

PASS = True


def report(name: str, ok: bool, detail: str = ""):
    global PASS
    if not ok:
        PASS = False
    status = "PASS" if ok else "FAIL"
    msg = f"[{status}] {name}"
    if detail:
        msg += f" — {detail}"
    print(msg)


try:
    from funboost.contrib.funspider import SimpleSpiderClient
    report("import SimpleSpiderClient", True)
except Exception as e:
    report("import SimpleSpiderClient", False, str(e))
    time.sleep(15)
    os._exit(66)


def abuyun_proxy():
    return "http://user:pass@proxy.abuyun.com:9020"


def redis_pool_proxy():
    return None


if __name__ == "__main__":
    try:
        client = SimpleSpiderClient(
            proxy_getter_list=[abuyun_proxy, redis_pool_proxy],
            retry_times=3,
            timeout=30,
            user_agents=None,
        )
        report("SimpleSpiderClient 实例化", isinstance(client, SimpleSpiderClient))
        report("retry_times=3", client.retry_times == 3)
        report("timeout=30", client.timeout == 30)
        report("proxy_getter_list 长度=2", len(client._proxy_getter_list) == 2)
        report("client.close() 可调用", callable(getattr(client, "close", None)))
        client.close()
        report("client.close() 无异常", True)
    except Exception as e:
        report("SimpleSpiderClient 示例", False, str(e))

    print(f"\n=== 最终结果: {'PASS' if PASS else 'FAIL'} ===")
    sys.stdout.flush()
    time.sleep(15)
    os._exit(66)
