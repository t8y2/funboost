"""round3b 验证：AbstractPublisher/AbstractConsumer 抽象方法列表与 SKILL 一致"""
import abc
import inspect
import os
import time

_ts = int(time.time())
os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
os.environ["PRINT_WRTIE_FILE_NAME"] = f"r2_dev_test_02_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"r2_dev_test_02_std_{_ts}"

from funboost.publishers.base_publisher import AbstractPublisher
from funboost.consumers.base_consumer import AbstractConsumer

# SKILL developing-funboost-broker 列出的必须实现方法
SKILL_PUBLISHER_ABSTRACT = {"_publish_impl", "clear", "get_message_count", "close"}
SKILL_CONSUMER_ABSTRACT = {"_dispatch_task", "_confirm_consume", "_requeue"}


def get_abstract_methods(cls):
    abstract = set()
    for name, member in inspect.getmembers(cls):
        if getattr(member, "__isabstractmethod__", False):
            abstract.add(name)
    return abstract


pub_abstract = get_abstract_methods(AbstractPublisher)
con_abstract = get_abstract_methods(AbstractConsumer)

checks = []
checks.append((
    "publisher_abstract_match",
    pub_abstract == SKILL_PUBLISHER_ABSTRACT,
    f"skill={sorted(SKILL_PUBLISHER_ABSTRACT)}, source={sorted(pub_abstract)}",
))
checks.append((
    "consumer_abstract_match",
    con_abstract == SKILL_CONSUMER_ABSTRACT,
    f"skill={sorted(SKILL_CONSUMER_ABSTRACT)}, source={sorted(con_abstract)}",
))
checks.append((
    "publisher_no_extra_abstract",
    pub_abstract.issubset(SKILL_PUBLISHER_ABSTRACT) and SKILL_PUBLISHER_ABSTRACT.issubset(pub_abstract),
    f"extra_in_source={pub_abstract - SKILL_PUBLISHER_ABSTRACT}, missing={SKILL_PUBLISHER_ABSTRACT - pub_abstract}",
))
checks.append((
    "consumer_no_extra_abstract",
    con_abstract.issubset(SKILL_CONSUMER_ABSTRACT) and SKILL_CONSUMER_ABSTRACT.issubset(con_abstract),
    f"extra_in_source={con_abstract - SKILL_CONSUMER_ABSTRACT}, missing={SKILL_CONSUMER_ABSTRACT - con_abstract}",
))

# custom_init 在 SKILL 中标注为非抽象
checks.append((
    "custom_init_not_abstract_publisher",
    "custom_init" not in pub_abstract,
    f"custom_init abstract={('custom_init' in pub_abstract)}",
))
checks.append((
    "custom_init_not_abstract_consumer",
    "custom_init" not in con_abstract,
    f"custom_init abstract={('custom_init' in con_abstract)}",
))

if __name__ == "__main__":
    print("[START] r2_dev_test_02_abstract_methods")
    all_ok = True
    for name, ok, detail in checks:
        tag = "PASS" if ok else "FAIL"
        print(f"[{tag}] {name}: {detail}")
        all_ok = all_ok and ok
    if all_ok:
        print("[PASS] 抽象方法列表与 SKILL 完全一致")
    else:
        print("[FAIL] 抽象方法列表与 SKILL 不一致")
    time.sleep(15)
    os._exit(66)
