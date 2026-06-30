"""round3 验证: funboost-faas-deploy — 发布端 Web 应用分离示例"""
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"faas_retry_03_webapp_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"faas_retry_03_webapp_std_{_ts}"

EXAMPLE = "faas-deploy / 发布端 Web 应用"
PASS = True


def report(ok: bool, msg: str):
    global PASS
    if not ok:
        PASS = False
    tag = "PASS" if ok else "FAIL"
    print(f"[{tag}] {EXAMPLE}: {msg}")


try:
    from fastapi import FastAPI
    from funboost.faas import fastapi_router
    from funboost.constant import EnvConst

    app = FastAPI()
    app.include_router(fastapi_router)
    report(True, "web_app.py 模式: FastAPI + fastapi_router 挂载成功")

    env_key = EnvConst.FUNBOOST_FAAS_IS_USE_LOCAL_BOOSTER
    report(
        env_key == "funboost.faas.is_use_local_booster",
        f"环境变量名 {env_key!r} 与 skill 描述一致",
    )

except Exception as e:
    report(False, f"异常: {type(e).__name__}: {e}")

if __name__ == "__main__":
    time.sleep(15)
    print(f"\n=== 最终结果: {'PASS' if PASS else 'FAIL'} ===")
    os._exit(66 if PASS else 1)
