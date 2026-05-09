import json
import random
import httpx
from parsel import Selector
from typing import Optional, Dict, List, Callable
from funboost.core.loggers import get_funboost_file_logger

logger = get_funboost_file_logger('funspider.http')

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]


class SpiderResponse:
    """统一封装 httpx 响应，提供 xpath/css/re 解析"""
    def __init__(self, resp: httpx.Response):
        self.status_code = resp.status_code
        self.url = str(resp.url)
        self._text = resp.text
        self._selector: Optional[Selector] = None
        self._resp_dict: Optional[dict] = None

    @property
    def selector(self) -> Selector:
        if self._selector is None:
            self._selector = Selector(text=self._text)
        return self._selector

    @property
    def text(self) -> str:
        return self._text

    @property
    def resp_dict(self) -> dict:
        if self._resp_dict is None:
            self._resp_dict = json.loads(self._text)
        return self._resp_dict

    def xpath(self, query: str) -> list:
        return self.selector.xpath(query)

    def css(self, query: str) -> list:
        return self.selector.css(query)

    def re(self, pattern: str) -> List[str]:
        return self.selector.re(pattern)

    def re_first(self, pattern: str) -> Optional[str]:
        return self.selector.re_first(pattern)


class BaseSpiderClient:
    def __init__(
        self,
        retry_times: int = 2,
        timeout: float = 30,
        proxy_getter_list: Optional[List[Callable[[], Optional[str]]]] = None,
        user_agents: Optional[List[str]] = None,
    ):
        self.retry_times = retry_times
        self.timeout = timeout
        self._proxy_getter_list = proxy_getter_list or []
        self._proxy_index = 0
        self._user_agents = user_agents or USER_AGENTS

    def _random_ua(self) -> str:
        return random.choice(self._user_agents)

    def _merge_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        h = {"User-Agent": self._random_ua()}
        h.update(headers or {})
        return h

    def _get_proxy(self) -> Optional[str]:
        if not self._proxy_getter_list:
            return None
        func = self._proxy_getter_list[self._proxy_index % len(self._proxy_getter_list)]
        self._proxy_index += 1
        return func()


class SimpleSpiderClient(BaseSpiderClient):
    """同步爬虫客户端 (httpx.Client)"""
    def __init__(
        self,
        retry_times: int = 2,
        timeout: float = 30,
        proxy_getter_list: Optional[List[Callable[[], Optional[str]]]] = None,
        user_agents: Optional[List[str]] = None,
    ):
        super().__init__(retry_times, timeout, proxy_getter_list, user_agents)
        self.client = httpx.Client(timeout=self.timeout)

    def request(self, method: str, url: str, **kwargs) -> SpiderResponse:
        headers = self._merge_headers(kwargs.pop('headers', {}))
        last_exc = None
        for attempt in range(self.retry_times + 1):
            try:
                proxy = self._get_proxy()
                if proxy:
                    kwargs['proxy'] = proxy
                resp = self.client.request(method, url, headers=headers, **kwargs)
                resp.raise_for_status()
                return SpiderResponse(resp)
            except Exception as e:
                last_exc = e
                logger.warning(f"[Sync] {url} 请求失败 (第{attempt+1}次): {e}")
        raise last_exc

    def get(self, url: str, **kwargs) -> SpiderResponse:
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs) -> SpiderResponse:
        return self.request("POST", url, **kwargs)

    def close(self):
        self.client.close()


class AsyncSpiderClient(BaseSpiderClient):
    """异步爬虫客户端 (httpx.AsyncClient) – 不绑定 Loop，可在 Funboost ASYNC 模式自由使用"""
    def __init__(
        self,
        retry_times: int = 2,
        timeout: float = 30,
        proxy_getter_list: Optional[List[Callable[[], Optional[str]]]] = None,
        user_agents: Optional[List[str]] = None,
    ):
        super().__init__(retry_times, timeout, proxy_getter_list, user_agents)
        self.client = httpx.AsyncClient(timeout=self.timeout)

    async def request(self, method: str, url: str, **kwargs) -> SpiderResponse:
        headers = self._merge_headers(kwargs.pop('headers', {}))
        last_exc = None
        for attempt in range(self.retry_times + 1):
            try:
                proxy = self._get_proxy()
                if proxy:
                    kwargs['proxy'] = proxy
                resp = await self.client.request(method, url, headers=headers, **kwargs)
                resp.raise_for_status()
                return SpiderResponse(resp)
            except Exception as e:
                last_exc = e
                logger.warning(f"[Async] {url} 请求失败 (第{attempt+1}次): {e}")
        raise last_exc

    async def get(self, url: str, **kwargs) -> SpiderResponse:
        return await self.request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs) -> SpiderResponse:
        return await self.request("POST", url, **kwargs)

    async def aclose(self):
        await self.client.aclose()