---
name: funboost-faas-deploy
description: 当需要将 funboost 任务部署为 HTTP 微服务时使用。触发场景：通过 FastAPI/Flask/Django 暴露发布和查询接口、使用内置 FaaS router、无需手写 API 代码。关键词：FaaS, 微服务, FastAPI, Flask, Django, HTTP API, REST, fastapi_router, flask_blueprint, web deploy。
compatibility: Python 3.7+, funboost with FastAPI/Flask/Django installed
---

# Funboost FaaS 微服务部署

## 概述

Funboost 提供内置的 HTTP Router（FastAPI、Flask、Django），一行代码即可为所有 boost 装饰的函数暴露发布和结果查询接口。

**核心原则：** 不要手动编写发布/结果 API — 直接使用内置 router。

## 适用场景

- 将任务函数暴露为 HTTP 接口
- 构建基于分布式队列的微服务 API
- 将 funboost 集成到现有 Web 应用
- 为前端/其他服务创建任务提交 API

## 速查表

| Web 框架 | 集成代码 |
|----------|----------|
| FastAPI | `app.include_router(fastapi_router)` |
| Flask | `app.register_blueprint(flask_blueprint)` |
| Django (Ninja) | `api.add_router("/funboost", django_router)` |

## FastAPI 集成

> **前置条件：** FaaS 接口依赖 Redis 发现已注册队列的元数据。需确保消费者已启动且通过心跳注册到 Redis，并在 `funboost_config.py` 中配置 Redis 连接。

```python
from fastapi import FastAPI
from funboost.faas import fastapi_router
from funboost import boost, BoosterParams, BrokerEnum

app = FastAPI()
app.include_router(fastapi_router)

@boost(BoosterParams(
    queue_name="email_queue",
    broker_kind=BrokerEnum.REDIS_ACK_ABLE,
    is_using_rpc_mode=True,
))
def send_email(to: str, subject: str, body: str):
    print(f"发送邮件到 {to}")
    return {"status": "sent", "to": to}

# 消费者在单独的进程/脚本中启动：
# send_email.consume()
```

自动提供以下接口：
- `POST /funboost/publish` — 提交任务
- `GET /funboost/get_result?task_id=xxx&timeout=5` — 查询任务结果

**请求体格式（POST /funboost/publish）：**

```json
{
    "queue_name": "email_queue",
    "msg_body": {"to": "user@example.com", "subject": "Hello", "body": "Hi"},
    "need_result": true,
    "timeout": 60
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `queue_name` | str | 是 | 目标队列名 |
| `msg_body` | dict | 是 | 函数入参字典（**注意：是 `msg_body` 不是 `msg`**） |
| `need_result` | bool | 否 | 是否等待返回结果（默认 false） |
| `timeout` | int | 否 | 等待结果超时秒数（默认 60） |

## Flask 集成

```python
from flask import Flask
from funboost.faas import flask_blueprint

app = Flask(__name__)
app.register_blueprint(flask_blueprint)

# 正常定义 @boost 任务...
```

## 发布端与消费端分离

**发布端（Web 服务器）：**

```python
# web_app.py
from fastapi import FastAPI
from funboost.faas import fastapi_router

app = FastAPI()
app.include_router(fastapi_router)

# 注意：FaaS router 默认从 Redis 元数据动态发现队列
# 仅当设置环境变量 os.environ['funboost.faas.is_use_local_booster'] = 'true' 时才需要本地导入任务模块
```

**消费端（Worker 进程）：**

```python
# worker.py
from tasks import send_email, process_order

send_email.consume()
process_order.consume()
```

## 自定义 API 接口（手动方式）

如果内置 router 不满足需求：

```python
from fastapi import FastAPI
from funboost import boost, BoosterParams, BrokerEnum

app = FastAPI()

@boost(BoosterParams(
    queue_name="custom_task",
    broker_kind=BrokerEnum.REDIS_ACK_ABLE,
    is_using_rpc_mode=True,
))
def heavy_computation(data: list):
    return sum(data)

@app.post("/compute")
async def submit_computation(data: list[int]):
    result = await heavy_computation.aio_push(data)
    return {"task_id": result.task_id}

@app.get("/compute/{task_id}")
async def get_result(task_id: str):
    from funboost.core.msg_result_getter import AioAsyncResult
    aio_result = AioAsyncResult(task_id)
    status_dict = await aio_result.status_and_result
    return {"success": status_dict.get("success"), "result": status_dict.get("result")}
```

## 常见错误

| 错误 | 修正 |
|------|------|
| 手动编写发布/结果 API | 先试用 `fastapi_router` / `flask_blueprint` |
| 在 Web 进程中启动消费者 | 消费者应分离到 Worker 进程 |
| 需要查询结果但忘了 `is_using_rpc_mode=True` | 自定义 API 需启用 RPC；FastAPI/Flask 内置 router 可通过 `need_result=true` 自动启用；Django adapter 仍要求消费端已配置 `is_using_rpc_mode=True` |
| Web 应用中没有配置队列发现 | 确保 Consumer 进程已启动（会向 Redis 注册队列元数据） |
| 在 async FastAPI 中用同步 `AsyncResult.result` | 使用 `AioAsyncResult` + `await` |

## 相关 Skill

- `funboost-rpc-mode` — 获取任务执行返回值
- `funboost-funweb-ops` — Web 管理界面运维
