
"""
Funboost md_for_ai 核心内容 — 为 codebase-memory-mcp 索引而转化为 Python 结构
本文件将 markdown 指南转为 Python 函数和类，使 MCP 的 search_graph 能通过 docstring 搜索到内容。
"""

# =====================================================================
# 一、AI 行为准则与约束 (Rules)
# =====================================================================

def rules_core_syntax():
    """
    ## Rules — AI 行为准则
    
    ### 0. 最高知识准则
    生成代码前必须深度阅读 funboost_all_docs_and_codes.md，禁止臆想类名、方法名、入参。
    
    ### 1. 核心语法：绝对使用 BoosterParams
    禁止 @boost("queue_name", qps=2)，必须 @boost(BoosterParams(queue_name="xxx", ...))。
    禁止臆造参数：timeout → function_timeout；max_retries → max_retry_times。
    
    ### 2. 发布消息 (push vs publish)
    push(*args, **kwargs) 只传业务参数；publish(msg_dict, task_options=TaskOptions(...)) 传框架控制参数。
    异步环境用 await func.aio_push() 或 await func.aio_publish()。
    """
    
def rules_consume_and_context():
    """
    ### 3. 消费启动方式
    func.consume() 基础启动；func.multi_process_consume(n) / func.mp_consume(n) 多进程叠加并发；
    BoostersManager.consume_group("group_name") 分组启动。
    连续启动 func1.consume(); func2.consume()，不要用 threading.Thread 包装。
    ctrl_c_recv() 阻塞主线程让 Ctrl+C 能停止。
    
    ### 4. 上下文获取 (禁止 Celery 思维)
    禁止在参数中加 self/bind=True。必须 from funboost import fct。
    fct.task_id, fct.function_result_status.run_times, fct.full_msg, fct.logger。
    
    ### 5. 定时任务 (ApsJobAdder)
    禁止用 apscheduler.add_job 执行消费函数。必须用 ApsJobAdder(func, job_store_kind='redis').add_push_job(...)。
    """
    
def rules_async_and_faas():
    """
    ### 6. 异步并发 (Asyncio)
    async def 消费函数必须设置 concurrent_mode=ConcurrentModeEnum.ASYNC。
    异步环境获取 RPC 结果必须用 await AioAsyncResult(task_id).result，禁止 AsyncResult.result。
    
    ### 7. FaaS 微服务
    from funboost.faas import fastapi_router; app.include_router(fastapi_router)。
    
    ### 8. 异构系统兼容
    消费非 Funboost 发布的消息：设置 should_check_publish_func_params=False，函数定义为 def task_fun(**kwargs):
    
    ### 9. 实例方法与类方法的 push
    实例方法：ClassName.method.push(obj, x)，第一个参数传实例。
    类方法：ClassName.method.push(ClassName, x)，第一个参数传类本身。
    
    ### 10. 自定义扩展
    禁止修改 funboost 源码。自定义配置用 BoosterParams(user_options={'my_key': 'value'})。
    重写拦截逻辑用 consumer_override_cls 继承 AbstractConsumer。
    """


# =====================================================================
# 二、Skills (AI 技能模板)
# =====================================================================

def skill_hello_world():
    """
    ## Skill 0: Hello World 任务 (零配置/本地单进程)
    使用 MEMORY_QUEUE，无需安装中间件。
    @boost(BrokerParams(queue_name="hello_queue", broker_kind=BrokerEnum.MEMORY_QUEUE, qps=2))
    func.push(word="funboost_0"); func.consume(); ctrl_c_recv()
    """

def skill_standard_task():
    """
    ## Skill 1: 标准后台任务
    @boost(BrokerParams(queue_name="my_standard_task", broker_kind=BrokerEnum.REDIS_ACK_ABLE,
           concurrent_num=50, qps=10, max_retry_times=3))
    func.push(user_id=i, action="login"); func.mp_consume(2); ctrl_c_recv()
    """

def skill_rpc():
    """
    ## Skill 2: RPC 模式
    @boost(BrokerParams(queue_name="rpc_task", is_using_rpc_mode=True))
    async_result = func.push(10, 20); print(async_result.result)
    """

def skill_cron():
    """
    ## Skill 3: 定时调度 (Cron/Interval)
    ApsJobAdder(func, job_store_kind='redis').add_push_job(trigger='cron', hour=2, minute=0, kwargs={...})
    """

