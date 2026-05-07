"""
为了更好的 pydantic 在各种ide下代码自动补全提示，且不依赖pydantic在各种ide的插件，所以写了个.pyi文件。
这个文件主要是为了增强用户体验，方便代码补全提示。

注意：新增或删除字段时需同步更新此文件
"""

import typing
import asyncio
import datetime
import logging

from funboost.core.pydantic_compatible_base import BaseJsonAbleModel
from funboost.concurrent_pool import FunboostBaseConcurrentPool


class FunctionResultStatusPersistanceConfig(BaseJsonAbleModel):
    is_save_status: bool
    is_save_result: bool
    expire_seconds: int
    is_use_bulk_insert: bool
    table_name: typing.Optional[str]

    def __init__(
        self,
        *,
        is_save_status: bool = False,
        is_save_result: bool = False,
        expire_seconds: int = 604800,
        is_use_bulk_insert: bool = False,
        table_name: typing.Optional[str] = None,
    ) -> None: ...


class BoosterParamsFieldsAssit:
    has_been_deleted_fields: typing.List[str]
    rename_fields: typing.Dict[str, str]


class BoosterParams(BaseJsonAbleModel):
    """
    掌握funboost 的精华就是知道 BoosterParams 的入参有哪些，如果知道有哪些入参字段，就掌握了funboost的 90% 用法。
    """

    queue_name: str
    broker_kind: str
    project_name: typing.Optional[str]
    concurrent_mode: str
    concurrent_num: int
    specify_concurrent_pool: typing.Optional[FunboostBaseConcurrentPool]
    specify_async_loop: typing.Optional[asyncio.AbstractEventLoop]
    is_auto_start_specify_async_loop_in_child_thread: bool
    qps: typing.Union[float, int, None]
    is_using_distributed_frequency_control: bool
    is_send_consumer_heartbeat_to_redis: bool
    max_retry_times: int
    is_using_advanced_retry: bool
    advanced_retry_config: dict
    is_push_to_dlx_queue_when_retry_max_times: bool
    consuming_function_decorator: typing.Optional[typing.Callable[..., typing.Any]]
    function_timeout: typing.Union[int, float, None]
    is_support_remote_kill_task: bool
    log_level: int
    logger_prefix: str
    create_logger_file: bool
    logger_name: typing.Union[str, None]
    log_filename: typing.Union[str, None]
    is_show_message_get_from_broker: bool
    is_print_detail_exception: bool
    publish_msg_log_use_full_msg: bool
    msg_expire_seconds: typing.Union[float, int, None]
    do_task_filtering: bool
    task_filtering_expire_seconds: int
    function_result_status_persistance_conf: FunctionResultStatusPersistanceConfig
    user_custom_record_process_info_func: typing.Optional[typing.Callable[..., typing.Any]]
    is_using_rpc_mode: bool
    rpc_result_expire_seconds: int
    rpc_timeout: int
    delay_task_apscheduler_jobstores_kind: str
    allow_run_time_cron: typing.Optional[str]
    schedule_tasks_on_main_thread: bool
    is_auto_start_consuming_message: bool
    booster_group: typing.Union[str, None]
    consuming_function: typing.Optional[typing.Callable[..., typing.Any]]
    consuming_function_raw: typing.Optional[typing.Callable[..., typing.Any]]
    consuming_function_name: str
    broker_exclusive_config: dict
    should_check_publish_func_params: bool
    manual_func_input_params: dict
    consumer_override_cls: typing.Optional[typing.Type]
    publisher_override_cls: typing.Optional[typing.Type]
    consuming_function_kind: typing.Optional[str]
    user_options: dict
    auto_generate_info: dict
    is_fake_booster: bool
    booster_registry_name: str

    def __init__(
        self,
        *,
        queue_name: str,
        broker_kind: str = ...,
        project_name: typing.Optional[str] = None,
        concurrent_mode: str = ...,
        concurrent_num: int = 50,
        specify_concurrent_pool: typing.Optional[FunboostBaseConcurrentPool] = None,
        specify_async_loop: typing.Optional[asyncio.AbstractEventLoop] = None,
        is_auto_start_specify_async_loop_in_child_thread: bool = True,
        qps: typing.Union[float, int, None] = None,
        is_using_distributed_frequency_control: bool = False,
        is_send_consumer_heartbeat_to_redis: bool = False,
        max_retry_times: int = 3,
        is_using_advanced_retry: bool = False,
        advanced_retry_config: dict = ...,
        is_push_to_dlx_queue_when_retry_max_times: bool = False,
        consuming_function_decorator: typing.Optional[typing.Callable[..., typing.Any]] = None,
        function_timeout: typing.Union[int, float, None] = None,
        is_support_remote_kill_task: bool = False,
        log_level: int = ...,
        logger_prefix: str = '',
        create_logger_file: bool = True,
        logger_name: typing.Union[str, None] = '',
        log_filename: typing.Union[str, None] = None,
        is_show_message_get_from_broker: bool = False,
        is_print_detail_exception: bool = True,
        publish_msg_log_use_full_msg: bool = False,
        msg_expire_seconds: typing.Union[float, int, None] = None,
        do_task_filtering: bool = False,
        task_filtering_expire_seconds: int = 0,
        function_result_status_persistance_conf: FunctionResultStatusPersistanceConfig = ...,
        user_custom_record_process_info_func: typing.Optional[typing.Callable[..., typing.Any]] = None,
        is_using_rpc_mode: bool = False,
        rpc_result_expire_seconds: int = 1800,
        rpc_timeout: int = 1800,
        delay_task_apscheduler_jobstores_kind: str = 'redis',
        allow_run_time_cron: typing.Optional[str] = None,
        schedule_tasks_on_main_thread: bool = False,
        is_auto_start_consuming_message: bool = False,
        booster_group: typing.Union[str, None] = None,
        consuming_function: typing.Optional[typing.Callable[..., typing.Any]] = None,
        consuming_function_raw: typing.Optional[typing.Callable[..., typing.Any]] = None,
        consuming_function_name: str = '',
        broker_exclusive_config: dict = ...,
        should_check_publish_func_params: bool = True,
        manual_func_input_params: dict = ...,
        consumer_override_cls: typing.Optional[typing.Type] = None,
        publisher_override_cls: typing.Optional[typing.Type] = None,
        consuming_function_kind: typing.Optional[str] = None,
        user_options: dict = ...,
        auto_generate_info: dict = ...,
        is_fake_booster: bool = False,
        booster_registry_name: str = ...,
    ) -> None: ...

    def __call__(self, func: typing.Callable) -> typing.Any: ...


