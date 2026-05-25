import uvicorn
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse

app = FastAPI(title="3层新闻网站")

CATEGORIES = [
    {"id": 1, "name": "科技", "desc": "科技领域最新动态与突破"},
    {"id": 2, "name": "社会", "desc": "社会热点新闻深度报道"},
    {"id": 3, "name": "体育", "desc": "全球体育赛事精彩回顾"},
    {"id": 4, "name": "娱乐", "desc": "娱乐资讯与明星动态"},
]

NEWS_LIST = [
    {"id": 1, "cat_id": 1, "title": "量子计算新突破：中国团队成功研制512量子比特处理器", "author": "张科技", "summary": "我国科研团队在量子计算领域取得重大突破，成功研制出512量子比特的量子处理器。", "publish_time": "2025-01-15 09:00:00"},
    {"id": 2, "cat_id": 1, "title": "AI大模型应用落地：智能客服替代率超80%", "author": "李科技", "summary": "人工智能大模型在各行业的应用加速落地，智能客服替代率已超过80%。", "publish_time": "2025-01-16 10:30:00"},
    {"id": 3, "cat_id": 1, "title": "5G-Advanced标准正式冻结，6G研发加速推进", "author": "王科技", "summary": "5G-Advanced国际标准正式冻结，为下一代移动通信技术发展奠定基础。", "publish_time": "2025-01-18 14:00:00"},
    {"id": 4, "cat_id": 1, "title": "国产芯片工艺突破：3nm制程试产成功", "author": "张科技", "summary": "国内芯片制造企业宣布3纳米制程工艺试产成功，性能提升30%。", "publish_time": "2025-01-20 08:00:00"},
    {"id": 5, "cat_id": 1, "title": "自动驾驶L4级别商用落地，无人出租车覆盖10城", "author": "李科技", "summary": "多家自动驾驶企业获得L4级别商用许可，无人出租车已覆盖全国10个城市。", "publish_time": "2025-01-22 11:00:00"},
    {"id": 6, "cat_id": 1, "title": "区块链技术赋能供应链金融，融资效率提升300%", "author": "王科技", "summary": "区块链技术在供应链金融领域的应用取得显著成效，企业融资效率提升300%。", "publish_time": "2025-01-25 16:00:00"},
    {"id": 7, "cat_id": 2, "title": "老旧小区改造全面完成，惠及超500万户居民", "author": "赵社会", "summary": "全国城镇老旧小区改造工作已全面完成，惠及超过500万户居民。", "publish_time": "2025-02-01 09:00:00"},
    {"id": 8, "cat_id": 2, "title": "乡村振兴新举措：数字农业试点成效显著", "author": "钱社会", "summary": "数字农业在全国多个试点地区取得显著成效，农产品产量平均增长20%。", "publish_time": "2025-02-03 10:00:00"},
    {"id": 9, "cat_id": 2, "title": "垃圾分类全国推行，资源回收利用率达45%", "author": "赵社会", "summary": "垃圾分类制度在全国范围内推行，资源回收利用率已达到45%。", "publish_time": "2025-02-05 14:00:00"},
    {"id": 10, "cat_id": 2, "title": "高等教育毛入学率突破65%，迈入普及化阶段", "author": "钱社会", "summary": "我国高等教育毛入学率突破65%，正式迈入高等教育普及化阶段。", "publish_time": "2025-02-08 08:30:00"},
    {"id": 11, "cat_id": 2, "title": "跨省异地就医直接结算覆盖全部三甲医院", "author": "赵社会", "summary": "跨省异地就医直接结算已覆盖全国所有三甲医院，惠及数亿参保人员。", "publish_time": "2025-02-10 11:00:00"},
    {"id": 12, "cat_id": 2, "title": "全国碳市场交易额突破百亿，减排成效显著", "author": "钱社会", "summary": "全国碳排放权交易市场累计交易额突破百亿元，推动企业减排效果显著。", "publish_time": "2025-02-12 15:00:00"},
    {"id": 13, "cat_id": 3, "title": "中国男足晋级世界杯亚洲区决赛圈", "author": "孙体育", "summary": "中国国家男子足球队在世界杯亚洲区预选赛中成功晋级决赛圈。", "publish_time": "2025-03-01 18:00:00"},
    {"id": 14, "cat_id": 3, "title": "2025年世界田径锦标赛中国代表团斩获5金", "author": "周体育", "summary": "在2025年世界田径锦标赛上，中国代表团表现出色，共斩获5枚金牌。", "publish_time": "2025-03-03 20:00:00"},
    {"id": 15, "cat_id": 3, "title": "NBA全明星赛收视率创历史新高", "author": "孙体育", "summary": "2025年NBA全明星赛在全球范围内收视率创下历史新高。", "publish_time": "2025-03-05 10:00:00"},
    {"id": 16, "cat_id": 3, "title": "冬奥会筹备工作有序推进，场馆全部竣工", "author": "周体育", "summary": "下一届冬奥会各项筹备工作有序推进，所有比赛场馆已全部竣工。", "publish_time": "2025-03-08 09:00:00"},
    {"id": 17, "cat_id": 3, "title": "中超联赛引入VAR2.0系统，判罚准确率提升", "author": "孙体育", "summary": "中超联赛全面引入VAR2.0智能辅助裁判系统，判罚准确率显著提升。", "publish_time": "2025-03-10 14:00:00"},
    {"id": 18, "cat_id": 3, "title": "电子竞技正式列入亚运会正式比赛项目", "author": "周体育", "summary": "电子竞技被正式列入下一届亚运会正式比赛项目，设6个小项。", "publish_time": "2025-03-12 16:00:00"},
    {"id": 19, "cat_id": 4, "title": "国产科幻电影票房突破60亿创历史纪录", "author": "吴娱乐", "summary": "国产科幻电影春节档票房突破60亿元，刷新了中国电影票房历史纪录。", "publish_time": "2025-04-01 08:00:00"},
    {"id": 20, "cat_id": 4, "title": "知名歌手全球巡演启动，首站北京一票难求", "author": "郑娱乐", "summary": "华语乐坛知名歌手宣布启动全球巡回演唱会，首站北京站门票秒售罄。", "publish_time": "2025-04-03 10:00:00"},
    {"id": 21, "cat_id": 4, "title": "爆款综艺节目第三季回归，全新赛制引期待", "author": "吴娱乐", "summary": "热门综艺节目第三季正式官宣回归，全新赛制引发观众期待。", "publish_time": "2025-04-05 12:00:00"},
    {"id": 22, "cat_id": 4, "title": "国产动画电影入围国际电影节主竞赛单元", "author": "郑娱乐", "summary": "一部国产动画电影成功入围国际A类电影节主竞赛单元，实现历史性突破。", "publish_time": "2025-04-08 14:00:00"},
    {"id": 23, "cat_id": 4, "title": "数字音乐产业规模突破千亿，流媒体成主流", "author": "吴娱乐", "summary": "中国数字音乐产业规模突破千亿元大关，流媒体音乐已成为消费主流。", "publish_time": "2025-04-10 09:00:00"},
    {"id": 24, "cat_id": 4, "title": "沉浸式戏剧新形式走红，观众参与感拉满", "author": "郑娱乐", "summary": "沉浸式互动戏剧新形式在年轻观众中迅速走红，场场爆满一票难求。", "publish_time": "2025-04-12 16:00:00"},
]

