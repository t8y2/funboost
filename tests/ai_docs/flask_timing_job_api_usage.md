# Flask Adapter 定时任务接口使用说明

## 📋 概述

已经将 FastAPI adapter 中的所有定时任务管理接口完整移植到 Flask adapter (`flask_adapter.py`)，现在可以直接在 Flask 应用中使用这些接口。

## 🚀 快速开始

### 1. 注册 Blueprint

在你的 Flask 应用中注册 `flask_blueprint`：

```python
from flask import Flask
from funboost.faas.flask_adapter import flask_blueprint

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

# 注册 funboost blueprint
app.register_blueprint(flask_blueprint)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
```

### 2. 访问接口

启动 Flask 应用后，可以通过以下路径访问定时任务接口：

- 基础路径：`http://localhost:5000/funboost`
- 例如：`http://localhost:5000/funboost/add_timing_job`

## 📚 接口列表

### 1. 添加定时任务

**接口**: `POST /funboost/add_timing_job`

**请求体示例**:

```json
{
    "queue_name": "test_queue",
    "trigger": "interval",
    "seconds": 10,
    "job_id": "my_job_001",
    "job_store_kind": "redis",
    "replace_existing": false
}
```

**触发器类型**:

1. **date** - 一次性任务
   ```json
   {
       "queue_name": "test_queue",
       "trigger": "date",
       "run_date": "2025-12-15 10:00:00"
   }
   ```

2. **interval** - 间隔执行
   ```json
   {
       "queue_name": "test_queue",
       "trigger": "interval",
       "minutes": 10
   }
   ```

3. **cron** - 定时执行
   ```json
   {
       "queue_name": "test_queue",
       "trigger": "cron",
       "hour": "9",
       "minute": "0"
   }
   ```

**响应示例**:
```json
{
    "succ": true,
    "msg": "定时任务添加成功",
    "data": {
        "job_id": "my_job_001",
        "queue_name": "test_queue",
        "trigger": "interval",
        "next_run_time": "2025-12-11 16:40:00"
    }
}
```

### 2. 获取定时任务列表

**接口**: `GET /funboost/get_timing_jobs`

**查询参数**:
- `queue_name` (可选): 队列名称，不提供则获取所有队列的任务
- `job_store_kind` (可选): 存储类型，默认 `redis`

**请求示例**:
```bash
# 获取所有任务
GET /funboost/get_timing_jobs

# 获取指定队列的任务
GET /funboost/get_timing_jobs?queue_name=test_queue

# 指定存储类型
GET /funboost/get_timing_jobs?job_store_kind=redis
```

**响应示例**:
```json
{
    "succ": true,
    "msg": "获取成功",
    "data": {
        "jobs": [
            {
                "job_id": "my_job_001",
                "queue_name": "test_queue",
                "trigger": "interval[0:00:10]",
                "next_run_time": "2025-12-11 16:40:00"
            }
        ],
        "count": 1
    }
}
```

### 3. 获取单个任务详情

**接口**: `GET /funboost/get_timing_job`

**查询参数**:
- `job_id` (必填): 任务ID
- `queue_name` (必填): 队列名称
- `job_store_kind` (可选): 存储类型，默认 `redis`

**请求示例**:
```bash
GET /funboost/get_timing_job?job_id=my_job_001&queue_name=test_queue
```

**响应示例**:
```json
{
    "succ": true,
    "msg": "获取成功",
    "data": {
        "job_id": "my_job_001",
        "queue_name": "test_queue",
        "trigger": "interval[0:00:10]",
        "next_run_time": "2025-12-11 16:40:00"
    }
}
```

### 4. 删除定时任务

**接口**: `DELETE /funboost/delete_timing_job`

**查询参数**:
- `job_id` (必填): 任务ID
- `queue_name` (必填): 队列名称
- `job_store_kind` (可选): 存储类型，默认 `redis`

**请求示例**:
```bash
DELETE /funboost/delete_timing_job?job_id=my_job_001&queue_name=test_queue
```

**响应示例**:
```json
{
    "succ": true,
    "msg": "定时任务 my_job_001 删除成功",
    "data": null
}
```

### 5. 删除所有任务

**接口**: `DELETE /funboost/delete_all_timing_jobs`

