
from funboost import MemoryFunboostPool

def add(a, b):
    return a + b

# 实例化任务池
pool = MemoryFunboostPool(10, qps=20,)

# 提交单个任务
future = pool.submit(add, 5, 3)
print(future.result())  # 输出: 8

# 使用 map 批量提交
results = pool.map(add, [1, 2, 3], [4, 5, 6])
print(list(results))  # 输出: [5, 7, 9]