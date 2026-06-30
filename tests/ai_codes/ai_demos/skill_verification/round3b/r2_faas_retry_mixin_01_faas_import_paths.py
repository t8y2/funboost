"""round3b r2: funboost-faas-deploy — fastapi_router / flask_blueprint import 路径验证"""
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"r2_faas_import_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"r2_faas_import_std_{_ts}"

EXAMPLE = "faas-deploy / import paths"
PASS = True


def report(ok: bool, msg: str):
    global PASS
    if not ok:
        PASS = False
    tag = "PASS" if ok else "FAIL"
    print(f"[{tag}] {EXAMPLE}: {msg}")


try:
    # SKILL 文档写法: from funboost.faas import fastapi_router
    from funboost.faas import fastapi_router
    report(fastapi_router is not None, "from funboost.faas import fastapi_router 成功")
    report(
        getattr(fastapi_router, "prefix", None) == "/funboost",
        f"fastapi_router.prefix={getattr(fastapi_router, 'prefix', None)!r}",
    )

    from funboost.faas import flask_blueprint
    report(flask_blueprint is not None, "from funboost.faas import flask_blueprint 成功")
    report(
        getattr(flask_blueprint, "url_prefix", None) == "/funboost",
        f"flask_blueprint.url_prefix={getattr(flask_blueprint, 'url_prefix', None)!r}",
    )

    # 底层模块路径也应可达（IDE type-checking 路径）
    from funboost.faas.fastapi_adapter import fastapi_router as far2
    from funboost.faas.flask_adapter import flask_blueprint as fbp2
    report(far2 is fastapi_router, "funboost.faas.fastapi_adapter.fastapi_router 与 faas 包导出同一对象")
    report(fbp2 is flask_blueprint, "funboost.faas.flask_adapter.flask_blueprint 与 faas 包导出同一对象")

    from fastapi import FastAPI
    from flask import Flask

    app_f = FastAPI()
    app_f.include_router(fastapi_router)
    routes = [r.path for r in app_f.routes if hasattr(r, "path")]
    report("/funboost/publish" in routes, f"FastAPI 挂载后含 /funboost/publish, routes={len(routes)}")

    app_fl = Flask(__name__)
    app_fl.register_blueprint(flask_blueprint)
    bp_routes = [str(r) for r in app_fl.url_map.iter_rules() if str(r).startswith("/funboost")]
    report(any("/funboost/publish" in r for r in bp_routes), f"Flask 挂载后含 /funboost/publish, rules={bp_routes[:3]}")

except Exception as e:
    report(False, f"异常: {type(e).__name__}: {e}")

if __name__ == "__main__":
    time.sleep(15)
    print(f"\n=== 最终结果: {'PASS' if PASS else 'FAIL'} ===")
    os._exit(66 if PASS else 1)
