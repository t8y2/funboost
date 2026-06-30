"""round3 验证 funboost-spider-crawling SKILL — AsyncSpiderClient + ASYNC 模式"""
import os
import sys
import time

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
_ts = int(time.time())
os.environ["PRINT_WRTIE_FILE_NAME"] = f"r3_spider_async_client_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"r3_spider_async_client_std_{_ts}"

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
    from funboost import boost, BoosterParams, ConcurrentModeEnum
    from funboost.contrib.funspider import AsyncSpiderClient
    report("import AsyncSpiderClient, ConcurrentModeEnum", True)
except Exception as e:
    report("import AsyncSpiderClient, ConcurrentModeEnum", False, str(e))
    time.sleep(12)
    os._exit(66)


def abuyun_proxy():
    return "http://user:pass@proxy.abuyun.com:9020"


async_client = AsyncSpiderClient(proxy_getter_list=[abuyun_proxy], retry_times=3)


@boost(BoosterParams(
    queue_name="r3_async_crawl",
    broker_kind="MEMORY_QUEUE",
    concurrent_mode=ConcurrentModeEnum.ASYNC,
    qps=10,
))
async def crawl_api(news_id: int):
    # 不发网络请求，仅验证 async def + 参数
    return {"news_id": news_id, "mock": True}


if __name__ == "__main__":
    try:
        report("AsyncSpiderClient 实例化", isinstance(async_client, AsyncSpiderClient))
        report("AsyncSpiderClient.retry_times=3", async_client.retry_times == 3)
        params = crawl_api.boost_params
        report("concurrent_mode=ASYNC", params.concurrent_mode == ConcurrentModeEnum.ASYNC)
        report("async def crawl_api 装饰成功", callable(crawl_api.aio_push))
        report("aclose 方法存在", callable(getattr(async_client, "aclose", None)))
    except Exception as e:
        report("AsyncSpiderClient 示例", False, str(e))

    print(f"\n=== 最终结果: {'PASS' if PASS else 'FAIL'} ===")
    sys.stdout.flush()
    time.sleep(12)
    os._exit(66)
