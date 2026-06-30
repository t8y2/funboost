"""round3b r2: funboost-advanced-retry — ExceptionForRequeue / ExceptionForPushToDlxqueue import 路径"""
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"r2_exception_import_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"r2_exception_import_std_{_ts}"

EXAMPLE = "advanced-retry / exception imports"
PASS = True


def report(ok: bool, msg: str):
    global PASS
    if not ok:
        PASS = False
    tag = "PASS" if ok else "FAIL"
    print(f"[{tag}] {EXAMPLE}: {msg}")


try:
    # SKILL 文档写法
    from funboost import ExceptionForRequeue, ExceptionForPushToDlxqueue, ExceptionForRetry
    report(True, "from funboost import ExceptionForRequeue, ExceptionForPushToDlxqueue 成功")

    # 源码实际定义位置
    from funboost.core.exceptions import (
        ExceptionForRequeue as EFR_core,
        ExceptionForPushToDlxqueue as EPD_core,
        ExceptionForRetry as EFT_core,
    )
    report(ExceptionForRequeue is EFR_core, "funboost 包导出 ExceptionForRequeue 与 core.exceptions 一致")
    report(ExceptionForPushToDlxqueue is EPD_core, "funboost 包导出 ExceptionForPushToDlxqueue 与 core.exceptions 一致")
    report(ExceptionForRetry is EFT_core, "funboost 包导出 ExceptionForRetry 与 core.exceptions 一致")

    # 可实例化 / raise
    try:
        raise ExceptionForRequeue("test requeue")
    except ExceptionForRequeue as e:
        report(True, f"ExceptionForRequeue 可 raise/catch: {e!r}")

    try:
        raise ExceptionForPushToDlxqueue("test dlx")
    except ExceptionForPushToDlxqueue as e:
        report(True, f"ExceptionForPushToDlxqueue 可 raise/catch: {e!r}")

    # base_consumer 内部 import 路径核对
    import inspect
    from funboost.consumers import base_consumer as bc_mod

    src_head = inspect.getsourcefile(bc_mod)
    with open(src_head, encoding="utf-8") as f:
        head_lines = "".join(f.readlines()[:100])
    report(
        "from funboost.core.exceptions import ExceptionForRequeue, ExceptionForPushToDlxqueue" in head_lines,
        "base_consumer.py 从 funboost.core.exceptions 导入异常类",
    )

except Exception as e:
    report(False, f"异常: {type(e).__name__}: {e}")

if __name__ == "__main__":
    time.sleep(15)
    print(f"\n=== 最终结果: {'PASS' if PASS else 'FAIL'} ===")
    os._exit(66 if PASS else 1)
