# -*- coding: utf-8 -*-
"""
Funboost Workflow - Publisher/Consumer Mixin

提供 WorkflowPublisherMixin 和 WorkflowConsumerMixin，
用于在消息中注入和提取工作流上下文，实现跨任务的上下文传递。

使用方式：
1. 直接使用预配置的 WorkflowBoosterParams（推荐）
2. 或手动指定 consumer_override_cls 和 publisher_override_cls
"""

import copy
import typing
import contextvars

from funboost.publishers.base_publisher import AbstractPublisher
from funboost.consumers.base_consumer import AbstractConsumer
from funboost.core.serialization import Serialization

# 使用 contextvars 统一管理上下文，同时支持多线程和异步协程场景
# 参考 funboost/core/current_task.py 的实现
_workflow_context_var: contextvars.ContextVar[typing.Optional[dict]] = contextvars.ContextVar(
    'workflow_context', default=None
)


class WorkflowPublisherMixin(AbstractPublisher):
    """
    工作流发布者 Mixin

    功能：
    1. 在发布消息时，检查当前上下文中是否有工作流信息
    2. 如果有，将工作流上下文注入到消息的 extra 字段中
    3. 支持链路追踪：可以追踪任务是由哪个上游任务触发的

    消息中的工作流上下文包含：
    - workflow_id: 工作流唯一标识
    - parent_task_id: 父任务 ID（谁触发了这个任务）
    - chain_depth: 链条深度（用于调试）

    覆写 _execute_publish 而非 publish，确保 publish/push/delay 三种调用方式
    都能正确注入工作流上下文。
    """

    @classmethod
    def set_workflow_context(cls, workflow_ctx: dict):
        """设置当前线程/协程的工作流上下文"""
        _workflow_context_var.set(workflow_ctx)

    @classmethod
    def get_workflow_context(cls) -> typing.Optional[dict]:
        """获取当前线程/协程的工作流上下文"""
        return _workflow_context_var.get()

    @classmethod
    def clear_workflow_context(cls):
        """清除当前线程/协程的工作流上下文"""
        _workflow_context_var.set(None)

    def _get_workflow_context_from_msg_or_contextvars(self, msg: dict) -> typing.Optional[dict]:
        """
        获取工作流上下文，优先从消息中获取（aio_publish 场景），否则从 contextvars 获取
        """
        aio_ctx = msg.get('extra', {}).get('_workflow_context_from_aio')
        if aio_ctx:
            return aio_ctx
        return self.get_workflow_context()

    def _inject_workflow_context_to_msg(self, msg: dict):
        """
        将当前 contextvars 中的工作流上下文注入到消息中
        用于 aio_publish 场景：在 asyncio 线程先捕获上下文，然后通过消息传递到 executor 线程
        """
        workflow_ctx = self.get_workflow_context()
        if workflow_ctx:
            if 'extra' not in msg:
                msg['extra'] = {}
            msg['extra']['_workflow_context_from_aio'] = workflow_ctx

    def _execute_publish(self, publish_msg_context):
        msg_dict = publish_msg_context.msg_dict
        workflow_ctx = self._get_workflow_context_from_msg_or_contextvars(msg_dict)

        if workflow_ctx:
            msg_ctx = {
                'workflow_id': workflow_ctx.get('workflow_id'),
                'parent_task_id': workflow_ctx.get('current_task_id'),
                'chain_depth': workflow_ctx.get('chain_depth', 0) + 1,
            }
            msg_dict.setdefault('extra', {})['workflow_context'] = msg_ctx
            msg_dict.get('extra', {}).pop('_workflow_context_from_aio', None)

            if isinstance(publish_msg_context.msg_json, str):
                publish_msg_context.msg_json = Serialization.to_json_str(msg_dict)

        return super()._execute_publish(publish_msg_context)

    async def aio_publish(self, msg, task_id=None, task_options=None):
        """
        asyncio 生态下发布消息，处理跨线程的工作流上下文传递。

        关键问题：父类 aio_publish 使用 run_in_executor 在线程池执行，
        但 contextvars 不会自动跨线程传递。

        解决方案：在当前 asyncio 线程先捕获 workflow_context 注入到消息中，
        然后 _execute_publish 在 executor 线程中从消息恢复上下文。
        """
        msg = copy.deepcopy(msg)
        if isinstance(msg, dict):
            self._inject_workflow_context_to_msg(msg)
        return await super().aio_publish(msg, task_id, task_options)


class WorkflowConsumerMixin(AbstractConsumer):
    """
    工作流消费者 Mixin
    
    功能：
    1. 在执行任务前，从消息中提取工作流上下文
    2. 将上下文保存到 contextvars，以便子任务继承（同时支持多线程和异步协程）
    3. 执行完成后清理上下文
    
    这样，当消费函数内部调用 other_task.push() 时，
    WorkflowPublisherMixin 可以从 contextvars 获取上下文并注入到子任务消息中。
    """
    
    def _extract_workflow_context(self, kw: dict) -> typing.Optional[dict]:
        """从消息中提取工作流上下文"""
        return kw['body'].get('extra', {}).get('workflow_context')
    
    def _run(self, kw: dict):
        """
        同步消费函数执行，注入工作流上下文
        """
        # 1. 提取工作流上下文
        msg_ctx = self._extract_workflow_context(kw)
        
        if msg_ctx:
            # 构建运行时上下文（添加 current_task_id，用于发布子任务时设置 parent_task_id）
            runtime_ctx = {
                'workflow_id': msg_ctx.get('workflow_id'),
                'parent_task_id': msg_ctx.get('parent_task_id'),
                'chain_depth': msg_ctx.get('chain_depth', 0),
                'current_task_id': kw['body']['extra'].get('task_id'),  # 当前任务自己的 ID
            }
            
            # 保存到 contextvars（同时支持多线程和 asyncio）
            WorkflowPublisherMixin.set_workflow_context(runtime_ctx)
        
        try:
            return super()._run(kw)
        finally:
            # 清理上下文
            WorkflowPublisherMixin.clear_workflow_context()
    
    async def _async_run(self, kw: dict):
        """
        异步消费函数执行，注入工作流上下文
        """
        # 1. 提取工作流上下文
        msg_ctx = self._extract_workflow_context(kw)
        
        if msg_ctx:
            # 构建运行时上下文（添加 current_task_id，用于发布子任务时设置 parent_task_id）
            runtime_ctx = {
                'workflow_id': msg_ctx.get('workflow_id'),
                'parent_task_id': msg_ctx.get('parent_task_id'),
                'chain_depth': msg_ctx.get('chain_depth', 0),
                'current_task_id': kw['body']['extra'].get('task_id'),  # 当前任务自己的 ID
            }
            
            # 保存到 contextvars（自动支持 asyncio 协程隔离）
            WorkflowPublisherMixin.set_workflow_context(runtime_ctx)
        
        try:
            return await super()._async_run(kw)
        finally:
            # 清理上下文
            WorkflowPublisherMixin.clear_workflow_context()


def get_current_workflow_context() -> typing.Optional[dict]:
    """
    获取当前工作流上下文（供用户代码使用）
    
    用法：
    ```python
    from funboost.workflow import get_current_workflow_context
    
    @boost(WorkflowBoosterParams(queue_name='my_task'))
    def my_task(x):
        ctx = get_current_workflow_context()
        if ctx:
            print(f"Workflow ID: {ctx.get('workflow_id')}")
            print(f"Parent Task: {ctx.get('parent_task_id')}")
    ```
    """
    return WorkflowPublisherMixin.get_workflow_context()