**查询参数**:
- `queue_name` (可选): 队列名称，不提供则删除所有队列的任务
- `job_store_kind` (可选): 存储类型，默认 `redis`

**请求示例**:
```bash
# 删除所有队列的所有任务
DELETE /funboost/delete_all_timing_jobs

# 删除指定队列的所有任务
DELETE /funboost/delete_all_timing_jobs?queue_name=test_queue
```

**响应示例**:
```json
{
    "succ": true,
    "msg": "成功删除 5 个定时任务",
    "data": {
        "deleted_count": 5,
        "failed_jobs": []
    }
}
```

### 6. 暂停定时任务

**接口**: `POST /funboost/pause_timing_job`

**查询参数**:
- `job_id` (必填): 任务ID
- `queue_name` (必填): 队列名称
- `job_store_kind` (可选): 存储类型，默认 `redis`

**请求示例**:
```bash
POST /funboost/pause_timing_job?job_id=my_job_001&queue_name=test_queue
```

**响应示例**:
```json
{
    "succ": true,
    "msg": "定时任务 my_job_001 已暂停",
    "data": null
}
```

### 7. 恢复定时任务

**接口**: `POST /funboost/resume_timing_job`

**查询参数**:
- `job_id` (必填): 任务ID
- `queue_name` (必填): 队列名称
- `job_store_kind` (可选): 存储类型，默认 `redis`

**请求示例**:
```bash
POST /funboost/resume_timing_job?job_id=my_job_001&queue_name=test_queue
```

**响应示例**:
```json
{
    "succ": true,
    "msg": "定时任务 my_job_001 已恢复",
    "data": null
}
```

## 🧪 使用 curl 测试

### 添加任务
```bash
curl -X POST http://localhost:5000/funboost/add_timing_job \
  -H "Content-Type: application/json" \
  -d '{
    "queue_name": "test_queue",
    "trigger": "interval",
    "seconds": 10
  }'
```

### 查询任务列表
```bash
curl http://localhost:5000/funboost/get_timing_jobs
```

### 删除任务
```bash
curl -X DELETE "http://localhost:5000/funboost/delete_timing_job?job_id=my_job_001&queue_name=test_queue"
```

## 📝 Python 调用示例

```python
import requests

BASE_URL = "http://localhost:5000/funboost"

# 1. 添加定时任务
def add_job():
    url = f"{BASE_URL}/add_timing_job"
    data = {
        "queue_name": "test_queue",
        "trigger": "interval",
        "seconds": 10,
        "job_id": "my_test_job"
    }
    response = requests.post(url, json=data)
    print(response.json())

# 2. 获取任务列表
def get_jobs():
    url = f"{BASE_URL}/get_timing_jobs"
    params = {"queue_name": "test_queue"}
    response = requests.get(url, params=params)
    print(response.json())

# 3. 删除任务
def delete_job(job_id, queue_name):
    url = f"{BASE_URL}/delete_timing_job"
    params = {
        "job_id": job_id,
        "queue_name": queue_name
    }
    response = requests.delete(url, params=params)
    print(response.json())

if __name__ == "__main__":
    add_job()
    get_jobs()
    # delete_job("my_test_job", "test_queue")
```

## ⚠️ 注意事项

1. **队列必须存在**: 添加定时任务前，确保队列已通过 `@boost` 装饰器注册
2. **存储方式**: 
   - `redis`: 支持分布式，任务持久化（推荐生产环境）
   - `memory`: 仅内存存储，进程重启后任务丢失
3. **任务ID**: 如果不指定 `job_id`，系统会自动生成唯一ID
4. **触发器参数**: 不同触发器类型需要提供不同的参数，详见接口文档

## 🔗 相关接口

除了定时任务接口外，Flask adapter 还提供了以下接口：

- `POST /funboost/publish` - 发布消息
- `GET /funboost/get_result` - 获取任务结果
- `GET /funboost/get_msg_count` - 获取队列消息数量
- `GET /funboost/get_all_queues` - 获取所有队列

完整的接口可以通过查看 `flask_adapter.py` 源码了解。

## 📖 更多信息

- 源码位置: `funboost/faas/flask_adapter.py`
- 定时任务核心: `funboost/timing_job/timing_push.py`
- APScheduler 文档: https://apscheduler.readthedocs.io/
