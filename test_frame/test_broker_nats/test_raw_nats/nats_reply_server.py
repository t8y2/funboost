# -*- coding: utf-8 -*-
"""
原生 NATS Request-Reply 服务端
启动后等待请求，计算 x+y 并响应结果
"""
import asyncio
import json
import time
import nats


async def main():
    nc = await nats.connect("nats://127.0.0.1:4222")

    async def handle_request(msg):
        data = json.loads(msg.data)
        x, y = data['x'], data['y']
        result = x + y
        await msg.respond(json.dumps(result).encode())

    await nc.subscribe("raw_rpc_add", cb=handle_request)
    print(f"[服务端] 已启动，监听 raw_rpc_add，等待请求...")

    try:
        await asyncio.Event().wait()
    except asyncio.CancelledError:
        pass
    finally:
        await nc.close()


if __name__ == '__main__':
    asyncio.run(main())
