import uvicorn
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse, JSONResponse

app = FastAPI()

NEWS_DATA = [
    {"id": i, "title": f"第{i}条新闻：{'人工智能' if i % 3 == 0 else '量子计算' if i % 3 == 1 else '航天探索'}领域重大突破", "summary": f"这是第{i}条新闻的摘要内容，涵盖了最新的科技动态。"}
    for i in range(1, 51)
]

COMMENTS_DATA = {
    i: [
        {"id": j, "news_id": i, "user": f"user_{i}_{j}", "content": f"这是对第{i}条新闻的第{j}条评论，{'说得好！' if j % 2 == 0 else '有不同看法。'}", "like_count": (i * j) % 100}
        for j in range(1, (i % 5) + 3)
    ]
    for i in range(1, 51)
}


@app.get("/", response_class=HTMLResponse)
def index():
    return '<h1>Fake News Site</h1><p><a href="/news/list?page=1">新闻列表</a></p>'


@app.get("/news/list", response_class=HTMLResponse)
def news_list(page: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=50)):
    start = (page - 1) * page_size
    end = start + page_size
    items = NEWS_DATA[start:end]
    total_pages = (len(NEWS_DATA) + page_size - 1) // page_size

    rows = ""
    for item in items:
        rows += f'''
        <tr>
            <td>{item['id']}</td>
            <td><a href="/news/detail/{item['id']}">{item['title']}</a></td>
            <td>{item['summary'][:20]}...</td>
        </tr>'''

    nav = ""
    if page > 1:
        nav += f'<a class="prev-page" href="/news/list?page={page-1}&page_size={page_size}">上一页</a> '
    if page < total_pages:
        nav += f'<a class="next-page" href="/news/list?page={page+1}&page_size={page_size}">下一页</a>'

    return f'''
    <html><body>
    <h1>新闻列表 - 第{page}页/共{total_pages}页</h1>
    <table border="1" cellpadding="5">
        <tr><th>ID</th><th>标题</th><th>摘要</th></tr>
        {rows}
    </table>
    <p>{nav}</p>
    </body></html>'''


@app.get("/news/detail/{news_id}", response_class=HTMLResponse)
def news_detail(news_id: int):
    news = NEWS_DATA[news_id - 1] if 1 <= news_id <= len(NEWS_DATA) else None
    if not news:
        return HTMLResponse("<h1>404 新闻不存在</h1>", status_code=404)

    comments = COMMENTS_DATA.get(news_id, [])
    comment_rows = ""
    for c in comments:
        comment_rows += f'''
        <tr>
            <td>{c['user']}</td>
            <td>{c['content']}</td>
            <td>{c['like_count']}</td>
        </tr>'''

    return f'''
    <html><body>
    <h1>{news['title']}</h1>
    <div class="content">
        <p>{news['summary']}</p>
        <p>这是第{news_id}条新闻的完整正文内容。当前新闻涉及领域正在经历快速发展，
        多项关键技术取得突破性进展。专家表示，这一趋势将在未来几年持续加速，
        对整个行业产生深远影响。</p>
        <p>发布时间：2025-01-{news_id:02d} 10:00:00</p>
        <p>作者：记者_{news_id}</p>
        <p>分类：{"科技" if news_id % 2 == 0 else "社会"}</p>
    </div>
    <h2>评论 ({len(comments)}条)</h2>
    <p><a href="/news/comments/{news_id}">查看全部评论</a></p>
    <table border="1" cellpadding="5">
        <tr><th>用户</th><th>内容</th><th>点赞</th></tr>
        {comment_rows}
    </table>
    <p><a href="/news/list?page=1">返回列表</a></p>
    </body></html>'''


@app.get("/news/comments/{news_id}", response_class=JSONResponse)
def news_comments(news_id: int):
    if news_id not in COMMENTS_DATA:
        return {"news_id": news_id, "comments": [], "total": 0}
    comments = COMMENTS_DATA[news_id]
    return {"news_id": news_id, "comments": comments, "total": len(comments)}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8888)
