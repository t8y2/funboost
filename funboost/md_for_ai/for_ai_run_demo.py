"""
ai写脚本自动运行时候，要模仿这个例子，这个例子是专门给ai写运行例子用的，普通人写的脚本不是按照这么写

1. 模仿 LOG_PATH  PRINT_WRTIE_FILE_NAME  SYS_STD_FILE_NAME 环境变量的设置，这写在代码最开始，为了方便ai从文件检查运行输出，ai不依赖捕获控制台输出。
ai应该运行后主动去读取 PRINT_WRTIE_FILE_NAME  SYS_STD_FILE_NAME 这两个nb_log生成的黑科技文件。

注意：ai当然也可以在启动python脚本之前，先在命令行设置这三个环境变量，而不是在python脚本中去写死os.environ



PRINT_WRTIE_FILE_NAME 只包含print的，文件更小更纯粹，更方便ai检查仅自己亲自写的print的，不关心框架输出的日志。
SYS_STD_FILE_NAME 包含了print 也包含了funboost框架的大量日志，相当于方便ai全量检查控制台所有输出。

说明：
nb_log 用了黑科技，会把所有的print自动加上时间和行号，ai如果非常不想print自动被加上时间和行号那就用 sys.stdout来打印。
print在文件里面实际内容列举一个如下：
 `2026-05-15 11:00:43  "d:\codes\funboost\tests\ai_codes\ai_demos\rpc_demo\rpc_demo.py:27" -[print]-multiply_task- 计算: 3 * 4 = 12`

2. 在代码最末尾加上，强制结束。
time.sleep(20) # 休眠一段时间，ai自己去评估消费所需的时间大小，然后强制退出，因为funboost consume启动后，代码进入循环消费不会自动结束
print('20秒到了，现在自动强制退出程序')
os._exit(66) # 强制退出脚本，防止ai的agent调用一直等待脚本结束
"""

import os


# PRINT_WRTIE_FILE_NAME 是 黑科技配置,远超一般日志包所需要管辖的范畴,是nb_log 独门绝技.
# 项目中的print是否自动写入到文件中。值为None则不重定向print到文件中。 自动每天一个文件， 2023-06-30.my_proj.print,生成的文件位置在定义的LOG_PATH
# 如果你设置了环境变量，export PRINT_WRTIE_FILE_NAME="my_proj.print" (linux临时环境变量语法，windows语法自己百度这里不举例),那就优先使用环境变量中设置的文件名字，而不是nb_log_config.py中设置的名字

# SYS_STD_FILE_NAME 是 黑科技配置,远超一般日志包所需要管辖的范畴,是nb_log 独门绝技.
# 项目中的所有标准输出（不仅包括print，还包括了streamHandler日志）都写入到这个文件，为None将不把标准输出重定向到文件。自动每天一个文件， 2023-06-30.my_proj.std,生成的文件位置在定义的LOG_PATH
# 如果你设置了环境变量，export SYS_STD_FILE_NAME="my_proj.std"  (linux临时环境变量语法，windows语法自己百度这里不举例),那就优先使用环境变量中设置的文件名字，，而不是nb_log_config.py中设置的名字
# 这个相当于是 nohup 自动重定向所有屏幕输出流到一个nohup.out文件的功能了,这个是nb_log日志包的独有黑科技功能,logging 和loguru没这种功能.
# 相对如不同命名空间的logger写入到十几个不同的日志文件,这个SYS_STD_FILE_NAME把项目的所有日志单独重新汇总在一个文件.

# 注意：ai当然也可以在启动python脚本之前，先在命令行设置这三个环境变量，而不是在python脚本中去写死os.environ
os.environ["LOG_PATH"] = 'd:/pythonlogs/ai_console_outs' # 指定的文件件，ai不用改
os.environ['PRINT_WRTIE_FILE_NAME'] = 'ai自己去取个合适的唯一名字print重定向.print' # ai按需修改成唯一名字，所有print会写到这个文件，方便ai检查print打印
os.environ['SYS_STD_FILE_NAME'] = 'ai自己去取个合适的唯一的名字std重定向.std' # ai按需修改成唯一名字，所有sys.stdout和stderr会写到这个文件，方便ai检查所有输出

"""
这样设置后d盘的 d:/pythonlogs/ai_console_outs 的文件夹下将会有  `2026-05-15.0001.合适的唯一的名字std重定向.std` 和 `2026-05-15.0001.合适的唯一名字print重定向.print`
注意文件名字前面可能有日期时间，ai需要模糊搜索文件名
"""





# ai必须在最开头些上面的三个环境变量，再开始写别的代码
#   ----------- 再开始写别的代码 ---------------

import nb_log  # 导入 nb_log ，如果导入了funboost，就不需要亲自导入nb_log

import time
from funboost import boost, BrokerEnum, BoosterParams


# 示例1: 最简单的任务函数
@boost(BoosterParams(
    queue_name="demo_queue_1",
    broker_kind=BrokerEnum.REDIS,  # redis已经安装和配置好了，请ai无需操心redis有没有安装和配置
    qps=5,  # 每秒执行5次
    concurrent_num=10,  # 并发数为10
))
def add_task(x, y):
    """简单的加法任务"""
    print(f'计算: {x} + {y} = {x + y}')
    time.sleep(0.1)  # 模拟耗时操作
    return x + y


if __name__ == '__main__':
    for i in range(10):
        add_task.push(i, i * 2)
        add_task.publish({"x":i*10, "y": i * 20})

    add_task.consume()

    time.sleep(20) # 休眠一段时间，ai自己去评估消费所需的时间大小，然后强制退出，因为funboost consume启动后，代码进入循环消费不会自动结束
    print('20秒到了，现在自动强制退出程序')
    os._exit(66) # 强制退出脚本，防止ai的agent调用一直等待脚本结束。这么写是为了ai验证脚本，人工启动的脚本不需要退出所以不需要exit。

    