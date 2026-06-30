"""round3b 验证 funboost-spider-crawling SKILL — funspider import 路径"""
import importlib
import inspect
import os
import sys
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"r2_spider_imports_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"r2_spider_imports_std_{_ts}"

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
    # SKILL 文档推荐路径: from funboost.contrib.funspider import ...
    expected_path = "funboost.contrib.funspider"
    try:
        mod = importlib.import_module(expected_path)
        report("模块 funboost.contrib.funspider 可导入", True)
    except Exception as e:
        report("模块 funboost.contrib.funspider 可导入", False, str(e))
        print(f"\n=== 最终结果: FAIL ===")
        time.sleep(12)
        os._exit(66)

    checks = [
        ("SimpleSpiderClient", "funboost.contrib.funspider.http"),
        ("AsyncSpiderClient", "funboost.contrib.funspider.http"),
        ("SpiderItem", "funboost.contrib.funspider.item"),
    ]
    for cls_name, expected_module in checks:
        try:
            cls = getattr(mod, cls_name)
            actual_module = cls.__module__
            ok = actual_module == expected_module
            report(
                f"from funboost.contrib.funspider import {cls_name}",
                ok,
                f"定义于 {actual_module}" if ok else f"期望 {expected_module}, 实际 {actual_module}",
            )
        except Exception as e:
            report(f"from funboost.contrib.funspider import {cls_name}", False, str(e))

    # 验证 SKILL 示例中的直接 import 语句
    try:
        from funboost.contrib.funspider import SimpleSpiderClient, AsyncSpiderClient, SpiderItem
        report("合并 import 语句", True, "SimpleSpiderClient, AsyncSpiderClient, SpiderItem")
        report("SimpleSpiderClient 可实例化签名", callable(SimpleSpiderClient))
        report("AsyncSpiderClient 可实例化签名", callable(AsyncSpiderClient))
        report("SpiderItem 是类", inspect.isclass(SpiderItem))
    except Exception as e:
        report("合并 import 语句", False, str(e))

    print(f"\n=== 最终结果: {'PASS' if PASS else 'FAIL'} ===")
    sys.stdout.flush()
    time.sleep(12)
    os._exit(66)
