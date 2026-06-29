# -*- coding: utf-8 -*-
"""
Funboost 综合能力演示 Demo
展示：基础消费、RPC结果获取、QPS控频、并发模式、延时任务、工作流编排
"""
import time
from funboost import boost, BrokerEnum, enable_ctrl_c_quit_on_windows, ConcurrentModeEnum
from funboost.timing_job.timing_push import ApsJobAdder
from funboost.workflow import chain


@boost(queue_name='demo_basic', broker_kind=BrokerEnum.REDIS, concurrent_num=5)
def basic_task(name: str, count: int):
    """基础任务：演示简单的发布-消费模式"""
    time.sleep(0.5)
    print(f'[基础任务] {name} - 第 {count} 次执行')
    return f'{name}_done_{count}'


@boost(queue_name='demo_rpc', broker_kind=BrokerEnum.REDIS, concurrent_num=3, is_using_rpc_mode=True)
def rpc_task(x: int, y: int):
    """RPC任务：演示获取消费结果"""
    time.sleep(0.3)
    result = x * y
    print(f'[RPC任务] {x} * {y} = {result}')
    return result


@boost(queue_name='demo_qps', broker_kind=BrokerEnum.REDIS, concurrent_num=10, qps=2)
def qps_limited_task(data: str):
    """QPS控频任务：精确控制每秒执行次数"""
    print(f'[QPS控频] 处理数据: {data}, 时间: {time.strftime("%H:%M:%S")}')


@boost(queue_name='demo_concurrent', broker_kind=BrokerEnum.REDIS, concurrent_num=8, concurrent_mode=ConcurrentModeEnum.THREADING)
def concurrent_task(task_id: int):
    """并发任务：演示多线程并发执行"""
    time.sleep(1)
    print(f'[并发任务] 任务 {task_id} 在线程中完成')


@boost(queue_name='demo_delay', broker_kind=BrokerEnum.REDIS, concurrent_num=3)
def delay_task(msg: str):
    """延时任务：演示消息延迟消费"""
    print(f'[延时任务] 收到消息: {msg}, 当前时间: {time.strftime("%H:%M:%S")}')


@boost(queue_name='demo_workflow', broker_kind=BrokerEnum.REDIS, concurrent_num=3)
def workflow_step(step_name: str, data: int = 0):
    """工作流步骤函数"""
    result = data + 10
    print(f'[工作流] {step_name}: 输入={data}, 输出={result}')
    return result


def demo_basic():
    """演示1：基础发布消费"""
    print('\n' + '=' * 50)
    print('演示1：基础发布消费模式')
    print('=' * 50)
    basic_task.consume()
    for i in range(3):
        basic_task.push(f'任务A', i + 1)


def demo_rpc():
    """演示2：RPC模式获取结果"""
    print('\n' + '=' * 50)
    print('演示2：RPC模式 - 同步获取消费结果')
    print('=' * 50)
    rpc_task.consume()
    
    result1 = rpc_task.push(3, 7)
    print(f'等待结果1: 3 * 7 = {result1.result}')
    
    result2 = rpc_task.push(10, 20)
    print(f'等待结果2: 10 * 20 = {result2.result}')


def demo_qps():
    """演示3：QPS精确控频"""
    print('\n' + '=' * 50)
    print('演示3：QPS控频 - 每秒最多执行2次')
    print('=' * 50)
    qps_limited_task.consume()
    
    print('快速发布10条消息，观察消费速度...')
    for i in range(10):
        qps_limited_task.push(f'data_{i}')


def demo_concurrent():
    """演示4：多线程并发"""
    print('\n' + '=' * 50)
    print('演示4：8线程并发执行')
    print('=' * 50)
    concurrent_task.consume()
    
    start = time.time()
    for i in range(8):
        concurrent_task.push(i + 1)
    print(f'8个任务已发布，预计约1秒完成（并发执行）')


def demo_delay():
    """演示5：延时任务"""
    print('\n' + '=' * 50)
    print('演示5：延时任务 - 5秒后消费')
    print('=' * 50)
    delay_task.consume()
    
    print(f'当前时间: {time.strftime("%H:%M:%S")}')
    delay_task.push('这是延时5秒的消息', delay_seconds=5)
    print('消息已发布，5秒后才会被消费')


def demo_workflow():
    """演示6：工作流编排"""
    print('\n' + '=' * 50)
    print('演示6：工作流编排 - Chain链式执行')
    print('=' * 50)
    workflow_step.consume()
    
    wf = chain(
        workflow_step.s('步骤1', 0),
        workflow_step.s('步骤2'),
        workflow_step.s('步骤3'),
    )
    wf.apply()
    print('工作流已提交，观察链式执行效果')


def demo_timer():
    """演示7：定时任务"""
    print('\n' + '=' * 50)
    print('演示7：定时任务 - 每3秒执行一次')
    print('=' * 50)
    basic_task.consume()
    
    ApsJobAdder(basic_task, job_store_kind='memory').add_push_job(
        trigger='interval',
        seconds=3,
        args=('定时任务', 999)
    )
    print('定时任务已添加，每3秒自动发布一次')


if __name__ == '__main__':
    print('\n' + '#' * 60)
    print('#  Funboost 综合能力演示 Demo')
    print('#  展示：基础消费、RPC、QPS控频、并发、延时、工作流')
    print('#' * 60)
    
    demo_basic()
    demo_rpc()
    demo_qps()
    demo_concurrent()
    demo_delay()
    demo_workflow()
    demo_timer()
    
    print('\n' + '=' * 50)
    print('所有演示已启动，按 Ctrl+C 退出...')
    print('=' * 50)
    enable_ctrl_c_quit_on_windows()
