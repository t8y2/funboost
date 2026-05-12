# -*- coding: utf-8 -*-
"""
验证客户端：并发发 3 个请求，验证服务端是否并发处理
"""
import asyncio
import json
import time
import nats


async def main():
    nc = await nats.connect("nats://127.0.0.1:4222")

    async def one_request(i):
        t0 = time.monotonic()
        response = await nc.request("raw_rpc_add", json.dumps({"x": i, "y": i * 10}).encode(), timeout=10)
        t1 = time.monotonic()
        result = json.loads(response.data)
        print(f"  请求{i} 完成: {i} + {i*10} = {result}  耗时: {round((t1 - t0) * 1000, 1)}ms")
        return t1 - t0

    print("[客户端] 并发发送 3 个请求，handler 模拟耗时 3 秒...")
    print()

    t_start = time.monotonic()
    latencies = await asyncio.gather(*[one_request(i) for i in range(3)])
    t_end = time.monotonic()
    total_time = t_end - t_start

    print()
    print(f"=== 验证结果 ===")
    print(f"  3 个请求总耗时: {round(total_time, 2)}s")
    if total_time < 6:
        print(f"  结论: 并发处理（≈ handler 耗时 {3}s，而非 3×3=9s）")
    else:
        print(f"  结论: 顺序处理（耗时 {round(total_time,1)}s ≈ 3×3=9s）")

    await nc.close()


if __name__ == '__main__':
    asyncio.run(main())