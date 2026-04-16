# -*- coding: utf-8 -*-


"""
Redis ZSet 实现的两种 Broker:

1. REDIS_ZSET_PRIORITY — 基于 ZSet score 的优先级队列
   score = priority，值越大优先级越高，越先被消费
   相比现有的 REDIS_PRIORITY（基于多个 list + blpop），ZSet 方案直接用 score 排序，
   粒度更细（支持任意浮点数 score），不需要预先声明 x-max-priority。

2. REDIS_ZSET_DELAY — 基于 ZSet score 的延迟队列
   score = 消息的可消费时间戳（Unix timestamp），到期后才可被消费
   相比现有的 APScheduler 方案，ZSet 延迟队列天然持久化在 Redis 中，
   重启后延迟消息不丢失，且支持分布式环境。

两种 broker 均支持确认消费（ACK），复用 ConsumerConfirmMixinWithTheHelpOfRedisByHearbeat。

使用方式:

    from funboost import boost, BoosterParams, TaskOptions
    from funboost.contrib.register_custom_broker_contrib.redis_zset_broker import (
        BROKER_KIND_REDIS_ZSET_PRIORITY, BROKER_KIND_REDIS_ZSET_DELAY,
    )

    # --- 优先级队列 ---
    @boost(BoosterParams(
        queue_name='my_zset_priority_queue',
        broker_kind=BROKER_KIND_REDIS_ZSET_PRIORITY,
        qps=5,
    ))
    def my_priority_task(x):
        print(x)

    # other_extra_params 中使用二级 key 'for_broker_redis_zset_priority' 传递参数，避免与其他用途的字段冲突
    my_priority_task.publish({'x': 1}, task_options=TaskOptions(
        other_extra_params={'for_broker_redis_zset_priority': {'priority': 5}}
    ))
    my_priority_task.publish({'x': 2}, task_options=TaskOptions(
        other_extra_params={'for_broker_redis_zset_priority': {'priority': 10}}
    ))
    # priority=10 的消息会先被消费

    # --- 延迟队列 ---
    @boost(BoosterParams(
        queue_name='my_zset_delay_queue',
        broker_kind=BROKER_KIND_REDIS_ZSET_DELAY,
        qps=5,
    ))
    def my_delay_task(x):
        print(x)

    # other_extra_params 中使用二级 key 'for_broker_redis_zset_delay' 传递参数
    # 方式一：指定延迟秒数（从当前时间算起）
    my_delay_task.publish({'x': 1}, task_options=TaskOptions(
        other_extra_params={'for_broker_redis_zset_delay': {'delay_seconds': 30}}
    ))
    # 方式二：指定绝对时间戳
    my_delay_task.publish({'x': 2}, task_options=TaskOptions(
        other_extra_params={'for_broker_redis_zset_delay': {'eta_timestamp': 1700000000}}
    ))
    # 方式三：不指定延迟参数，立即可消费
    my_delay_task.publish({'x': 3})
"""

"""
Funboost 的扩展性不是“可以扩展”，而是“极其容易、完整、安全地扩展”。 
只用了 200 行代码，就为 Funboost 增加了两种官方级别的 Broker 模式，
并且立即拥有了 QPS 控频、并发控制、重试、死信、RPC、Web 监控等全部企业级能力。
这在 Python 生态中是非常罕见的。所以，说它“无敌”可能有点绝对，但确实是天花板级别的存在。👑
"""

from funboost.core.serialization import Serialization
import time


from funboost import register_custom_broker, AbstractConsumer, AbstractPublisher, register_broker_exclusive_config_default
from funboost.consumers.confirm_mixin import ConsumerConfirmMixinWithTheHelpOfRedisByHearbeat
from funboost.publishers.redis_queue_flush_mixin import FlushRedisQueueMixin
from funboost.utils.redis_manager import RedisMixin

BROKER_KIND_REDIS_ZSET_PRIORITY = 'REDIS_ZSET_PRIORITY'
BROKER_KIND_REDIS_ZSET_DELAY = 'REDIS_ZSET_DELAY'

_FOR_BROKER_KEY_PRIORITY = 'for_broker_redis_zset_priority'
_FOR_BROKER_KEY_DELAY = 'for_broker_redis_zset_delay'


# ============================================================================
# Publisher 基类
# ============================================================================

class RedisZSetPublisherBase(FlushRedisQueueMixin, AbstractPublisher, RedisMixin):
    """Redis ZSet Publisher 基类，子类需实现 _get_score(msg) 方法"""

    def _get_broker_specific_params(self, for_broker_key: str, msg) -> dict:
        """从 other_extra_params 的二级 key 中提取 broker 专用参数"""
        params = self._get_from_other_extra_params(for_broker_key, msg)
        return params if isinstance(params, dict) else {}

    def _get_score(self, msg: str) -> float:
        raise NotImplementedError

    def _publish_impl(self, msg: str):
        score = self._get_score(msg)
        self.redis_db_frame.zadd(self._queue_name, {msg: score})

    def get_message_count(self):
        return self.redis_db_frame.zcard(self._queue_name)

    def close(self):
        pass


# ============================================================================
# Consumer 基类
# ============================================================================

