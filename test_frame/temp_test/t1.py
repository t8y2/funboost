


class MyClass:
    def __init__(self,x):
        self.x = x

    def func(self, a, b, c=3, d=4, e=5):
        pass

print(str(type(MyClass)))

import time
time.sleep(10000)
print(str(type(MyClass)))