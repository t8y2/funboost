"""
nb_log GIL 崩溃可复现 Demo

环境:
- Windows 11
- Python 3.10
- nb-log 14.4

问题:
nb_log 的 BulkFileWritter 后台线程与 time.sleep() 冲突，导致 GIL 崩溃。

错误信息:
Fatal Python error: PyEval_SaveThread: the function must be called with the GIL held,
but the GIL is released (the current Python thread state is NULL)

复现步骤:
1. 在 Windows 上运行此脚本
2. 等待 1-10 秒
3. 观察 GIL 崩溃

临时修复:
修改 nb_log/rotate_file_writter.py 第 172 行:
    OsFileWritter = FileWritter if os.name == 'posix' else BulkFileWritter
改为:
    OsFileWritter = FileWritter
"""

import sys
import time
from pathlib import Path



# 导入 nb_log 的 logger
from nb_log import get_logger

logger = get_logger(
    "gil_bug_demo",
    log_filename="gil_bug_demo.log",
    error_log_filename="gil_bug_demo_error.log",
)


def main():
    """主函数 - 模拟简化架构的主循环"""
    print("=" * 60)
    print("nb_log GIL 崩溃复现 Demo")
    print("=" * 60)

    logger.info("启动 Demo")
    logger.info("PID: %d", __import__('os').getpid())

    # 模拟主循环
    iteration = 0
    while True:
        try:
            iteration += 1
            logger.info(f"迭代 {iteration}")

            # 模拟业务逻辑
            time.sleep(0.1)  # 这里会触发 GIL 崩溃

            if iteration >= 100:
                logger.info("完成 100 次迭代，退出")
                break

        except KeyboardInterrupt:
            logger.info("收到键盘中断")
            break
        except Exception as e:
            logger.error(f"异常: {e}", exc_info=True)
            break

    logger.info("Demo 结束")


if __name__ == "__main__":
    main()
