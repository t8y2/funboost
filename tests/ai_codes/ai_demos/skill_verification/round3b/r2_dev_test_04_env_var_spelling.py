"""round3b 验证：developing-funboost-testing SKILL 中三个环境变量拼写与 nb_log 源码一致"""
import glob
import os
import time
from pathlib import Path

_ts = int(time.time())
LOG_DIR = r"D:\pythonlogs\ai_console_outs"
PRINT_NAME = f"r2_dev_test_04_{_ts}"
STD_NAME = f"r2_dev_test_04_std_{_ts}"

# SKILL 文档中的拼写（含 PRINT_WRTIE 故意拼写）
SKILL_ENV_VARS = {
    "LOG_PATH": LOG_DIR,
    "PRINT_WRTIE_FILE_NAME": PRINT_NAME,
    "SYS_STD_FILE_NAME": STD_NAME,
}

# 常见错误拼写（应不存在于 nb_log）
WRONG_SPELLINGS = ["PRINT_WRITE_FILE_NAME", "PRINT_WRITE_NAME", "SYS_STDOUT_FILE_NAME"]

for k, v in SKILL_ENV_VARS.items():
    os.environ[k] = v

# 必须在 import nb_log 前设置环境变量
from nb_log import nb_log_config_default as nb_cfg  # noqa: E402

checks = []

for var_name, expected_val in SKILL_ENV_VARS.items():
    if var_name == "LOG_PATH":
        actual = os.environ.get("LOG_PATH") or nb_cfg.LOG_PATH
    elif var_name == "PRINT_WRTIE_FILE_NAME":
        actual = os.environ.get("PRINT_WRTIE_FILE_NAME") or nb_cfg.PRINT_WRTIE_FILE_NAME
    elif var_name == "SYS_STD_FILE_NAME":
        actual = os.environ.get("SYS_STD_FILE_NAME") or nb_cfg.SYS_STD_FILE_NAME
    else:
        actual = os.environ.get(var_name)
    checks.append((
        f"env_{var_name}",
        actual == expected_val or str(actual) == expected_val,
        f"expected={expected_val!r}, actual={actual!r}",
    ))

for wrong in WRONG_SPELLINGS:
    checks.append((
        f"wrong_spelling_{wrong}",
        wrong not in dir(nb_cfg) and os.environ.get(wrong) is None,
        f"{wrong} 不应被 nb_log 使用",
    ))

# 功能验证：print 应写入 LOG_PATH 下带 PRINT_NAME 的文件
print(f"[ENV_TEST] unique_marker_{_ts}")
time.sleep(2)

print_files = glob.glob(str(Path(LOG_DIR) / f"*{PRINT_NAME}*"))
std_files = glob.glob(str(Path(LOG_DIR) / f"*{STD_NAME}*"))
checks.append((
    "print_file_created",
    len(print_files) >= 1,
    f"glob *{PRINT_NAME}* -> {print_files}",
))
checks.append((
    "std_file_created",
    len(std_files) >= 1,
    f"glob *{STD_NAME}* -> {std_files}",
))

if print_files:
    content = Path(print_files[0]).read_text(encoding="utf-8", errors="replace")
    checks.append((
        "print_file_has_marker",
        f"unique_marker_{_ts}" in content,
        f"file={print_files[0]}",
    ))

if __name__ == "__main__":
    print("[START] r2_dev_test_04_env_var_spelling")
    all_ok = True
    for name, ok, detail in checks:
        tag = "PASS" if ok else "FAIL"
        print(f"[{tag}] {name}: {detail}")
        all_ok = all_ok and ok
    if all_ok:
        print("[PASS] LOG_PATH / PRINT_WRTIE_FILE_NAME / SYS_STD_FILE_NAME 拼写正确且生效")
    else:
        print("[FAIL] 环境变量拼写或生效验证失败")
    time.sleep(15)
    os._exit(66)
