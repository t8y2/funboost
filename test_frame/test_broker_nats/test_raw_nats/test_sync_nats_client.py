# -*- coding: utf-8 -*-
"""
使用 SyncNATSClient 进行压测
演示同步风格的 NATS request-reply，统计 QPS 和延迟
"""
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from sync_nats_client import SyncNATSClient


def bench_sync_nats(total=100000, concurrency=50):
    with SyncNATSClient("nats://127.0.0.1:4222") as client:
        print(f"[SyncNATSClient] 压测  总请求: {total}  并发: {concurrency}")
        print()

        latencies = []
        t_start = time.monotonic()

        def one_request(i):
            t0 = time.monotonic()
            result = client.request("raw_rpc_add", {"x": i, "y": i * 10}, timeout=5)
            t1 = time.monotonic()
            latencies.append(t1 - t0)
            if i < 5:
                print(f"  request({i}, {i * 10}) -> {result}  耗时: {round((t1 - t0) * 1000, 2)}ms")

        with ThreadPoolExecutor(max_workers=concurrency) as pool:
            futures = [pool.submit(one_request, i) for i in range(total)]
            for f in as_completed(futures):
                f.result()

        t_end = time.monotonic()
        total_time = t_end - t_start

        latencies.sort()
        avg_ms = sum(latencies) / len(latencies) * 1000
        p50_ms = latencies[len(latencies) // 2] * 1000
        p99_ms = latencies[int(len(latencies) * 0.99)] * 1000
        qps = total / total_time

        print()
        print(f"=== SyncNATSClient 压测结果 ===")
        print(f"  总请求数:   {total}")
        print(f"  并发数:     {concurrency}")
        print(f"  总耗时:     {round(total_time, 3)}s")
        print(f"  QPS:        {round(qps, 1)}")
        print(f"  平均延迟:   {round(avg_ms, 3)}ms")
        print(f"  P50 延迟:   {round(p50_ms, 3)}ms")
        print(f"  P99 延迟:   {round(p99_ms, 3)}ms")


if __name__ == '__main__':
    bench_sync_nats(total=100000, concurrency=1000)