def skill_async():
    """
    ## Skill 4: Asyncio 异步任务
    @boost(BrokerParams(concurrent_mode=ConcurrentModeEnum.ASYNC, is_using_rpc_mode=True))
    async def async_fetch(url): ...
    aio_result = await async_fetch.aio_push("http://example.com")
    result = await AioAsyncResult(aio_result.task_id).status_and_result
    """

def skill_workflow():
    """
    ## Skill 5: 工作流编排
    from funboost.workflow import chain, group, chord, WorkflowBoosterParams
    workflow = chain(download.s("video.mp4"), chord(group(...), notify.s(user_id=1001)))
    result = workflow.apply()
    """

def skill_faas():
    """
    ## Skill 6: FaaS 微服务
    from funboost.faas import fastapi_router; app.include_router(fastapi_router)
    POST /funboost/publish — 发布消息
    GET /funboost/get_result?task_id=... — 获取 RPC 结果
    POST /funboost/add_timing_job — 添加定时任务
    GET /funboost/get_msg_count — 获取队列消息数
    POST /funboost/pause_consume /resume_consume — 暂停/恢复消费
    GET /funboost/get_all_queues — 获取所有队列
    """

def skill_spider():
    """
    ## Skill 7: 爬虫
    from boost_spider import RequestClient, SpiderResponse, DatasetSink
    client = RequestClient(request_retry_times=3, is_change_ua_every_request=True)
    resp = client.get(url); title = resp.xpath('//title/text()').extract_first()
    """

def skill_booster_params_inherit():
    """
    ## Skill 8: 继承 BoosterParams
    class MyBoosterParams(BoosterParams):
        broker_kind: str = BrokerEnum.REDIS_ACK_ABLE
        max_retry_times: int = 3
    @boost(MyBoosterParams(queue_name='task_queue_1'))
    """

def skill_consume_any_json():
    """
    ## Skill 9: 消费异构任意 JSON
    @boost(BrokerParams(should_check_publish_func_params=False))
    def process_any_msg(**kwargs): ...
    """

def skill_override_class():
    """
    ## Skill 10: 自定义消费者拦截器
    class MyCustomConsumer(AbstractConsumer):
        def _user_convert_msg_before_run(self, msg) -> dict: ...
        def user_custom_record_process_info_func(self, frs): ...
    @boost(BrokerParams(consumer_override_cls=MyCustomConsumer))
    """

def skill_broker_exclusive_config():
    """
    ## Skill 11: broker_exclusive_config
    RabbitMQ: {'x-max-priority': 5, 'no_ack': False}
    Kafka: {'group_id': 'my_group', 'auto_offset_reset': 'earliest', 'num_partitions': 10}
    Redis: {'pull_msg_batch_size': 100}
    """

def skill_web_manager():
    """
    ## Skill 12: Funboost Web 管理器
    python -m funboost.funweb.app 或 from funboost.funweb.app import start_funboost_web_manager
    """


# =====================================================================
# 三、Skill 100: BoosterParams 全量字段
# =====================================================================

class BoosterParamsFieldGuide:
    """BoosterParams 全量字段定义 (Skill 100)
    
    queue_name: str — 必填，队列名
    broker_kind: str — 默认 BrokerEnum.SQLITE_QUEUE，中间件类型
    project_name: Optional[str] — 项目标签，Web 管理用
    
    concurrent_mode: str — 默认 THREADING，支持 GEVENT/EVENTLET/ASYNC/SINGLE_THREAD
    concurrent_num: int — 默认 50，并发数量
    specify_concurrent_pool: Optional[FunboostBaseConcurrentPool] — 指定线程池/协程池
    
    qps: float/int/None — 每秒执行次数，None 则不限制
    is_using_distributed_frequency_control: bool — 分布式控频（需 Redis）
    
    max_retry_times: int — 默认 3，最大重试次数
    is_using_advanced_retry: bool — 启用指数退避重试
    advanced_retry_config: dict — retry_mode(sleep/requeue), retry_base_interval, retry_multiplier, retry_max_interval, retry_jitter
    is_push_to_dlx_queue_when_retry_max_times: bool — 重试耗尽推送死信队列
    
    function_timeout: int/float/None — 函数超时秒数
    is_support_remote_kill_task: bool — 远程杀死正在运行的函数
    
    msg_expire_seconds: int/float/None — 消息过期时间
    do_task_filtering: bool — 任务入参去重
    task_filtering_expire_seconds: int — 过滤失效期，0 为永久
    
    is_using_rpc_mode: bool — 启用 RPC 模式
    rpc_result_expire_seconds: int — 默认 1800，Redis 保存 RPC 结果过期时间
    rpc_timeout: int — 默认 1800，等待 RPC 结果超时
    
    log_level: int — 默认 DEBUG
    logger_prefix: str — 日志名前缀
    create_logger_file: bool — 是否创建文件日志
    is_show_message_get_from_broker: bool — 是否记录从队列获取的消息内容
    is_print_detail_exception: bool — 出错是否打印详细堆栈
    
    should_check_publish_func_params: bool — 默认 True，是否校验消息字段与函数签名一致
    consuming_function_decorator: Callable — 函数装饰器
    user_custom_record_process_info_func: Callable — 自定义记录结果
    
    broker_exclusive_config: dict — 中间件专有配置
    consumer_override_cls: Type — 自定义消费者类
    publisher_override_cls: Type — 自定义发布者类
    
    booster_group: str — 消费分组名
    allow_run_time_cron: str — 只允许在 cron 时间内运行
    user_options: dict — 用户自定义配置
    """


