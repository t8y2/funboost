# 定时任务 API 接口说明

## 概述

FastAPI 路由现在提供了完整的定时任务管理接口，支持通过 HTTP API 动态添加、查询、删除、暂停和恢复定时任务。

## 新增接口列表

| 接口 | 方法 | 功能 |
|------|------|------|
| `/funboost/add_timing_job` | POST | 添加定时任务 |
| `/funboost/get_timing_jobs` | GET | 获取定时任务列表 |
| `/funboost/delete_timing_job` | DELETE | 删除定时任务 |
| `/funboost/pause_timing_job` | POST | 暂停定时任务 |
| `/funboost/resume_timing_job` | POST | 恢复定时任务 |

## 定时触发方式

支持 **3 种定时触发方式**，与 APScheduler 完全兼容：

### 1. date - 指定时间执行一次

在指定的日期时间执行一次任务。

**参数：**
- `run_date`: 运行时间，格式: `"YYYY-MM-DD HH:MM:SS"`

**示例：**
```json
{
  "queue_name": "test_queue",
  "trigger": "date",
  "run_date": "2025-12-03 15:00:00",
  "job_id": "my_date_job",
  "args": [10, 20],
  "job_store_kind": "redis"
}
```

### 2. interval - 固定间隔执行

按固定时间间隔重复执行任务。

**参数：**
- `weeks`: 周数
- `days`: 天数
- `hours`: 小时数
- `minutes`: 分钟数
- `seconds`: 秒数

**示例：**
```json
{
  "queue_name": "test_queue",
  "trigger": "interval",
  "seconds": 10,
  "job_id": "my_interval_job",
  "kwargs": {"x": 1, "y": 2},
  "job_store_kind": "redis"
}
```

### 3. cron - Cron 表达式执行

使用 cron 表达式定时执行任务。

**参数：**
- `year`: 年份 (4位数字)
- `month`: 月份 (1-12)
- `day`: 日期 (1-31)
- `week`: 周 (1-53)
- `day_of_week`: 星期 (0-6 或 mon,tue,wed,thu,fri,sat,sun)
- `hour`: 小时 (0-23)
- `minute`: 分钟 (0-59)
- `second`: 秒 (0-59)

**Cron 表达式说明：**
- 使用 `*` 表示任意值
- 使用 `*/n` 表示每 n 个单位
- 使用 `a-b` 表示范围
- 使用 `a,b,c` 表示多个值

**示例 1 - 每天下午 3 点半执行：**
```json
{
  "queue_name": "test_queue",
  "trigger": "cron",
  "hour": "15",
  "minute": "30",
  "job_id": "daily_3pm_job",
  "args": [1, 2],
  "job_store_kind": "redis"
}
```

**示例 2 - 每 2 小时执行一次：**
```json
{
  "queue_name": "test_queue",
  "trigger": "cron",
  "hour": "*/2",
  "minute": "0",
  "job_id": "every_2_hours_job",
  "kwargs": {"x": 10, "y": 20},
  "job_store_kind": "redis"
}
```

**示例 3 - 工作日每天上午 9 点执行：**
```json
{
  "queue_name": "test_queue",
  "trigger": "cron",
  "day_of_week": "mon-fri",
  "hour": "9",
  "minute": "0",
  "job_id": "weekday_morning_job",
  "job_store_kind": "redis"
}
```

## API 详细说明

### 1. 添加定时任务

**接口：** `POST /funboost/add_timing_job`

**请求参数：**
```json
{
  "queue_name": "队列名称（必填）",
  "trigger": "触发器类型: date/interval/cron（必填）",
  "job_id": "任务ID（可选，不提供则自动生成）",
  "job_store_kind": "存储方式: redis/memory（默认: redis）",
  "replace_existing": "是否替换已存在的任务（默认: false）",
  
  "args": [1, 2],  // 位置参数（可选）
  "kwargs": {"x": 1, "y": 2},  // 关键字参数（可选）
  
  // 根据 trigger 类型提供相应参数
  "run_date": "2025-12-03 15:00:00",  // date 触发器
  "seconds": 10,  // interval 触发器
  "hour": "15",  // cron 触发器
  // ... 其他参数
}
```

**响应示例：**
```json
{
  "succ": true,
  "msg": "定时任务添加成功",
  "data": {
    "job_id": "my_job_123",
    "queue_name": "test_queue",
    "trigger": "cron",
    "next_run_time": "2025-12-03 15:00:00+08:00"
  }
}
```

### 2. 获取定时任务列表

**接口：** `GET /funboost/get_timing_jobs`

**查询参数：**
- `queue_name`: 队列名称（可选，不提供则获取所有队列的任务）
- `job_store_kind`: 存储方式，`redis` 或 `memory`（默认: redis）

**响应示例：**
```json
{
  "succ": true,
  "msg": "获取成功",
  "data": {
    "jobs": [
      {
        "job_id": "job1",
        "queue_name": "test_queue",
        "trigger": "cron",
        "next_run_time": "2025-12-03 15:00:00+08:00"
      },
      {
        "job_id": "job2",
        "queue_name": "test_queue",
        "trigger": "interval",
        "next_run_time": "2025-12-03 14:50:10+08:00"
      }
    ],
    "count": 2
  }
}
```

### 3. 删除定时任务

**接口：** `DELETE /funboost/delete_timing_job`

