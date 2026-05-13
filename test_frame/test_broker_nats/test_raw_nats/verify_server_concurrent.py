# -*- coding: utf-8 -*-
"""
验证 NATS 服务端 handler 是否并发执行
"""
import asyncio
import json
import time
import nats


async def main():
    nc = await nats.connect("nats://127.0.0.1:4222")

    request_count = 0
    start_time = None

    async def handle_request(msg):
        nonlocal request_count, start_time
        request_count += 1
        if request_count == 1:
            start_time = time.monotonic()
        data = json.loads(msg.data)
        x, y = data['x'], data['y']
        await asyncio.sleep(3)
        result = x + y
        await msg.respond(json.dumps(result).encode())

    await nc.subscribe("raw_rpc_add", cb=handle_request)
    print("[服务端] 已启动，监听 raw_rpc_add，handler 模拟耗时 3 秒...")
    print()

    await asyncio.Event().wait()


if __name__ == '__main__':
    asyncio.run(main())