"""round3 验证 funboost-spider-crawling SKILL — SpiderResponse 解析方法"""
import os
import sys
import time

import httpx

os.environ["LOG_PATH"] = r"D:\pythonlogs\ai_console_outs"
_ts = int(time.time())
os.environ["PRINT_WRTIE_FILE_NAME"] = f"r3_spider_response_{_ts}"
os.environ["SYS_STD_FILE_NAME"] = f"r3_spider_response_std_{_ts}"

PASS = True


def report(name: str, ok: bool, detail: str = ""):
    global PASS
    if not ok:
        PASS = False
    status = "PASS" if ok else "FAIL"
    msg = f"[{status}] {name}"
    if detail:
        msg += f" — {detail}"
    print(msg)


try:
    from funboost.contrib.funspider import SpiderResponse
    report("import SpiderResponse", True)
except Exception as e:
    report("import SpiderResponse", False, str(e))
    time.sleep(12)
    os._exit(66)


def _make_resp(text: str, url: str = "https://example.com/page") -> SpiderResponse:
    req = httpx.Request("GET", url)
    raw = httpx.Response(200, text=text, request=req)
    return SpiderResponse(raw)


if __name__ == "__main__":
    try:
        html = """
        <html><body>
        <h1>Hello Title</h1>
        <a class="title" href="/news/123">link1</a>
        <a class="title" href="/news/456">link2</a>
        <div class="item">A</div><div class="item">B</div>
        </body></html>
        """
        resp = _make_resp(html, "https://example.com/news/789/page")

        title = resp.css("h1::text").get()
        report("resp.css('h1::text').get()", title == "Hello Title", repr(title))

        links = resp.css("a.title::attr(href)").getall()
        report("resp.css('a.title::attr(href)').getall()", links == ["/news/123", "/news/456"], repr(links))

        news_id = resp.re_first(r"/news/(\d+)")
        report("resp.re_first(r'/news/(\\d+)')", news_id == "789", repr(news_id))

        items = resp.xpath("//div[@class='item']//text()").getall()
        report("resp.xpath(...).getall()", "A" in items and "B" in items, repr(items))

        json_resp = _make_resp('{"key": "val", "n": 1}', "https://api.example.com")
        data = json_resp.resp_dict
        report("resp.resp_dict JSON 解析", data == {"key": "val", "n": 1}, repr(data))
    except Exception as e:
        report("SpiderResponse 解析示例", False, str(e))

    print(f"\n=== 最终结果: {'PASS' if PASS else 'FAIL'} ===")
    sys.stdout.flush()
    time.sleep(12)
    os._exit(66)
