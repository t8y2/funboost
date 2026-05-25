# Redis ACK 消费确认实现原理深度分析

> Funboost vs Celery 在 Redis 消息队列场景下的 ACK 机制对比

---

## 一、问题背景

### 1.1 为什么需要 ACK？

在消息队列中，"消费确认"（Acknowledge）是保证**消息不丢失**的关键机制：

```
未开启 ACK：
消费者取出消息 → 处理失败 → 消息已丢失 ❌

开启 ACK：
消费者取出消息 → 加入 unack 队列 → 处理成功 → 从 unack 删除 ✅
                ↓
            处理失败/崩溃
                ↓
        消息自动回到队列 → 重新消费 ✅
```

### 1.2 Redis 实现 ACK 的挑战

Redis **不是**消息队列，它是内存数据库。实现 ACK 的核心难点：

> **何时判断消费者已"死亡"，并安全地把它的待确认消息放回队列？**

---

## 二、Funboost 的 5 种 Redis ACK 实现

| 实现 | BrokerEnum | 核心机制 | 推荐度 |
|------|-----------|----------|--------|
| 简单模式 | `REDIS` | 无 ACK | ⭐ |
| 心跳检测 | `REDIS_ACK_ABLE` | ZSet + 心跳 | ⭐⭐⭐⭐⭐ |
| 超时检测 | `REDIS_ACK_USING_TIMEOUT` | 超时自动重回 | ⭐⭐⭐ |
| 双队列模式 | `REDIS_BRPOP_LPUSH` | brpoplpush | ⭐⭐⭐⭐ |
| Stream | `REDIS_STREAM` | Redis 5.0+ | ⭐⭐⭐⭐ |

---

## 三、REDIS_ACK_ABLE 实现原理（推荐）

### 3.1 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                      Redis Server                          │
│                                                             │
│   ┌──────────────┐    ┌──────────────────────────────┐     │
│   │   main_queue │    │  unack_{queue}_consumer_id   │     │
│   │  (list)      │    │       (ZSet)                 │     │
│   │              │    │                              │     │
│   │  msg1        │    │  msg2: 1699999999.123        │     │
│   │  msg2  ──────┼────┼───→ timestamp 作为分数       │     │
│   │  msg3        │    │  msg3: 1700000000.456        │     │
│   └──────────────┘    └──────────────────────────────┘     │
│                                                             │
│   ┌──────────────────────────────────────────────────┐     │
│   │              heartbeat registry (Set)              │     │
│   │                                                    │     │
│   │  consumer_1&&timestamp                             │     │
│   │  consumer_2&&timestamp                             │     │
│   │  consumer_3&&timestamp                             │     │
│   └──────────────────────────────────────────────────┘     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 核心数据结构

```python
# 消费者注册自己的 unack key
_unack_zset_name = f'{queue_name}__unack_id_{consumer_id}'
_unack_registry_key = f'funboost_unack_registry:{queue_name}'

# 心跳记录
heartbeat_key = f'funboost_hearbeat_queue__str:{queue_name}'
# 格式: "consumer_id&&timestamp"
```

### 3.3 消息取出（Lua 脚本保证原子性）

```python
lua_script = '''
    # 批量取出消息
    local task_list = redis.call("lrange", KEYS[1], 0, batch_size-1)
    redis.call("ltrim", KEYS[1], batch_size, -1)
    
    if (#task_list > 0) then
        for _, task_value in ipairs(task_list) do
            # 加入 unack ZSet，timestamp 作为分数
            redis.call('zadd', KEYS[2], ARGV[1], task_value)
        end
        return task_list
    end
    return nil
'''

# 执行
task_list = script(keys=[queue_name, unack_zset], args=[time.time()])
```

**关键点：**
- 使用 Lua 脚本保证 `lpop` + `zadd` 原子性
- 批量取出减少 Redis 往返次数
- timestamp 记录取出时间

### 3.4 消费确认

```python
def _confirm_consume(self, kw):
    """从 unack ZSet 中删除"""
    self.redis_db_frame.zrem(self._unack_zset_name, kw['task_str'])
```

### 3.5 心跳保活机制

```python
# 每秒发送心跳
def send_heartbeat(self):
    heartbeat_key = f'funboost_hearbeat_queue__str:{queue_name}'
    self.redis_db_frame.sadd(heartbeat_key, f'{consumer_id}&&{timestamp}')
    
    # 心跳有效期 60 秒
    self.redis_db_frame.expire(heartbeat_key, 60)
```

### 3.6 死亡消费者检测与消息回收

