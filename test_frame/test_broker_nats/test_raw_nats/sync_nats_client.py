# -*- coding: utf-8 -*-
"""
同步风格的 NATS 客户端，连接复用，线程安全
"""
import asyncio
import json
import threading
from nats.aio.client import Client as NATS


class SyncNATSClient:
    """同步风格的 NATS 客户端，连接复用，线程安全"""

    def __init__(self, servers="nats://localhost:4222", **options):
        self._servers = servers
        self._options = options

        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._nc = NATS()
        self._connected = False

    def _run_loop(self):
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    async def _async_connect(self):
        await self._nc.connect(self._servers, **self._options)

    def connect(self):
        """建立连接（同步阻塞直到连上）"""
        if self._connected:
            return
        self._thread.start()
        future = asyncio.run_coroutine_threadsafe(self._async_connect(), self._loop)
        future.result()
        self._connected = True

    def close(self):
        """关闭连接和事件循环"""
        if not self._connected:
            return
        close_future = asyncio.run_coroutine_threadsafe(self._nc.close(), self._loop)
        close_future.result()
        self._loop.call_soon_threadsafe(self._loop.stop)
        self._thread.join()
        self._connected = False

    def request(self, subject, payload, timeout=5):
        """同步发送请求并等待响应"""
        if not self._connected:
            raise RuntimeError("客户端未连接，请先调用 connect()")

        async def _req():
            return await self._nc.request(
                subject,
                json.dumps(payload).encode(),
                timeout=timeout
            )

        future = asyncio.run_coroutine_threadsafe(_req(), self._loop)
        try:
            resp = future.result(timeout=timeout + 1)
            return json.loads(resp.data.decode())
        except Exception:
            future.cancel()
            raise

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False