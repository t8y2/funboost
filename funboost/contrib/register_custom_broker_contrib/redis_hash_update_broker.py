# -*- coding: utf-8 -*-
"""
可覆盖消息的 Redis HASH Broker —— "dict 强化版"
=================================================

核心语义：
    同一个 override_key 的消息，后发的自动覆盖先发的。
    消费端只消费最新值，天然去重 + 保鲜。

典型场景：
    - IoT 设备上报传感器数据（只关心最新温度/湿度）
    - 状态频繁更新（只关心最新坐标/进度）
    - 配置下发（覆盖旧配置）

存储结构：
    Redis HASH  key = "{queue_name}:hash_update"
                field = override_key（覆盖标识）
                value = funboost msg_json

消费方式：
    Lua 脚本原子 pop：hkeys → 取第一个 → hget → hdel → 返回

注册 broker_kind：REDIS_HASH_UPDATE

override_key 的三级生成策略（优先级从高到低）：

    1. 用户显式指定（最高优先级）：
       通过 publish 方法传递：
       task_options=TaskOptions(other_extra_params={
           'for_broker_redis_hash_update': {'override_key': '自定义字符串'}
       })
       适用于入参复杂（嵌套 dict / list）不好自动提取唯一标识的场景。
       二级 key 命名空间隔离，不会与其他 broker 的 other_extra_params 冲突。

    2. 从函数入参中自动提取：
       broker_exclusive_config 中设置 override_key_fields = ['device_id']
       框架自动从函数入参中提取指定字段，组合生成 override_key。

    3. 全部入参（最低优先级）：
       override_key_fields 为空时，用全部函数入参（排除 extra / extra_params）做 override_key。

broker_exclusive_config 支持项：
    override_key_fields : list[str]  构成 override_key 的函数入参字段名列表，为空则用全部入参
    pull_base_interval  : float     消费空轮询最小休眠秒数（默认 0.01）
    pull_max_interval   : float     消费空轮询最大休眠秒数（默认 2）
    pull_batch_size     : int       每次批量拉取条数（默认 100）

用法示例::

    from funboost import boost, BoosterParams
    from funboost.core.func_params_model import TaskOptions
    from funboost.contrib.register_custom_broker_contrib.redis_hash_update_broker import (
        BROKER_KIND_REDIS_HASH_UPDATE,
    )

    @boost(BoosterParams(
        queue_name='iot_sensor_queue',
        broker_kind=BROKER_KIND_REDIS_HASH_UPDATE,
        concurrent_num=4,
        broker_exclusive_config={
            'override_key_fields': ['device_id'],
        },
    ))
    def report_temperature(device_id, temperature, timestamp):
        print(device_id, temperature, timestamp)

    # 方式1：自动从 device_id 入参生成 override_key
    report_temperature.push(device_id='sensor_001', temperature=24.0, timestamp='...')

    # 方式2：显式指定 override_key（适合入参复杂的场景）
    report_temperature.publish(
        {'device_id': 'sensor_001', 'temperature': 24.0, 'timestamp': '...'},
        task_options=TaskOptions(other_extra_params={
            'for_broker_redis_hash_update': {'override_key': 'my_custom_key'}
        }),
    )
"""

import json
import time
import hashlib

from funboost import (
    register_custom_broker,
    AbstractConsumer,
    AbstractPublisher,
    register_broker_exclusive_config_default,
)
from funboost.utils.redis_manager import RedisMixin


BROKER_KIND_REDIS_HASH_UPDATE = 'REDIS_HASH_UPDATE'
_FOR_BROKER_KEY = 'for_broker_redis_hash_update'

# ============================================================
# 工具函数：从 funboost msg_json 中提取 override_key
# ============================================================

def _extract_override_key(msg_json, override_key_fields=None):
    """
    从 funboost 消息 JSON 中提取用作 HASH field 的 override_key。

    override_key_fields 为 None 或空 → 用全部函数入参（排除 extra / extra_params）做 key。
    override_key_fields 非空 → 只取指定字段的值组合做 key。
    """
    if isinstance(msg_json, (bytes, str)):
        msg_dict = json.loads(msg_json)
    else:
        msg_dict = msg_json

    kw = {k: v for k, v in msg_dict.items() if k not in ('extra', 'extra_params')}

    if override_key_fields:
        key_parts = {f: kw.get(f) for f in override_key_fields}
    else:
        key_parts = kw

    raw = json.dumps(key_parts, sort_keys=True, ensure_ascii=False)
    return hashlib.md5(raw.encode('utf-8')).hexdigest()


