"""验证 funboost-spider-crawling SKILL — boost_spider 可选包 import"""
import os
import sys
import time

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
_ts = int(time.time())
os.environ["PRINT_WRTIE_FILE_NAME"] = f"v2_spider_boost_spider_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"v2_spider_boost_spider_std_{_ts}"

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


if __name__ == "__main__":
    try:
        from boost_spider import RequestClient, SpiderResponse, DatasetSink
        report("boost_spider RequestClient import", True)
        report("boost_spider SpiderResponse import", True)
        report("boost_spider DatasetSink import", True)
    except ImportError as e:
        # 可选三方包，未安装时标记 SKIP 而非 FAIL
        print(f"[SKIP] boost_spider 未安装 — {e}")
        print("=== 最终结果: SKIP (可选依赖) ===")
        sys.stdout.flush()
        time.sleep(15)
        os._exit(66)
    except Exception as e:
        report("boost_spider import", False, str(e))

    print(f"\n=== 最终结果: {'PASS' if PASS else 'FAIL'} ===")
    sys.stdout.flush()
    time.sleep(15)
    os._exit(66)
