"""round3 验证: funboost-faas-deploy — Flask 集成示例（仅 import + blueprint 挂载）"""
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"faas_retry_02_flask_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"faas_retry_02_flask_std_{_ts}"

EXAMPLE = "faas-deploy / Flask 集成"
PASS = True


def report(ok: bool, msg: str):
    global PASS
    if not ok:
        PASS = False
    tag = "PASS" if ok else "FAIL"
    print(f"[{tag}] {EXAMPLE}: {msg}")


try:
    from flask import Flask
    from funboost.faas import flask_blueprint

    app = Flask(__name__)
    app.register_blueprint(flask_blueprint)
    report(True, "Flask app.register_blueprint(flask_blueprint) 无报错")

    routes = {(r.rule, frozenset(r.methods)) for r in app.url_map.iter_rules() if r.rule.startswith("/funboost")}
    has_publish = any(rule == "/funboost/publish" and "POST" in methods for rule, methods in routes)
    has_get_result = any(rule == "/funboost/get_result" and "GET" in methods for rule, methods in routes)
    report(has_publish, "Flask 路由 POST /funboost/publish 已挂载")
    report(has_get_result, "Flask 路由 GET /funboost/get_result 已挂载")

    from funboost import boost, BoosterParams, BrokerEnum

    @boost(BoosterParams(
        queue_name="r3_faas_flask_task",
        broker_kind=BrokerEnum.MEMORY_QUEUE,
        concurrent_num=2,
    ))
    def flask_demo_task(x: int):
        return x * 2

    report(True, "@boost 任务定义成功（skill: 正常定义 @boost 任务...）")

except ImportError as e:
    report(False, f"Flask 未安装或导入失败: {e}")
except Exception as e:
    report(False, f"异常: {type(e).__name__}: {e}")

if __name__ == "__main__":
    time.sleep(15)
    print(f"\n=== 最终结果: {'PASS' if PASS else 'FAIL'} ===")
    os._exit(66 if PASS else 1)