class BoosterParamsComplete(BoosterParams):
    """
    BoosterParams的子类, 预设了一些常用配置:
    function_result_status_persistance_conf 永远支持函数消费状态 结果状态持久化
    is_send_consumer_heartbeat_to_redis 永远支持发送消费者的心跳到redis
    is_using_rpc_mode 永远支持rpc模式
    broker_kind 永远是使用 amqpstorm包 操作 rabbitmq作为消息队列
    specify_concurrent_pool 同一个进程的不同booster函数,共用一个线程池
    """

    def __init__(
        self,
        *,
        queue_name: str,
        broker_kind: str = ...,
        project_name: typing.Optional[str] = None,
        concurrent_mode: str = ...,
        concurrent_num: int = 50,
        specify_concurrent_pool: typing.Optional[FunboostBaseConcurrentPool] = ...,
        specify_async_loop: typing.Optional[asyncio.AbstractEventLoop] = None,
        is_auto_start_specify_async_loop_in_child_thread: bool = True,
        qps: typing.Union[float, int, None] = None,
        is_using_distributed_frequency_control: bool = False,
        is_send_consumer_heartbeat_to_redis: bool = True,
        max_retry_times: int = 3,
        is_using_advanced_retry: bool = False,
        advanced_retry_config: dict = ...,
        is_push_to_dlx_queue_when_retry_max_times: bool = False,
        consuming_function_decorator: typing.Optional[typing.Callable[..., typing.Any]] = None,
        function_timeout: typing.Union[int, float, None] = None,
        is_support_remote_kill_task: bool = False,
        log_level: int = ...,
        logger_prefix: str = '',
        create_logger_file: bool = True,
        logger_name: typing.Union[str, None] = '',
        log_filename: typing.Union[str, None] = None,
        is_show_message_get_from_broker: bool = False,
        is_print_detail_exception: bool = True,
        publish_msg_log_use_full_msg: bool = False,
        msg_expire_seconds: typing.Union[float, int, None] = None,
        do_task_filtering: bool = False,
        task_filtering_expire_seconds: int = 0,
        function_result_status_persistance_conf: FunctionResultStatusPersistanceConfig = ...,
        user_custom_record_process_info_func: typing.Optional[typing.Callable[..., typing.Any]] = None,
        is_using_rpc_mode: bool = True,
        rpc_result_expire_seconds: int = 3600,
        rpc_timeout: int = 1800,
        delay_task_apscheduler_jobstores_kind: str = 'redis',
        allow_run_time_cron: typing.Optional[str] = None,
        schedule_tasks_on_main_thread: bool = False,
        is_auto_start_consuming_message: bool = False,
        booster_group: typing.Union[str, None] = None,
        consuming_function: typing.Optional[typing.Callable[..., typing.Any]] = None,
        consuming_function_raw: typing.Optional[typing.Callable[..., typing.Any]] = None,
        consuming_function_name: str = '',
        broker_exclusive_config: dict = ...,
        should_check_publish_func_params: bool = True,
        manual_func_input_params: dict = ...,
        consumer_override_cls: typing.Optional[typing.Type] = None,
        publisher_override_cls: typing.Optional[typing.Type] = None,
        consuming_function_kind: typing.Optional[str] = None,
        user_options: dict = ...,
        auto_generate_info: dict = ...,
        is_fake_booster: bool = False,
        booster_registry_name: str = ...,
    ) -> None: ...