```python
def _requeue_tasks_which_unconfirmed(self):
    # 1. 获取所有活跃消费者的 ID
    all_heartbeats = self.redis_db_frame.smembers(heartbeat_key)
    alive_consumer_ids = {record.split('&&')[0] for record in all_heartbeats}
    
    # 2. 遍历所有 unack key
    all_unack_keys = self.redis_db_frame.smembers(unack_registry_key)
    
    for unack_key in all_unack_keys:
        consumer_id = extract_consumer_id(unack_key)
        
        # 3. 判断消费者是否死亡
        if consumer_id not in alive_consumer_ids:
            # 4. 批量取出未确认消息
            unacked_tasks = self.redis_db_frame.zrevrange(unack_key, 0, 1000)
            
            # 5. 重新发布到主队列
            for task in unacked_tasks:
                self.publisher.publish(task)
            
            # 6. 清理
            self.redis_db_frame.delete(unack_key)
            self.redis_db_frame.srem(unack_registry_key, unack_key)
```

### 3.7 核心优势

| 特性 | 说明 |
|------|------|
| **精确检测** | 基于心跳判断消费者存活，非超时 |
| **零误判** | 即使消费者处理很慢，也不会被误判死亡 |
| **批量优化** | 批量取出/删除，减少 IO |
| **分布式安全** | 分布式锁保证只有一个进程执行回收 |

---

## 四、REDIS_BRPOP_LPUSH 实现原理

### 4.1 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                      Redis Server                          │
│                                                             │
│   ┌──────────────┐    ┌──────────────────────────────┐     │
│   │   main_queue │◄───┤  unack_{queue}_{consumer_id}  │     │
│   │  (list)      │    │       (list)                  │     │
│   │              │    │                              │     │
│   │  msg1        │    │  msg2 ← msg3 ← msg4         │     │
│   │  msg2 ───────┼───→  brpoplpush 原子操作          │     │
│   │  msg3        │    │                              │     │
│   └──────────────┘    └──────────────────────────────┘     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 核心机制

```python
def _dispatch_task(self):
    while True:
        # brpoplpush: 从 main_queue 取出，原子地推入 unack list
        msg = redis.brpoplpush(
            queue_name,           # 源队列
            unack_list_name,      # 目标队列（unack）
            timeout=60            # 阻塞超时
        )
        if msg:
            self._submit_task(msg)
```

### 4.3 消费确认

```python
def _confirm_consume(self, kw):
    """从 unack list 删除"""
    self.redis_db_frame.lrem(
        self._unack_list_name,
        count=1,
        value=kw['raw_msg']
    )
```

### 4.4 死亡消费者检测

```python
def _requeue_tasks_which_unconfirmed(self):
    # 1. 发送心跳
    self._distributed_consumer_statistics.send_heartbeat()
    alive_ids = get_queue_heartbeat_ids()
    
    # 2. 遍历所有 unack key
    for unack_key in self.redis_db_frame.smembers(registry_key):
        consumer_id = extract_id(unack_key)
        
        # 3. 判断是否死亡
        if consumer_id not in alive_ids:
            # 4. 批量取回消息
            msg_list = self.redis_db_frame.lrange(unack_key, 0, -1)
            
            # 5. 推送回主队列
            self.redis_db_frame.lpush(queue_name, *msg_list)
            
            # 6. 清理
            self.redis_db_frame.delete(unack_key)
            self.redis_db_frame.srem(registry_key, unack_key)
```

### 4.5 与 REDIS_ACK_ABLE 对比

| 维度 | REDIS_ACK_ABLE | REDIS_BRPOP_LPUSH |
|------|----------------|-------------------|
| 数据结构 | ZSet | List |
| 取出方式 | Lua 批量 | brpoplpush 单条 |
| 性能 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| 精确度 | 相同 | 相同 |

---

## 五、REDIS_STREAM 实现原理

### 5.1 Redis Stream 优势

```
Kafka 特性     │ Redis Stream
─────────────┼─────────────
 Consumer Group│ XREADGROUP
 Offset 追踪   │ 自动管理
 消息持久化    │ AOF/RDB
 消息回溯      │ XREAD + ID
```

### 5.2 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                      Redis Server                          │
│                                                             │
│   ┌─────────────────────────────────────────────────────┐   │
│   │                 mystream (Stream)                    │   │
│   │                                                       │   │
│   │  1699999999000-0 → {data: "msg1"}                     │   │
│   │  1699999999001-0 → {data: "msg2"}  ←──────┐         │   │
│   │  1699999999002-0 → {data: "msg3"}           │         │   │
│   │                                       XCLAIM         │   │
│   └─────────────────────────────────────────────────────┘   │
│                                                             │
│   ┌─────────────────────────────────────────────────────┐   │
│   │            mygroup (Consumer Group)                  │   │
│   │                                                       │   │
│   │   consumer_1: pending [1699999001-0]                  │   │
│   │   consumer_2: pending []                              │   │
│   └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 5.3 消费者组创建

