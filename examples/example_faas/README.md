# funboost faas （Function as a Service） 示例

本示例演示如何在funboost faas 用法。

```
funboost faas ,可以单独部署启动消费，用户可以让booster随着web一起启动，也可以单独启动消费。

因为 funboost.faas 是基于funboost注册到redis中的元数据驱动，所以可以动态发现booster，
所以只要消费函数部署上线了，web服务完全无需重启，从http接口马上就能调用了，
相比传统web开发，加一个功能就要加一个接口，然后重启web，funboost faas爽的一逼。
```


## 📁 文件说明

### 1. `task_funs_dir` - 任务函数定义文件夹

**作用**: 定义需要被 Funboost 管理的消费函数（任务函数）

`Project1BoosterParams` 是 `BoosterParams`子类 ，每个消费函数可以直接用这个子类，减少每个装饰器都重复相同入参




### 2. `example_fastapi_faas.py` - FastAPI 应用主入口

**作用**: FastAPI 应用的主程序，展示如何一键集成 Funboost 路由，实现faas

运行 Uvicorn 服务器


**核心代码**:
```python
from funboost.faas import fastapi_router,CareProjectNameEnv

CareProjectNameEnv.set('test_project1') # 可选，只关注指定的test_project1项目下的队列

app = FastAPI()
app.include_router(fastapi_router)  # 核心用法：一行代码集成



if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**访问地址**:
- API 文档: http://127.0.0.1:8000/docs
- 根路径: http://127.0.0.1:8000/

---

### 3. `start_consume.py` - 独立消费者启动脚本

**作用**: 演示如何单独启动 Funboost 消费者，而不随 FastAPI 一起启动



---

### 4. `example_req_fastapi.py` - API 测试客户端

**作用**: 演示如何调用 Funboost FastAPI 路由的各个接口

**包含的测试用例**:

#### 测试 1: `test_publish_and_get_result()`
- **功能**: 发布任务并同步等待结果
- **请求**: `POST /funboost/publish`
- **参数**:
  ```json
  {
    "queue_name": "test_fastapi_router_queue",
    "msg_body": {"x": 10, "y": 20},
    "need_result": true,
    "timeout": 10
  }
  ```
- **特点**: `need_result=True` 时，接口会阻塞等待任务完成并返回结果

#### 测试 2: `test_get_msg_count()`
- **功能**: 获取指定队列的消息数量
- **请求**: `GET /funboost/get_msg_count?queue_name=test_fastapi_router_queue`
- **用途**: 监控队列积压情况

#### 测试 3: `test_publish_async_then_get_result()`
- **功能**: 异步发布任务，先获取 task_id，再通过 task_id 查询结果
- **流程**:
  1. 发布任务（`need_result=False`），立即返回 task_id
  2. 使用 task_id 调用 `GET /funboost/get_result` 获取结果
- **优势**: 不阻塞，适合长时间任务

**运行方式**:
```bash
python example_req_fastapi.py
```

---





