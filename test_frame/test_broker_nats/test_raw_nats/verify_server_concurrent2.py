# -*- coding: utf-8 -*-
"""
验证：观察服务端日志，看 handler 是否真的并发执行
"""
import asyncio
import json
import time
import nats


async def main():
    nc = await nats.connect("nats://127.0.0.1:4222")

    async def handle_request(msg):
        data = json.loads(msg.data)
        req_id = data['req_id']
        start = time.monotonic()
        print(f"  [handler-{req_id}] 开始执行，收到时间: {round(start * 1000)}ms")
        await asyncio.sleep(3)
        end = time.monotonic()
        print(f"  [handler-{req_id}] 执行完成，耗时: {round((end - start) * 1000)}ms")
        result = data['x'] + data['y']
        await msg.respond(json.dumps({'req_id': req_id, 'result': result}).encode())

    await nc.subscribe("raw_rpc_add", cb=handle_request)
    print("[服务端] 已启动，监听 raw_rpc_add，handler 模拟耗时 3 秒...")
    print()

    await asyncio.Event().wait()


if __name__ == '__main__':
    asyncio.run(main())