```python
def _dispatch_task(self):
    # 创建消费者组（如果不存在）
    try:
        self.redis_db_frame.xgroup_create(
            stream_name,
            group_name,
            id=0,           # 从头开始消费
            mkstream=True   # 不存在则创建
        )
    except ResponseError as e:
        pass  # 组已存在
```

### 5.4 消息消费

```python
def _dispatch_task(self):
    while True:
        # XREADGROUP: 读取消费者组中的新消息
        results = self.redis_db_frame.xreadgroup(
            group_name,              # 消费者组
            consumer_name,           # 消费者 ID
            {stream_name: ">"},       # 只读新消息
            count=batch_size,
            block=60_000             # 阻塞 60 秒
        )
        
        for msg_id, msg_data in results:
            kw = {'body': msg_data[''], 'msg_id': msg_id}
            self._submit_task(kw)
```

### 5.5 消费确认

```python
def _confirm_consume(self, kw):
    """ACK + 删除消息"""
    with self.redis_db_frame.pipeline() as pipe:
        pipe.xack(stream_name, group_name, kw['msg_id'])
        pipe.xdel(stream_name, kw['msg_id'])  # 删除以保持队列干净
        pipe.execute()
```

### 5.6 死亡消费者检测

```python
def _requeue_tasks_which_unconfirmed(self):
    # 1. 获取消费者组中的消费者状态
    consumers = self.redis_db_frame.xinfo_consumers(stream_name, group_name)
    
    alive_ids = get_alive_consumer_ids()
    
    for consumer_info in consumers:
        if consumer_info['name'] not in alive_ids:
            # 2. 获取该消费者的 pending 消息
            pending = self.redis_db_frame.xpending_range(
                stream_name, group_name, '-', '+', 
                1000, consumer_info['name']
            )
            
            # 3. XCLAIM 夺取消息
            claimed = self.redis_db_frame.xclaim(
                stream_name, group_name,
                current_consumer,
                force=True,           # 强制夺取
                message_ids=[p['message_id'] for p in pending]
            )
            
            # 4. 重新提交
            for msg_id, msg_data in claimed:
                self._submit_task({'body': msg_data[''], 'msg_id': msg_id})
```

### 5.7 Redis Stream vs 自实现 ACK

| 维度 | REDIS_STREAM | REDIS_ACK_ABLE |
|------|-------------|----------------|
| 复杂度 | Redis 原生 | 自实现 |
| 性能 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| 功能 | 消息回溯 | 需手动 |
| 消息 ID | 自动生成 | 需手动 |
| 消费者组 | 原生 | 自实现 |

---

## 六、REDIS_ACK_USING_TIMEOUT 实现原理

### 6.1 简单超时机制

```python
# 核心思想：基于时间判断，而非心跳
broker_kind=BrokerEnum.REDIS_ACK_USING_TIMEOUT

# 配置超时时间（秒）
broker_exclusive_config={'ack_timeout': 1800}  # 30 分钟
```

### 6.2 工作流程

```
1. 取出消息 → 加入 unack 队列（带 timestamp）
2. 每 60 秒扫描 unack 队列
3. 检查每条消息的取出时间
4. 如果  elapsed > ack_timeout → 重新发布到主队列
```

### 6.3 实现代码

```python
def _requeue_tasks_which_unconfirmed(self):
    current_time = time.time()
    ack_timeout = self.consumer_params.broker_exclusive_config.get('ack_timeout', 1800)
    
    while True:
        # 按时间排序，取最早的消息
        oldest = self.redis_db_frame.zrange(self._unack_zset_name, 0, 0)
        
        if not oldest:
            break
            
        timestamp = self.redis_db_frame.zscore(self._unack_zset_name, oldest[0])
        
        # 检查是否超时
        if current_time - timestamp > ack_timeout:
            # 重新发布
            self.publisher.publish(oldest[0])
            # 从 unack 删除
            self.redis_db_frame.zrem(self._unack_zset_name, oldest[0])
        else:
            break
```

### 6.4 优缺点

| 优点 | 缺点 |
|------|------|
| 实现简单 | 无法区分"处理慢"和"真崩溃" |
| 不依赖心跳 | 可能误判正在执行的长任务 |
| 资源占用少 | 不适合处理时间很长的任务 |

### 6.5 适用场景