# =====================================================================
# 四、源码速查
# =====================================================================

def source_code_structure():
    """
    ## funboost 源码结构
    
    core/ — 核心模块: booster.py(Booster装饰器), func_params_model.py(BoosterParams), 
             current_task.py(fct), msg_result_getter.py(AsyncResult/AioAsyncResult),
             function_result_status_saver.py(FunctionResultStatus),
             serialization.py, exceptions.py, funboost_pool.py(FunboostPool)
    
    consumers/ — 49个消费者实现, base_consumer.py(AbstractConsumer)
    publishers/ — 45个发布者实现, base_publisher.py(AbstractPublisher)
    
    factories/ — 工厂: broker_kind__publsiher_consumer_type_map.py(映射表 + register_custom_broker)
    
    concurrent_pool/ — 5种并发池: ThreadPoolExecutorShrinkAble, AsyncPoolExecutor, 
                       GeventPoolExecutor, EventletPoolExecutor, SoloExecutor
    
    timing_job/ — APScheduler 集成: ApsJobAdder
    faas/ — FastAPI/Flask/Django 集成: fastapi_router, flask_blueprint, django_adapter
    workflow/ — 工作流编排: Chain, Group, Chord, Signature, WorkflowBoosterParams
    
    contrib/ — 扩展: override_publisher_consumer_cls/(熔断/微批/Prometheus/OTel/额度/告警),
               register_custom_broker_contrib/(NATS/WebSocket/Watchdog/Redis ZSet),
               funspider/(SimpleSpiderClient/AsyncSpiderClient/SpiderItem),
               cdc/(MySQL binlog同步)
    
    assist/ — 第三方框架辅助: celery_helper, celery_pool, dramatiq_helper, huey_helper, rq_helper
    funweb/ — Web管理界面: start_funboost_web_manager
    queues/ — 队列实现: PythonQueues, FastestMemQueue, SqlaQueue, PeeweeQueue, PostgresQueue
    
    utils/ — 工具: redis_manager(RedisMixin), ctrl_c_end(ctrl_c_recv), 
             decorators(run_many_times/keep_circulating/synchronized),
             func_timeout(函数超时控制), notify_util(Notifier)
    """


