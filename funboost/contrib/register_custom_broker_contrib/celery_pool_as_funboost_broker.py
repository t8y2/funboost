# -*- coding: utf-8 -*-
"""
演示：复用 funboost.assist.celery_pool.CeleryPool，
     通过 register_custom_broker 将其注册为 funboost 的自定义 broker_kind。

核心思路：
    CeleryPool 已经封装了 Celery app 创建、worker 自动启动、universal_task 注册等逻辑。
    本方案直接复用 CeleryPool 实例的 app 和 _start_worker()，
    只需在其 app 上额外注册一个 "funboost 消息处理 task"，就能桥接 funboost 的消息协议。

    Publisher：通过 pool.app.send_task() 发送 funboost 消息
    Consumer：在 pool.app 上注册 task 解析 funboost 消息并调用消费函数
    Worker：  复用 pool._start_worker() 自动在后台线程启动

运行方式：
    D:\\ProgramData\\Miniconda3\\envs\\py39b\\python.exe tests/ai_codes/celery_pool_as_funboost_broker.py
"""

import json
import time
import threading
import typing
import uuid

from funboost import (
    register_custom_broker, AbstractConsumer, AbstractPublisher,
    register_broker_exclusive_config_default,
    boost, BoosterParams,
)
from funboost.assist.celery_pool import CeleryPool

# ============================================================================
# 常量与共享池
# ============================================================================

BROKER_KIND_CELERY_POOL = 'CELERY_POOL'

_pool_cache: typing.Dict[str, CeleryPool] = {}
_pool_cache_lock = threading.Lock()


def _get_or_create_pool(queue_name: str, config: dict) -> CeleryPool:
    """
    获取或创建指定 queue 的 CeleryPool 实例。
    同一个 queue_name 的 Publisher 和 Consumer 共享同一个 CeleryPool。
    首次创建时 is_auto_start_worker=False，由 Consumer 显式启动。
    """
    with _pool_cache_lock:
        if queue_name in _pool_cache:
            return _pool_cache[queue_name]

        pool = CeleryPool(
            broker_url=config.get('broker_url', 'redis://localhost:6379/0'),
            result_backend=config.get('result_backend'),
            concurrent_num=config.get('concurrent_num', 4),
            pool_type=config.get('pool_type', 'threads'),
            queue_name=queue_name,
            is_auto_start_worker=False,
            worker_loglevel=config.get('worker_loglevel', 'WARNING'),
            worker_startup_timeout=config.get('worker_startup_timeout', 3.0),
        )
        _pool_cache[queue_name] = pool
        return pool


# ============================================================================
# Publisher：复用 CeleryPool.app 发送 funboost 消息
# ============================================================================

class CeleryPoolPublisher(AbstractPublisher):

    def custom_init(self):
        super().custom_init()
        config = self.publisher_params.broker_exclusive_config
        self._pool = _get_or_create_pool(self.queue_name, config)
        self._task_name = f'funboost_celery_pool_{self.queue_name}'

    def _publish_impl(self, msg: str):
        return self._pool.app.send_task(
            name=self._task_name,
            kwargs={'funboost_msg': msg},
            queue=self.queue_name,
        )

    def _execute_publish(self, publish_msg_context):
        """覆写基类，返回 Celery 原生 AsyncResult 而非 funboost AsyncResult"""
        t_start = time.time()
        celery_result = self._wrapped_publish_impl(publish_msg_context.msg_json)
        current_time = time.time()
        if self.logger.isEnabledFor(10):
            self.logger.debug(
                f'向{self._queue_name} 队列，推送消息 '
                f'耗时{round(current_time - t_start, 4)}秒  '
                f'{publish_msg_context.msg_function_kw}',
                extra={'task_id': publish_msg_context.task_id},
            )
        self.count_per_minute += 1
        self.publish_msg_num_total += 1
        if current_time - self._current_time > 10:
            with self._lock_for_count:
                if current_time - self._current_time > 10:
                    self.logger.info(
                        f'10秒内推送了 {self.count_per_minute} 条消息,'
                        f'累计推送了 {self.publish_msg_num_total} 条消息到 '
                        f'{self._queue_name} 队列中')
                    self._init_count()
        self._after_publish(publish_msg_context)
        return celery_result

    def clear(self):
        pass

    def get_message_count(self):
        return -1

    def close(self):
        pass


# ============================================================================
# Consumer：复用 CeleryPool.app 注册 task + CeleryPool._start_worker()
# ============================================================================