# ============================================================
# Publisher
# ============================================================

class RedisHashUpdatePublisher(AbstractPublisher, RedisMixin):
    """
    发布消息到 Redis HASH，相同 override_key 自动覆盖旧消息。
    """

    def custom_init(self):
        self._hash_key = '{}:hash_update'.format(self._queue_name)
        config = self.publisher_params.broker_exclusive_config
        self._override_key_fields = config.get('override_key_fields') or []

    def _get_broker_specific_params(self, msg):
        # type: (str) -> dict
        params = self._get_from_other_extra_params(_FOR_BROKER_KEY, msg)
        return params if isinstance(params, dict) else {}

    def _resolve_override_key(self, msg):
        # type: (str) -> str
        broker_params = self._get_broker_specific_params(msg)
        override_key = broker_params.get('override_key')
        if override_key:
            return str(override_key)
        return _extract_override_key(msg, self._override_key_fields or None)

    def _publish_impl(self, msg):
        # type: (str) -> None
        mk = self._resolve_override_key(msg)
        self.redis_db_frame.hset(self._hash_key, mk, msg)

    def clear(self):
        self.redis_db_frame.delete(self._hash_key)
        self.logger.warning('清除 {} 中的消息成功'.format(self._hash_key))

    def get_message_count(self):
        return self.redis_db_frame.hlen(self._hash_key)

    def close(self):
        pass


# ============================================================
# Consumer
# ============================================================

_LUA_HPOP_BATCH = """
local keys = redis.call('hkeys', KEYS[1])
if #keys == 0 then
    return nil
end
local batch = tonumber(ARGV[1])
if batch > #keys then
    batch = #keys
end
local results = {}
for i = 1, batch do
    local field = keys[i]
    local value = redis.call('hget', KEYS[1], field)
    redis.call('hdel', KEYS[1], field)
    results[#results + 1] = value
end
return results
"""


class RedisHashUpdateConsumer(AbstractConsumer, RedisMixin):
    """
    从 Redis HASH 消费消息（原子 pop，每次取一批）。
    """

    def custom_init(self):
        super().custom_init()
        self._hash_key = '{}:hash_update'.format(self._queue_name)
        config = self.consumer_params.broker_exclusive_config
        self._pull_base_interval = config.get('pull_base_interval', 0.01)
        self._pull_max_interval = config.get('pull_max_interval', 2)
        self._pull_batch_size = config.get('pull_batch_size', 100)
        self._override_key_fields = config.get('override_key_fields') or []
        self._lua_batch_script = None

    def _ensure_lua_script(self):
        if self._lua_batch_script is None:
            self._lua_batch_script = self.redis_db_frame.register_script(_LUA_HPOP_BATCH)

    def _dispatch_task(self):
        self._ensure_lua_script()
        sleep_time = self._pull_base_interval
        while True:
            result_list = self._lua_batch_script(
                keys=[self._hash_key],
                args=[self._pull_batch_size],
            )
            if result_list:
                sleep_time = self._pull_base_interval
                self._print_message_get_from_broker(result_list)
                for msg_str in result_list:
                    kw = {'body': msg_str}
                    self._submit_task(kw)
            else:
                time.sleep(sleep_time)
                sleep_time = min(sleep_time * 2, self._pull_max_interval)

    def _confirm_consume(self, kw):
        pass

    def _requeue(self, kw):
        msg_str = kw['body']
        if isinstance(msg_str, bytes):
            msg_str = msg_str.decode('utf-8')
        msg_dict = json.loads(msg_str) if isinstance(msg_str, str) else msg_str
        broker_params = msg_dict.get('extra', {}).get('other_extra_params', {}).get(_FOR_BROKER_KEY, {})
        override_key = broker_params.get('override_key') if isinstance(broker_params, dict) else None
        if override_key:
            mk = str(override_key)
        else:
            mk = _extract_override_key(msg_str, self._override_key_fields or None)
        self.redis_db_frame.hset(self._hash_key, mk, msg_str)


# ============================================================
# 注册 broker
# ============================================================

register_broker_exclusive_config_default(
    BROKER_KIND_REDIS_HASH_UPDATE,
    {
        'override_key_fields': [],
        'pull_base_interval': 0.01,
        'pull_max_interval': 2,
        'pull_batch_size': 100,
    }
)

register_custom_broker(BROKER_KIND_REDIS_HASH_UPDATE, RedisHashUpdatePublisher, RedisHashUpdateConsumer)