class TaskOptions(BaseJsonAbleModel):
    """
    publish 支持的额外参数，和函数参数一起发布到中间件。
    """

    task_id: typing.Optional[str]
    publish_time: typing.Optional[float]
    publish_time_format: typing.Optional[str]
    function_timeout: typing.Union[float, int, None]
    max_retry_times: typing.Union[int, None]
    is_print_detail_exception: typing.Union[bool, None]
    msg_expire_seconds: typing.Union[float, int, None]
    is_using_rpc_mode: typing.Union[bool, None]
    countdown: typing.Union[float, int, None]
    eta: typing.Union[datetime.datetime, str, None]
    misfire_grace_time: typing.Union[int, None]
    user_extra_info: typing.Optional[dict]
    other_extra_params: typing.Optional[dict]
    do_task_filtering: typing.Optional[bool]
    filter_str: typing.Optional[str]
    can_not_json_serializable_keys: typing.Optional[typing.List[str]]
    otel_context: typing.Optional[dict]

    def __init__(
        self,
        *,
        task_id: typing.Optional[str] = None,
        publish_time: typing.Optional[float] = None,
        publish_time_format: typing.Optional[str] = None,
        function_timeout: typing.Union[float, int, None] = None,
        max_retry_times: typing.Union[int, None] = None,
        is_print_detail_exception: typing.Union[bool, None] = None,
        msg_expire_seconds: typing.Union[float, int, None] = None,
        is_using_rpc_mode: typing.Union[bool, None] = None,
        countdown: typing.Union[float, int, None] = None,
        eta: typing.Union[datetime.datetime, str, None] = None,
        misfire_grace_time: typing.Union[int, None] = None,
        user_extra_info: typing.Optional[dict] = None,
        other_extra_params: typing.Optional[dict] = None,
        do_task_filtering: typing.Optional[bool] = None,
        filter_str: typing.Optional[str] = None,
        can_not_json_serializable_keys: typing.Optional[typing.List[str]] = None,
        otel_context: typing.Optional[dict] = None,
    ) -> None: ...


class PublisherParams(BaseJsonAbleModel):
    queue_name: str
    broker_kind: typing.Optional[str]
    project_name: typing.Optional[str]
    log_level: int
    logger_prefix: str
    create_logger_file: bool
    logger_name: str
    log_filename: typing.Optional[str]
    clear_queue_within_init: bool
    consuming_function: typing.Optional[typing.Callable[..., typing.Any]]
    broker_exclusive_config: dict
    should_check_publish_func_params: bool
    manual_func_input_params: dict
    publisher_override_cls: typing.Optional[typing.Type]
    publish_msg_log_use_full_msg: bool
    consuming_function_kind: typing.Optional[str]
    rpc_timeout: int
    user_options: dict
    auto_generate_info: dict
    is_fake_booster: bool
    booster_registry_name: str

    def __init__(
        self,
        *,
        queue_name: str,
        broker_kind: typing.Optional[str] = None,
        project_name: typing.Optional[str] = None,
        log_level: int = ...,
        logger_prefix: str = '',
        create_logger_file: bool = True,
        logger_name: str = '',
        log_filename: typing.Optional[str] = None,
        clear_queue_within_init: bool = False,
        consuming_function: typing.Optional[typing.Callable[..., typing.Any]] = None,
        broker_exclusive_config: dict = ...,
        should_check_publish_func_params: bool = True,
        manual_func_input_params: dict = ...,
        publisher_override_cls: typing.Optional[typing.Type] = None,
        publish_msg_log_use_full_msg: bool = False,
        consuming_function_kind: typing.Optional[str] = None,
        rpc_timeout: int = 1800,
        user_options: dict = ...,
        auto_generate_info: dict = ...,
        is_fake_booster: bool = False,
        booster_registry_name: str = ...,
    ) -> None: ...