def broker_mapping_table():
    """
    ## Broker 完整映射表
    
    MEMORY_QUEUE → LocalPythonQueueConsumer / LocalPythonQueuePublisher
    FASTEST_MEM_QUEUE → FastestMemQueueConsumer / FastestMemQueuePublisher
    
    REDIS → RedisConsumer / RedisPublisher
    REDIS_ACK_ABLE → RedisConsumerAckAble / RedisPublisher (推荐)
    REDIS_STREAM → RedisStreamConsumer / RedisStreamPublisher
    REDIS_PRIORITY → RedisPriorityConsumer / RedisPriorityPublisher
    REDIS_BRPOP_LPUSH → RedisBrpopLpushConsumer / RedisPublisherLpush
    REDIS_PUBSUB → RedisPbSubConsumer / RedisPubSubPublisher
    REDIS_ZSET_PRIORITY/DELAY → RedisZSetConsumer / RedisZSetPublisher(contrib)
    REDIS_HASH_UPDATE → RedisHashUpdateConsumer / RedisHashUpdatePublisher(contrib)
    
    RABBITMQ_AMQPSTORM(=RABBITMQ) → RabbitmqConsumerAmqpStorm / RabbitmqPublisherUsingAmqpStorm
    RABBITMQ_COMPLEX_ROUTING → RabbitmqComplexRoutingConsumer / RabbitmqComplexRoutingPublisher
    RABBITMQ_AMQP → RabbitmqAmqpConsumer / RabbitmqAmqpPublisher
    RABBITMQ_PIKA → RabbitmqConsumer / RabbitmqPublisher
    RABBITMQ_RABBITPY → RabbitmqConsumerRabbitpy / RabbitmqPublisherUsingRabbitpy
    
    KAFKA → KafkaConsumer / KafkaPublisher
    KAFKA_CONFLUENT(=CONFLUENT_KAFKA) → KafkaConsumerManuallyCommit / ConfluentKafkaPublisher
    KAFKA_CONFLUENT_SASlPlAIN → SaslPlainKafkaConsumer / SaslPlainKafkaPublisher
    
    ROCKETMQ → RocketmqConsumer / RocketmqPublisher
    ROCKETMQ5 → Rocketmq5Consumer / Rocketmq5Publisher
    PULSAR → PulsarConsumer / PulsarPublisher
    NSQ → NsqConsumer / NsqPublisher
    MQTT → MqttConsumer / MqttPublisher
    ZEROMQ → ZeroMqConsumer / ZeroMqPublisher
    NATS_CORE → NatsConsumer / NatsPublisher(contrib)
    NATS_JETSTREAM → NatsJetStreamConsumer / NatsJetStreamPublisher(contrib)
    SQS → SqsConsumer / SqsPublisher
    
    SQLITE_QUEUE → PersistQueueConsumer / PersistQueuePublisher
    MONGOMQ → MongoMqConsumer / MongoMqPublisher
    SQLACHEMY → SqlachemyConsumer / SqlachemyQueuePublisher
    POSTGRES → PostgresConsumer / PostgresPublisher
    PEEWEE → PeeweeConsumer / PeeweePublisher
    TXT_FILE → TxtFileConsumer / TxtFilePublisher
    
    TCP → TCPConsumer / TCPPublisher
    UDP → UDPConsumer / UDPPublisher
    HTTP → HTTPConsumer / HTTPPublisher
    GRPC → GrpcConsumer / GrpcPublisher
    WEBSOCKET → WebSocketConsumer / WebSocketPublisher(contrib)
    HTTPSQS → HttpsqsConsumer / HttpsqsPublisher
    
    CELERY → CeleryConsumer / CeleryPublisher
    DRAMATIQ → DramatiqConsumer / DramatiqPublisher
    HUEY → HueyConsumer / HueyPublisher
    RQ → RqConsumer / RqPublisher
    NAMEKO → NamekoConsumer / NamekoPublisher
    KOMBU → KombuConsumer / KombuPublisher
    FASTSTREAM → FastStreamConsumer / FastStreamPublisher
    
    MYSQL_CDC → MysqlCdcConsumer / MysqlCdcPublisher
    WATCHDOG → WatchdogConsumer / WatchdogPublisher(contrib)
    CELERY_POOL → CeleryPoolConsumer / CeleryPoolPublisher(contrib)
    EMPTY → EmptyConsumer / EmptyPublisher
    """


# =====================================================================
# 五、中间件扩展指南
# =====================================================================

def broker_extension_guide():
    """
    ## 扩展 broker 的 3 种方式
    
    ### 1. 静态扩展（直接写死在 funboost 源码中）
    修改: consumers/, publishers/, constant.py(BrokerEnum), 
          broker_kind__exclusive_config_default_define.py,
          broker_kind__publsiher_consumer_type_map.py
    
    ### 2. 动态扩展方式一: register_custom_broker
    适合扩展全新的 broker，不修改 funboost 源码。
    继承 AbstractPublisher/AbstractConsumer 或 EmptyPublisher/EmptyConsumer。
    参考 funboost/contrib/register_custom_broker_contrib/ 目录下代码。
    
    ### 3. 动态扩展方式二: consumer_override_cls / publisher_override_cls
    适合覆盖修改现有 broker 逻辑，Mixin 混入。
    @boost(BoosterParams(consumer_override_cls=YourMixin, publisher_override_cls=YourMixin, broker_kind=BrokerEnum.EMPTY))
    参考 funboost/contrib/override_publisher_consumer_cls/ 目录下代码。
    使用 Mixin 时，Mixin 方法优先级高于原 Consumer (MRO)。
    """

def publisher_required_methods():
    """
    ## Publisher 需要实现的方法
    
    custom_init() — 可选，自定义初始化
    _publish_impl(msg: str) — 必须实现，发布消息的核心逻辑
    clear() — 必须实现，清空队列
    get_message_count() — 必须实现，获取队列消息数量
    close() — 必须实现，关闭连接（可 pass，因为 funboost 永久运行）
    """