class RedisZSetConsumerBase(ConsumerConfirmMixinWithTheHelpOfRedisByHearbeat, AbstractConsumer):
    """Redis ZSet Consumer 基类，子类需实现 _build_pop_lua() 方法"""

    def custom_init(self):
        super().custom_init()
        self.pull_msg_batch_size = self.consumer_params.broker_exclusive_config['pull_msg_batch_size']
        self.pull_initial_interval = self.consumer_params.broker_exclusive_config.get('pull_base_interval', 0.01)
        self.pull_max_interval = self.consumer_params.broker_exclusive_config.get('pull_max_interval', 2)

    def _build_pop_lua(self) -> str:
        """
        返回 Lua 脚本字符串。
        KEYS[1] = 主队列 zset
        KEYS[2] = unack zset
        ARGV[1] = 当前时间戳 (float)
        ARGV[2] = batch_size (int)
        脚本需返回取出的 member 列表，并将它们从 KEYS[1] 移入 KEYS[2]。
        """
        raise NotImplementedError

    def _dispatch_task(self):
        lua = self._build_pop_lua()
        script = self.redis_db_frame.register_script(lua)
        sleep_time = self.pull_initial_interval
        while True:
            task_str_list = script(
                keys=[self._queue_name, self._unack_zset_name],
                args=[time.time(), self.pull_msg_batch_size],
            )
            if task_str_list:
                sleep_time = self.pull_initial_interval
                self._print_message_get_from_broker(task_str_list)
                for task_str in task_str_list:   # pyright: ignore[reportGeneralTypeIssues]
                    kw = {'body': task_str, 'task_str': task_str}
                    self._submit_task(kw)
            else:
                time.sleep(sleep_time)
                sleep_time = min(sleep_time * 2, self.pull_max_interval)


# ============================================================================
# REDIS_ZSET_PRIORITY — ZSet 优先级队列
# ============================================================================

class RedisZSetPriorityPublisher(RedisZSetPublisherBase):
    """
    score = priority，值越大越先消费。
    通过 task_options=TaskOptions(other_extra_params={
        'for_broker_redis_zset_priority': {'priority': N}
    }) 指定优先级。不指定时默认 priority = 0。
    """

    def _get_score(self, msg: str) -> float:
        params = self._get_broker_specific_params(_FOR_BROKER_KEY_PRIORITY, msg)
        priority = params.get('priority')
        return float(priority) if priority is not None else 0.0


class RedisZSetPriorityConsumer(RedisZSetConsumerBase):
    """ZREVRANGE：score 从大到小，取出最高优先级的消息"""

    def _build_pop_lua(self) -> str:
        return '''
            local members = redis.call("zrevrange", KEYS[1], 0, tonumber(ARGV[2]) - 1)
            if #members > 0 then
                for i, member in ipairs(members) do
                    redis.call("zrem", KEYS[1], member)
                    redis.call("zadd", KEYS[2], ARGV[1], member)
                end
            end
            return members
        '''

    def _requeue(self, kw):
        body = kw['body']
        priority = body.get('extra', {}).get('other_extra_params', {}).get(_FOR_BROKER_KEY_PRIORITY, {}).get('priority', 0) or 0
        self.redis_db_frame.zadd(self._queue_name, {Serialization.to_json_str(body): float(priority)})


# ============================================================================
# REDIS_ZSET_DELAY — ZSet 延迟队列
# ============================================================================

class RedisZSetDelayPublisher(RedisZSetPublisherBase):
    """
    score = 消息可消费的时间戳。
    通过 task_options=TaskOptions(other_extra_params={
        'for_broker_redis_zset_delay': {'delay_seconds': N}
    }) 指定延迟秒数，
    或 task_options=TaskOptions(other_extra_params={
        'for_broker_redis_zset_delay': {'eta_timestamp': T}
    }) 指定绝对时间戳。
    不指定时 score = time.time()，立即可消费。
    """

    def _get_score(self, msg: str) -> float:
        params = self._get_broker_specific_params(_FOR_BROKER_KEY_DELAY, msg)
        eta_timestamp = params.get('eta_timestamp')
        if eta_timestamp is not None:
            return float(eta_timestamp)
        delay_seconds = params.get('delay_seconds')
        if delay_seconds is not None:
            return time.time() + float(delay_seconds)
        return time.time()


class RedisZSetDelayConsumer(RedisZSetConsumerBase):
    """ZRANGEBYSCORE -inf ~ now：取出所有已到期的消息"""

    def custom_init(self):
        super().custom_init()
        self.pull_initial_interval = self.consumer_params.broker_exclusive_config.get('pull_base_interval', 0.1)

    def _build_pop_lua(self) -> str:
        return '''
            local members = redis.call("zrangebyscore", KEYS[1], "-inf", ARGV[1], "LIMIT", 0, tonumber(ARGV[2]))
            if #members > 0 then
                for i, member in ipairs(members) do
                    redis.call("zrem", KEYS[1], member)
                    redis.call("zadd", KEYS[2], ARGV[1], member)
                end
            end
            return members
        '''

    def _requeue(self, kw):
        self.redis_db_frame.zadd(self._queue_name, {Serialization.to_json_str(kw['body']): time.time()})


# ============================================================================
# 注册 Broker
# ============================================================================



register_broker_exclusive_config_default(
    BROKER_KIND_REDIS_ZSET_PRIORITY,
    {
        'pull_msg_batch_size': 16,
        'pull_base_interval': 0.02, # 指数退避，初始拉取间隔 0.02s
        'pull_max_interval': 2,
    }
)

register_broker_exclusive_config_default(
    BROKER_KIND_REDIS_ZSET_DELAY,
    {
        'pull_msg_batch_size': 16,
        'pull_base_interval': 0.01, # 指数退避，初始拉取间隔 0.01s
        'pull_max_interval': 2,
    }
)

register_custom_broker(BROKER_KIND_REDIS_ZSET_PRIORITY, RedisZSetPriorityPublisher, RedisZSetPriorityConsumer)
register_custom_broker(BROKER_KIND_REDIS_ZSET_DELAY, RedisZSetDelayPublisher, RedisZSetDelayConsumer)