class CeleryPoolConsumer(AbstractConsumer):

    BROKER_KIND = None

    def custom_init(self):
        super().custom_init()
        config = self.consumer_params.broker_exclusive_config
        self._pool = _get_or_create_pool(self.queue_name, config)

        task_name = f'funboost_celery_pool_{self.queue_name}'
        consuming_func = self.consuming_function
        consumer_logger = self.logger
        max_retries = self.consumer_params.max_retry_times
        app = self._pool.app

        app.conf.task_routes.update({task_name: {'queue': self.queue_name}})

        @app.task(name=task_name, bind=True, max_retries=max_retries)
        def handle_funboost_msg(celery_self, funboost_msg: str):
            try:
                msg_dict = json.loads(funboost_msg)
            except (json.JSONDecodeError, TypeError):
                consumer_logger.error(f'无法解析消息: {funboost_msg}')
                return

            extra = msg_dict.pop('extra', {})
            msg_dict.pop('extra_params', None)
            task_id = extra.get('task_id', 'unknown')

            consumer_logger.debug(
                f'[CELERY_POOL] task_id={task_id} '
                f'执行 {consuming_func.__name__}({msg_dict})'
            )
            try:
                result = consuming_func(**msg_dict)
                consumer_logger.debug(
                    f'[CELERY_POOL] task_id={task_id} 完成, result={result}'
                )
                return result
            except Exception as exc:
                retries = celery_self.request.retries
                if retries < max_retries:
                    consumer_logger.warning(
                        f'[CELERY_POOL] task_id={task_id} '
                        f'第{retries + 1}次出错: {exc}, 重试'
                    )
                    raise celery_self.retry(exc=exc, countdown=0)
                else:
                    consumer_logger.error(
                        f'[CELERY_POOL] task_id={task_id} '
                        f'达到最大重试{max_retries}次, 放弃: {exc}'
                    )
                    raise

    def start_consuming_message(self):
        if not self._pool._worker_thread:
            self._pool._start_worker()
            self.logger.info(
                f'[CELERY_POOL] 复用 CeleryPool worker: '
                f'queue={self.queue_name}, pool={self._pool.pool_type}, '
                f'concurrency={self._pool.concurrent_num}'
            )
        super().start_consuming_message()

    def _dispatch_task(self):
        while True:
            time.sleep(100)

    def _confirm_consume(self, kw):
        pass

    def _requeue(self, kw):
        pass


# ============================================================================
# 注册 broker
# ============================================================================

register_broker_exclusive_config_default(
    BROKER_KIND_CELERY_POOL,
    {
        'broker_url': 'redis://localhost:6379/0',
        'result_backend': None,
        'concurrent_num': 4,
        'pool_type': 'threads',
        'worker_loglevel': 'WARNING',
        'worker_startup_timeout': 3.0,
    }
)

register_custom_broker(BROKER_KIND_CELERY_POOL, CeleryPoolPublisher, CeleryPoolConsumer)


# ============================================================================
# 测试
# ============================================================================

if __name__ == '__main__':

    random_suffix = uuid.uuid4().hex[:8]

    @boost(BoosterParams(
        queue_name=f'test_cp_broker_{random_suffix}',
        broker_kind=BROKER_KIND_CELERY_POOL,
        concurrent_num=2,
        max_retry_times=2,
        broker_exclusive_config={
            'broker_url': 'redis://localhost:6379/0',
            'result_backend': 'redis://localhost:6379/0',
            'concurrent_num': 4,
            'pool_type': 'threads',
            'worker_loglevel': 'INFO',
            'worker_startup_timeout': 5.0,
        }
    ))
    def add(x, y):
        print(f'  [add] {x} + {y} = {x + y}')
        return x + y

    @boost(BoosterParams(
        queue_name=f'test_cp_broker2_{random_suffix}',
        broker_kind=BROKER_KIND_CELERY_POOL,
        concurrent_num=2,
        broker_exclusive_config={
            'broker_url': 'redis://localhost:6379/0',
            'result_backend': 'redis://localhost:6379/0',
            'concurrent_num': 2,
            'pool_type': 'threads',
            'worker_loglevel': 'INFO',
            'worker_startup_timeout': 5.0,
        }
    ))
    def multiply(a, b):
        print(f'  [multiply] {a} * {b} = {a * b}')
        return a * b

    print('=' * 60)
    print('测试：CeleryPool 复用模式 作为 funboost 自定义 broker')
    print(f'随机后缀: {random_suffix}')
    print('=' * 60)

    print('\n>>> 启动消费者（复用 CeleryPool._start_worker()）...')
    add.consume()
    multiply.consume()

    print('\n>>> 发布任务...')
    time.sleep(2)

    import logging
    log = logging.getLogger('TEST_RESULT')

    celery_results = []
    for i in range(5):
        cr = add.push(i, i * 10)
        celery_results.append(('add', i, i * 10, cr))
    for i in range(3):
        cr = multiply.push(a=i + 1, b=i + 100)
        celery_results.append(('multiply', i + 1, i + 100, cr))

    log.warning(f'已推送 {len(celery_results)} 个任务，等待执行 (5s)...')
    time.sleep(5)

    log.warning('>>> 获取结果（push() 直接返回 celery.result.AsyncResult）')
    for func_name, a, b, cr in celery_results:
        if cr.state == 'SUCCESS':
            log.warning(f'  {func_name}({a}, {b}) = {cr.result}')
        else:
            log.warning(f'  {func_name}({a}, {b}) state={cr.state}')

    log.warning('>>> 测试完成！')
    logging.shutdown()
    import os
    # os._exit(0) # 不要退出