def consumer_required_methods():
    """
    ## Consumer 需要实现的方法
    
    custom_init() — 可选，自定义初始化
    _dispatch_task() — 必须实现，从中间件取消息，循环调用 self._submit_task(kw)
    _confirm_consume(kw) — 必须实现，确认消费(ack)
    _requeue(kw) — 必须实现，消息重入队
    
    kw 必须包含: {'body': message_body, ...其他 broker 特有字段}
    """

def override_class_super_rules():
    """
    ## 重写父类方法时 super() 的规则
    
    必须调用 super().xx() 的情况（即使父类是 pass）:
    - custom_init(): 先调 super()，再执行自己的初始化
    - _submit_task(): 先执行自己的逻辑，再调 super()
    - _run/_async_run(): 在自己的逻辑中间调 super()
    
    可以不调 super() 的情况:
    - 父类方法抛出 NotImplementedError (如 _publish_impl, _dispatch_task, _confirm_consume, _requeue)
    - 确实需要完全替换父类逻辑
    
    记录结果的钩子:
    - _both_sync_and_aio_frame_custom_record_process_info_func: 同步和异步都会调用
    - _frame_custom_record_process_info_func: 只用于同步
    - _aio_frame_custom_record_process_info_func: 只用于异步
    """


# =====================================================================
# 六、用户问题 → 源码路由表
# =====================================================================

def user_question_routing():
    """
    ## 用户问题 → 源码路由表
    
    怎么用/怎么装饰函数 → core/booster.py Booster
    怎么发消息/push/publish → publishers/base_publisher.py AbstractPublisher.push/publish
    怎么消费/consume → consumers/base_consumer.py AbstractConsumer.start_consuming_message
    有什么参数/BoosterParams → core/func_params_model.py BoosterParams
    有什么broker/中间件 → constant.py BrokerEnum
    怎么限流/QPS → BoosterParams.qps
    失败重试/指数退避 → BoosterParams.max_retry_times / is_using_advanced_retry
    怎么获取结果/RPC → core/msg_result_getter.py AsyncResult/AioAsyncResult, BoosterParams.is_using_rpc_mode
    怎么获取task_id/fct → core/current_task.py fct
    怎么定时执行/ApsJobAdder → timing_job/timing_push.py ApsJobAdder
    怎么做工作流/chain/group/chord → workflow/primitives.py Chain/Group/Chord
    FastAPI集成/FaaS → faas/fastapi_adapter.py fastapi_router
    怎么自定义broker/扩展 → factories/broker_kind__publsiher_consumer_type_map.py register_custom_broker
    怎么用Celery → consumers/celery_consumer.py + assist/celery_helper.py
    熔断器 → contrib/override_publisher_consumer_cls/circuit_breaker_mixin.py
    微批消费 → contrib/override_publisher_consumer_cls/funboost_micro_batch_mixin.py
    Prometheus → contrib/override_publisher_consumer_cls/funboost_promethus_mixin.py
    OpenTelemetry → contrib/override_publisher_consumer_cls/funboost_otel_mixin.py
    """


# =====================================================================
# 七、内置导出公共 API
# =====================================================================

def public_api_exports():
    """
    ## __init__.py 公共 API 导出
    
    boost, Booster, BoostersManager — core/booster
    BoosterParams, BoosterParamsComplete, TaskOptions — core/func_params_model
    BrokerEnum, ConcurrentModeEnum — constant
    funboost_current_task, fct, get_current_taskid — core/current_task
    AsyncResult, AioAsyncResult — core/msg_result_getter
    AbstractConsumer — consumers/base_consumer
    AbstractPublisher — publishers/base_publisher
    FunctionResultStatus — core/function_result_status_saver
    ExceptionForRetry, ExceptionForRequeue, ExceptionForPushToDlxqueue — core/exceptions
    register_custom_broker — factories/broker_kind__publsiher_consumer_type_map
    ApsJobAdder, funboost_aps_scheduler — timing_job
    fastapi_router — faas/fastapi_adapter
    flask_blueprint — faas/flask_adapter
    ctrl_c_recv — utils/ctrl_c_end
    RedisMixin — utils/redis_manager
    MemoryFunboostPool, FunboostPool, FunboostPoolPickleFunc — core/funboost_pool
    RemoteTaskKiller — core/kill_remote_task
    """