CAT_MAP = {c["id"]: c for c in CATEGORIES}
NEWS_MAP = {n["id"]: n for n in NEWS_LIST}


def render_detail_content(news_id, news):
    cat_name = CAT_MAP[news["cat_id"]]["name"]
    body = f"这是关于「{news['title']}」的完整报道。{news['summary']}这一事件在社会各界引起广泛关注，专家表示这将对该领域产生深远影响。"
    body += "相关部门已就此展开深入研究和部署，预计将在未来几个月内推出具体措施。社会各界对此寄予厚望，认为这将推动行业健康有序发展。"
    body += f"业内分析师指出，{cat_name}领域正在经历前所未有的变革，相关企业和机构需要积极应对，抓住发展机遇。"
    return body


@app.get("/", response_class=HTMLResponse)
def index():
    return """
    <html><body>
    <h1>欢迎来到新闻网站</h1>
    <p>这是一个3层级的新闻网站，请选择您感兴趣的新闻分类：</p>
    <ul>
        <li><a href="/categories">浏览所有分类</a></li>
    </ul>
    </body></html>
    """


@app.get("/categories", response_class=HTMLResponse)
def categories():
    items = ""
    for cat in CATEGORIES:
        items += f'<li><a href="/category/{cat["id"]}/news?page=1">{cat["name"]}</a> - {cat["desc"]}</li>'
    return f"""
    <html><body>
    <h1>新闻分类</h1>
    <ul>{items}</ul>
    <p><a href="/">返回首页</a></p>
    </body></html>
    """


@app.get("/category/{cat_id}/news", response_class=HTMLResponse)
def category_news(cat_id: int, page: int = Query(1, ge=1), page_size: int = Query(4, ge=1, le=20)):
    cat = CAT_MAP.get(cat_id)
    if not cat:
        return HTMLResponse("<h1>分类不存在</h1>", status_code=404)

    cat_news = [n for n in NEWS_LIST if n["cat_id"] == cat_id]
    total_pages = (len(cat_news) + page_size - 1) // page_size
    start = (page - 1) * page_size
    end = start + page_size
    items = cat_news[start:end]

    rows = ""
    for item in items:
        rows += f"""
        <tr>
            <td>{item['id']}</td>
            <td><a href="/news/{item['id']}">{item['title']}</a></td>
            <td>{item['author']}</td>
            <td>{item['publish_time']}</td>
        </tr>"""

    nav = ""
    if page > 1:
        nav += f'<a class="prev-page" href="/category/{cat_id}/news?page={page - 1}&page_size={page_size}">上一页</a> '
    if page < total_pages:
        nav += f'<a class="next-page" href="/category/{cat_id}/news?page={page + 1}&page_size={page_size}">下一页</a>'

    return f"""
    <html><body>
    <h1>{cat['name']}新闻 - 第{page}页/共{total_pages}页</h1>
    <table border="1" cellpadding="5">
        <tr><th>ID</th><th>标题</th><th>作者</th><th>发布时间</th></tr>
        {rows}
    </table>
    <p>{nav}</p>
    <p><a href="/categories">返回分类列表</a></p>
    </body></html>
    """


@app.get("/news/{news_id}", response_class=HTMLResponse)
def news_detail(news_id: int):
    news = NEWS_MAP.get(news_id)
    if not news:
        return HTMLResponse("<h1>404 新闻不存在</h1>", status_code=404)

    content = render_detail_content(news_id, news)
    cat_name = CAT_MAP[news["cat_id"]]["name"]

    return f"""
    <html><body>
    <h1>{news['title']}</h1>
    <div class="content">
        <p><strong>作者：</strong>{news['author']}</p>
        <p><strong>分类：</strong>{cat_name}</p>
        <p><strong>发布时间：</strong>{news['publish_time']}</p>
        <hr>
        <p>{news['summary']}</p>
        <p>{content}</p>
    </div>
    <p><a href="/category/{news['cat_id']}/news?page=1">返回列表</a></p>
    <p><a href="/categories">返回分类列表</a></p>
    </body></html>
    """


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8765)
