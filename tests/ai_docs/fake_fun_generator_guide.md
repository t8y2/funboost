# FakeFunGenerator 动态函数生成器说明

## 🎯 功能说明

`FakeFunGenerator` 是一个能够根据参数元数据动态生成函数对象的工具类。主要用于 **funboost.faas** 场景，允许 web 服务在没有真正函数定义的情况下进行参数校验。

## 📋 核心方法

### `gen_fun_by_params(must_arg_name_list, optional_arg_name_list, func_name)`

根据必需参数和可选参数列表动态生成一个具有正确签名的函数。

**参数：**
- `must_arg_name_list`: 必需参数列表（无默认值的位置参数）
- `optional_arg_name_list`: 可选参数列表（有默认值的关键字参数）
- `func_name`: 生成的函数名称

**返回：**
- 动态生成的函数对象，具有正确的参数签名

## 💡 使用示例

### 示例 1: 基本用法

```python
from funboost.core.consuming_func_iniput_params_check import FakeFunGenerator
import inspect

# 生成一个函数：def my_func(x, y, z=None, w=None)
func = FakeFunGenerator.gen_fun_by_params(
    must_arg_name_list=['x', 'y'],
    optional_arg_name_list=['z', 'w'],
    func_name='my_func'
)

# 检查函数签名
print(inspect.signature(func))
# 输出: (x, y, z=None, w=None)

# 获取参数信息
spec = inspect.getfullargspec(func)
print(spec.args)        # ['x', 'y', 'z', 'w']
print(spec.defaults)    # (None, None)
```

### 示例 2: 只有必需参数

```python
# 生成: def process(a, b, c)
func = FakeFunGenerator.gen_fun_by_params(
    must_arg_name_list=['a', 'b', 'c'],
    optional_arg_name_list=[],
    func_name='process'
)

spec = inspect.getfullargspec(func)
print(spec.args)        # ['a', 'b', 'c']
print(spec.defaults)    # None（没有默认值）
```

### 示例 3: 只有可选参数

```python
# 生成: def config(opt1=None, opt2=None)
func = FakeFunGenerator.gen_fun_by_params(
    must_arg_name_list=[],
    optional_arg_name_list=['opt1', 'opt2'],
    func_name='config'
)

spec = inspect.getfullargspec(func)
print(spec.args)        # ['opt1', 'opt2']
print(len(spec.defaults))  # 2（两个参数都有默认值）
```

## 🔧 与 ConsumingFuncInputParamsChecker 配合使用

动态生成的函数可以被 `ConsumingFuncInputParamsChecker` 正确解析：

```python
from funboost.core.consuming_func_iniput_params_check import (
    FakeFunGenerator, 
    ConsumingFuncInputParamsChecker
)

# 1. 动态生成函数
func = FakeFunGenerator.gen_fun_by_params(
    must_arg_name_list=['user_id', 'amount'],
    optional_arg_name_list=['currency', 'memo'],
    func_name='process_payment'
)

# 2. 提取参数信息
params_info = ConsumingFuncInputParamsChecker.gen_func_params_info_by_func(func)

print(params_info)
# {
#     'func_name': 'process_payment',
#     'func_position': '<function process_payment at 0x...>',
#     'is_manual_func_input_params': False,
#     'all_arg_name_list': ['user_id', 'amount', 'currency', 'memo'],
#     'must_arg_name_list': ['user_id', 'amount'],
#     'optional_arg_name_list': ['currency', 'memo']
# }

# 3. 创建参数检查器
checker = ConsumingFuncInputParamsChecker(params_info)

# 4. 校验发布参数
checker.check_params({'user_id': 123, 'amount': 100})  # ✅ 通过
checker.check_params({'user_id': 123, 'amount': 100, 'currency': 'USD'})  # ✅ 通过
checker.check_params({'user_id': 123})  # ❌ 缺少必需参数 amount
checker.check_params({'user_id': 123, 'amount': 100, 'unknown': 'x'})  # ❌ 包含未定义参数
```

## 🚀 funboost.faas 应用场景

### 传统方式的问题

在传统的 web 服务 + 任务队列架构中：
- web 服务需要导入消费函数
- web 服务和消费服务紧耦合
- 修改消费函数需要重启 web 服务

### funboost.faas 的解决方案

使用 `FakeFunGenerator`，web 服务完全不需要真正的函数对象：

```python
# === 消费服务端 ===
from funboost import boost

@boost('user_queue', qps=10, project_name='my_project')
def register_user(username, email, password, phone=None):
    # 注册用户逻辑
    pass

# 消费函数启动后，参数信息自动保存到 redis


# === Web 服务端（FastAPI） ===
from funboost.faas import fastapi_router, SingleQueueConusmerParamsGetter
from funboost.core.consuming_func_iniput_params_check import FakeFunGenerator

# 1. 从 redis 读取元数据
queue_params = SingleQueueConusmerParamsGetter('user_queue').get_one_queue_params_use_cache()
func_params_info = queue_params['auto_generate_info']['final_func_input_params_info']

# 2. 动态生成伪函数（无需真正的函数定义）
fake_func = FakeFunGenerator.gen_fun_by_params(
    must_arg_name_list=func_params_info['must_arg_name_list'],
    optional_arg_name_list=func_params_info['optional_arg_name_list'],
    func_name=func_params_info['func_name']
)

# 3. 创建参数检查器
checker = ConsumingFuncInputParamsChecker(func_params_info)

# 4. 校验用户发布的参数
# 现在 web 服务可以在发布前进行参数校验，无需导入真正的消费函数！
```

## ✨ 优势总结

1. **完全解耦**
   - web 服务无需导入消费函数
   - 无需消费函数的源代码
   - 只依赖 redis 中的元数据

2. **动态更新**
   - 修改消费函数后，web 服务自动获取新的参数信息
   - 无需重启 web 服务
   - 真正的热更新

3. **灵活部署**
   - web 服务和消费服务可以独立部署
   - 消费函数可以用不同的语言实现（只要元数据兼容）
   - 支持多版本并存

4. **参数校验**
   - 在 web 层就能校验参数
   - 避免无效任务进入队列
   - 提供友好的错误提示

## 🔬 实现原理

使用 Python 的 `exec` 动态执行代码生成函数：

```python
def gen_fun_by_params(must_arg_name_list, optional_arg_name_list, func_name):
    # 构建参数字符串
    must_params = 'x, y'  # 必需参数
    optional_params = 'z=None, w=None'  # 可选参数
    all_params = 'x, y, z=None, w=None'
    
    # 动态生成函数代码
    func_code = f'''
def {func_name}({all_params}):
    return locals()
'''
    
    # 执行代码，在独立命名空间中
    namespace = {}
    exec(func_code, {}, namespace)
    
    # 返回生成的函数对象
    return namespace[func_name]
```

生成的函数：
- 具有正确的 `__name__` 属性
- 具有正确的参数签名
- 可以被 `inspect` 模块解析
- 可以正常调用

## 📚 相关文档

- `ConsumingFuncInputParamsChecker`: 参数检查器
- `funboost.faas`: 基于元数据的 FaaS 架构
- `SingleQueueConusmerParamsGetter`: 从 redis 获取队列元数据