**查询参数：**
- `job_id`: 任务ID（必填）
- `queue_name`: 队列名称（必填）
- `job_store_kind`: 存储方式（默认: redis）

**响应示例：**
```json
{
  "succ": true,
  "msg": "定时任务 my_job_123 删除成功",
  "data": null
}
```

### 4. 暂停定时任务

**接口：** `POST /funboost/pause_timing_job`

**查询参数：**
- `job_id`: 任务ID（必填）
- `queue_name`: 队列名称（必填）
- `job_store_kind`: 存储方式（默认: redis）

**响应示例：**
```json
{
  "succ": true,
  "msg": "定时任务 my_job_123 已暂停",
  "data": null
}
```

### 5. 恢复定时任务

**接口：** `POST /funboost/resume_timing_job`

**查询参数：**
- `job_id`: 任务ID（必填）
- `queue_name`: 队列名称（必填）
- `job_store_kind`: 存储方式（默认: redis）

**响应示例：**
```json
{
  "succ": true,
  "msg": "定时任务 my_job_123 已恢复",
  "data": null
}
```

## Python 使用示例

```python
import requests
import json

base_url = "http://127.0.0.1:8000"

# 1. 添加一个每10秒执行一次的任务
def add_interval_job():
    url = f"{base_url}/funboost/add_timing_job"
    data = {
        "queue_name": "test_fastapi_router_queue",
        "trigger": "interval",
        "seconds": 10,
        "job_id": "interval_job_10s",
        "kwargs": {"x": 10, "y": 20},
        "job_store_kind": "redis",
        "replace_existing": True
    }
    
    resp = requests.post(url, json=data)
    print(json.dumps(resp.json(), indent=2, ensure_ascii=False))

# 2. 添加一个每天下午3点执行的任务
def add_cron_job():
    url = f"{base_url}/funboost/add_timing_job"
    data = {
        "queue_name": "test_fastapi_router_queue",
        "trigger": "cron",
        "hour": "15",
        "minute": "0",
        "job_id": "daily_3pm_job",
        "args": [100, 200],
        "job_store_kind": "redis"
    }
    
    resp = requests.post(url, json=data)
    print(json.dumps(resp.json(), indent=2, ensure_ascii=False))

# 3. 获取所有定时任务
def get_all_jobs():
    url = f"{base_url}/funboost/get_timing_jobs"
    params = {"job_store_kind": "redis"}
    
    resp = requests.get(url, params=params)
    print(json.dumps(resp.json(), indent=2, ensure_ascii=False))

# 4. 获取指定队列的定时任务
def get_queue_jobs():
    url = f"{base_url}/funboost/get_timing_jobs"
    params = {
        "queue_name": "test_fastapi_router_queue",
        "job_store_kind": "redis"
    }
    
    resp = requests.get(url, params=params)
    print(json.dumps(resp.json(), indent=2, ensure_ascii=False))

# 5. 暂停定时任务
def pause_job():
    url = f"{base_url}/funboost/pause_timing_job"
    params = {
        "job_id": "interval_job_10s",
        "queue_name": "test_fastapi_router_queue",
        "job_store_kind": "redis"
    }
    
    resp = requests.post(url, params=params)
    print(json.dumps(resp.json(), indent=2, ensure_ascii=False))

# 6. 恢复定时任务
def resume_job():
    url = f"{base_url}/funboost/resume_timing_job"
    params = {
        "job_id": "interval_job_10s",
        "queue_name": "test_fastapi_router_queue",
        "job_store_kind": "redis"
    }
    
    resp = requests.post(url, params=params)
    print(json.dumps(resp.json(), indent=2, ensure_ascii=False))

# 7. 删除定时任务
def delete_job():
    url = f"{base_url}/funboost/delete_timing_job"
    params = {
        "job_id": "interval_job_10s",
        "queue_name": "test_fastapi_router_queue",
        "job_store_kind": "redis"
    }
    
    resp = requests.delete(url, params=params)
    print(json.dumps(resp.json(), indent=2, ensure_ascii=False))

if __name__ == "__main__":
    print("1. 添加 interval 任务")
    add_interval_job()
    
    print("\n2. 添加 cron 任务")
    add_cron_job()
    
    print("\n3. 获取所有任务")
    get_all_jobs()
    
    print("\n4. 暂停任务")
    pause_job()
    
    print("\n5. 恢复任务")
    resume_job()
    
    print("\n6. 删除任务")
    delete_job()
```

## 注意事项

1. **job_store_kind 选择**：
   - `redis`: 任务持久化存储，服务重启后任务不丢失（推荐）
   - `memory`: 任务存储在内存，服务重启后任务丢失

2. **job_id 唯一性**：每个任务的 `job_id` 在同一个队列内必须唯一

3. **replace_existing**：如果设置为 `true`，会替换已存在的同名任务

4. **时区**：时间使用服务器配置的时区（FunboostCommonConfig.TIMEZONE）

5. **参数传递**：
   - 使用 `args` 传递位置参数：`[1, 2, 3]`
   - 使用 `kwargs` 传递关键字参数：`{"x": 1, "y": 2}`

## 总结

通过这些接口，你可以：
- ✅ 动态添加各种类型的定时任务
- ✅ 查询所有或指定队列的定时任务
- ✅ 暂停/恢复/删除定时任务
- ✅ 支持 date、interval、cron 三种触发方式
- ✅ 支持 redis 持久化存储

所有操作都通过简单的 HTTP API 完成，无需重启服务！🚀
