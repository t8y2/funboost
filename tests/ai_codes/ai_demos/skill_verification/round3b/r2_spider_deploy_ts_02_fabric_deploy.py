"""round3b 验证 funboost-remote-deploy SKILL — fabric_deploy import 路径与参数"""
import inspect
import os
import sys
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"r2_fabric_deploy_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"r2_fabric_deploy_std_{_ts}"

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
    # SKILL: from funboost import fabric_deploy 不应存在
    try:
        import funboost
        report("from funboost import fabric_deploy 不应存在", not hasattr(funboost, "fabric_deploy"))
    except Exception as e:
        report("检查 funboost 顶层导出", False, str(e))

    # SKILL 推荐路径
    try:
        from funboost.core.fabric_deploy_helper import fabric_deploy, kill_all_remote_tasks
        report(
            "from funboost.core.fabric_deploy_helper import fabric_deploy",
            callable(fabric_deploy),
            fabric_deploy.__module__,
        )
        report(
            "from funboost.core.fabric_deploy_helper import kill_all_remote_tasks",
            callable(kill_all_remote_tasks),
        )
    except Exception as e:
        report("fabric_deploy_helper import", False, str(e))

    # SKILL 推荐: my_task.fabric_deploy(host, port, user, password, process_num=2)
    try:
        from funboost import boost, BoosterParams, BrokerEnum

        @boost(BoosterParams(
            queue_name=f"r2_fabric_deploy_{_ts}",
            broker_kind=BrokerEnum.MEMORY_QUEUE,
        ))
        def demo_task(x):
            return x

        report("Booster.fabric_deploy 方法存在", hasattr(demo_task, "fabric_deploy"))
        report("Booster.fabric_deploy 可调用", callable(demo_task.fabric_deploy))
    except Exception as e:
        report("Booster.fabric_deploy 方法", False, str(e))

    # 参数签名验证（对照 SKILL 速查表）
    try:
        sig = inspect.signature(fabric_deploy)
        params = sig.parameters
        required = {"booster", "host", "port", "user", "password"}
        report("fabric_deploy 必填参数", required.issubset(params.keys()), str(required))

        skill_optional = {
            "process_num",
            "pkey_file_path",
            "extra_shell_str",
            "only_upload_within_the_last_modify_time",
            "file_volume_limit",
            "invoke_runner_kwargs",
            "python_interpreter",
            "path_pattern_exluded_tuple",
            "file_suffix_tuple_exluded",
            "sftp_log_level",
        }
        report("fabric_deploy SKILL 文档可选参数", skill_optional.issubset(params.keys()))

        defaults = fabric_deploy.__defaults__ or ()
        # process_num 默认 1（最后一个位置参数前若干默认值）
        report("process_num 默认值=1", params["process_num"].default == 1)
        report(
            "invoke_runner_kwargs 默认 pty=True",
            params["invoke_runner_kwargs"].default.get("pty") is True,
        )
        report(
            "invoke_runner_kwargs 默认 warn=False",
            params["invoke_runner_kwargs"].default.get("warn") is False,
        )

        booster_sig = inspect.signature(demo_task.fabric_deploy)
        booster_params = set(booster_sig.parameters.keys())
        helper_params = set(params.keys()) - {"booster"}
        report(
            "Booster.fabric_deploy 参数与 helper 一致(除 booster)",
            booster_params == helper_params,
            f"booster_only={booster_params - helper_params}, helper_only={helper_params - booster_params}",
        )
    except Exception as e:
        report("fabric_deploy 签名检查", False, str(e))

    print(f"\n=== 最终结果: {'PASS' if PASS else 'FAIL'} ===")
    sys.stdout.flush()
    time.sleep(12)
    os._exit(66)