```python
# ✅ 适合：任务执行时间短且可预估
@boost(BoosterParams(
    queue_name='fast_tasks',
    broker_kind=BrokerEnum.REDIS_ACK_USING_TIMEOUT,
    function_timeout=30,  # 任务最多 30 秒
    broker_exclusive_config={'ack_timeout': 60}  # 超过 60 秒未确认则重回
))
def fast_task(x):
    pass

# ❌ 不适合：任务执行时间很长（1 小时）
# 会导致大量消息被误判重回
```

---

## 七、Celery 的 Redis ACK 实现

### 7.1 Celery 配置

```python
# celeryconfig.py
broker_url = 'redis://localhost:6379/0'
result_backend = 'redis://localhost:6379/1'

# 开启 ACK 相关配置
task_acks_late = True              # 任务完成后才 ACK
task_reject_on_worker_lost = True  # worker 丢失时拒绝任务
```

### 7.2 Celery vs Funboost 实现对比

| 维度 | Celery | Funboost |
|------|--------|----------|
| **ACK 触发时机** | 任务执行完成后 | 任务执行完成后 |
| **死亡检测** | Redis 监控事件 | 心跳机制 |
| **消息回收** | Broker 自动 | 自实现逻辑 |
| **实现复杂度** | 依赖 Kombu | 自实现 |
| **灵活性** | 受限于 Kombu | 完全自定义 |

### 7.3 Celery 的问题

```python
# Celery 使用 Redis 作为 broker 时：
# 1. 基于 Redis 的 visibility_timeout
# 2. 超时后消息自动回到队列

# 问题：无法区分"处理慢"和"真崩溃"
# 如果任务需要 1 小时，但 visibility_timeout 是 5 分钟
# 消息会被重复执行！
```

---

## 八、核心对比总结

### 8.1 ACK 机制对比表

| 维度 | Funboost | Celery |
|------|----------|--------|
| **ACK 模式数量** | 5 种 | 1 种 |
| **心跳检测** | ✅ | ❌ |
| **超时检测** | ✅ | ✅ |
| **死亡消费者精准检测** | ✅ | ❌ |
| **批量优化** | ✅ | ❌ |
| **自定义灵活度** | 高 | 低 |

### 8.2 选择指南

```
场景选择：
├── 需要最高可靠性 → REDIS_ACK_ABLE（心跳检测）
├── 需要高性能 + Redis 5.0+ → REDIS_STREAM
├── 需要 brpoplpush → REDIS_BRPOP_LPUSH
├── 任务时间可预估 → REDIS_ACK_USING_TIMEOUT
└── 不需要可靠性 → REDIS（最快）
```

### 8.3 性能排序

```
1. REDIS               (无 ACK，最快)
2. REDIS_ACK_ABLE      (心跳检测)  ★ 推荐
3. REDIS_BRPOP_LPUSH   (brpoplpush)
4. REDIS_STREAM        (XREADGROUP)
5. REDIS_ACK_USING_TIMEOUT (超时检测)
```

---

## 九、最佳实践

### 9.1 高可靠场景

```python
@boost(BoosterParams(
    queue_name='reliable_queue',
    broker_kind=BrokerEnum.REDIS_ACK_ABLE,
    # 批量拉取提升性能
    broker_exclusive_config={
        'pull_msg_batch_size': 100,
    }
))
def reliable_task(x):
    pass
```

### 9.2 高性能场景

```python
@boost(BoosterParams(
    queue_name='fast_queue',
    broker_kind=BrokerEnum.REDIS_STREAM,  # Redis 5.0+
    broker_exclusive_config={
        'group': 'my_group',
        'pull_msg_batch_size': 500,
    }
))
def fast_task(x):
    pass
```

### 9.3 优先级队列

```python
@boost(BoosterParams(
    queue_name='vip_queue',
    broker_kind=BrokerEnum.REDIS_ZSET_PRIORITY,  # 无级优先级
))
def vip_task(importance, data):
    pass

# VIP 用户优先级 1000，普通用户优先级 1
vip_task.publish({'importance': 1000, 'data': 'vip data'}, priority=1000)
```

---

## 十、源码位置

| 文件 | 说明 |
|------|------|
| `consumers/redis_consumer_ack_able.py` | REDIS_ACK_ABLE 实现 |
| `consumers/redis_brpoplpush_consumer.py` | REDIS_BRPOP_LPUSH 实现 |
| `consumers/redis_stream_consumer.py` | REDIS_STREAM 实现 |
| `consumers/confirm_mixin.py` | 确认消费 Mixin（心跳检测） |
| `constant.py` | BrokerEnum 定义 |

---

*文档版本：v1.0*
*最后更新：2026-05-18*
