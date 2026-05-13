# -*- coding: utf-8 -*-
"""
原生 NATS Request-Reply 客户端
发送请求并统计 QPS 和平均延迟，可对比 HTTP 性能
"""
import asyncio
import json
import time
import nats
from nb_aiopool import NbAioPool

async def bench_nats(total: int = 10000, concurrency: int = 50):
    nc = await nats.connect("nats://127.0.0.1:4222")

    print(f"[客户端] NATS Request-Reply 压测  总请求: {total}  并发: {concurrency}")
    print()

    latencies = []
    t_start = time.monotonic()

    async def one_request(i):
        t0 = time.monotonic()
        response = await nc.request("raw_rpc_add", json.dumps({"x": i, "y": i * 10}).encode(), timeout=5)
        t1 = time.monotonic()
        result = json.loads(response.data)
        latencies.append(t1 - t0)
        if i < 5:
            print(f"  request({i}, {i * 10}) -> {result}  耗时: {round((t1 - t0) * 1000, 2)}ms")

    async with NbAioPool(max_concurrency=concurrency, max_queue_size=total) as pool:
        coros = [one_request(i) for i in range(total)]
        await pool.batch_run(coros, block=True)

    t_end = time.monotonic()
    total_time = t_end - t_start

    latencies.sort()
    avg_ms = sum(latencies) / len(latencies) * 1000
    p50_ms = latencies[len(latencies) // 2] * 1000
    p99_ms = latencies[int(len(latencies) * 0.99)] * 1000
    qps = total / total_time

    print()
    print(f"=== NATS Request-Reply 压测结果 ===")
    print(f"  总请求数:   {total}")
    print(f"  并发数:     {concurrency}")
    print(f"  总耗时:     {round(total_time, 3)}s")
    print(f"  QPS:        {round(qps, 1)}")
    print(f"  平均延迟:   {round(avg_ms, 3)}ms")
    print(f"  P50 延迟:   {round(p50_ms, 3)}ms")
    print(f"  P99 延迟:   {round(p99_ms, 3)}ms")


    await nc.close()


if __name__ == '__main__':
    asyncio.run(bench_nats(total=100000, concurrency=10))
