#!/usr/bin/env python3
"""智库观察数据抓取：权威教育网站的智库报告/观察视角/行业趋势 → public/data/thinktank.json

数据源（权威站点，直连抓取，失败自动跳过不阻断）：
  edu.cn / cernet.edu.cn（中国教育和科研计算机网 CERNET，教育信息化领域权威媒体）——
  首页 + 教育信息化资讯 + 理论研讨（专家专栏）做文章池，关键词过滤出
  教育信息化前沿报告 / 行业趋势 / 观察视角类文章；不足 12 条用最新资讯回填。

每篇文章抓详情页抽 description 摘要 + 正文图（过滤 logo/广告图）。
产物字段：{updatedAt, items:[{id,title,url,image,summary,date,source}]}，最多保留 24 条。
"""
import json
import os
import re
import socket
import urllib.request
from datetime import datetime, timezone, timedelta
from urllib.parse import urljoin

OUT_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        'public', 'data', 'thinktank.json')
UA = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/120.0 Safari/537.36')
TIMEOUT = 15
MAX_ITEMS = 12   # 老大拍板：12 条就够
MAX_ARTICLES = 24  # 最多抓多少篇文章详情（多抓些提高有图率，减少占位图）

# 智库报告/行业观察相关关键词（标题过滤用）
KEYWORDS = ('人工智能', 'AI', '智能体', '信息化', '数字化', '数智', '智慧',
            '趋势', '报告', '观察', '洞察', '前沿', '研究', '治理', '转型',
            '大数据', '网络安全', 'IPv6', '平台', '大模型', '云计算')
# 标题黑名单（明显无关的时政/招生类）
BLOCKWORDS = ('招生', '招聘', '放假', '运动会', '录取', '成绩查询', '考试时间',
              '冠军', '颁奖典礼', '来华培训', '起源之谜', '收费管理办法', '榜样',
              '启动仪式', '展演', '比赛')

CERNET_LISTS = (
    'https://www.edu.cn/',
    'https://www.cernet.edu.cn/info/',
    'https://www.cernet.edu.cn/info/focus/li_lun_yj/',
)

# 直连（本机环境代理会劫持教育类站点，参照 gdgpo 链路约定显式禁代理）。
# caigou.com.cn 证书已过期（2026-10 实测），对其跳过证书校验。
import ssl
_CTX_INSECURE = ssl._create_unverified_context()
OPENER = urllib.request.build_opener(
    urllib.request.ProxyHandler({}),
    urllib.request.HTTPSHandler(context=_CTX_INSECURE),
)
OPENER.addheaders = [('User-Agent', UA)]
socket.setdefaulttimeout(TIMEOUT)


def fetch(url, retries=2):
    last = None
    for _ in range(retries + 1):
        try:
            with OPENER.open(url) as resp:
                return resp.read().decode('utf-8', errors='replace')
        except Exception as e:  # noqa: BLE001
            last = e
    print(f'  ⚠️ fetch fail: {url[:80]} → {last}')
    return ''


def text_of(html):
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', html)).strip()


def date_from_jyb_url(url):
    m = re.search(r'/(\d{6})/t(\d{8})_', url)
    if m:
        d = m.group(2)
        return f'{d[:4]}-{d[4:6]}-{d[6:]}'
    # caigou: /news/202508133.shtml → YYYYMMDD 前缀（2025-08-13 期号）
    m = re.search(r'/news/(\d{4})(\d{2})(\d{2})\d+\.shtml', url)
    if m:
        return f'{m.group(1)}-{m.group(2)}-{m.group(3)}'
    return ''


_JYB_POOL_CACHE = []  # collect_jyb_articles() 顺带缓存全量文章池，供 main() 回填


def article_id(url):
    """edu.cn 同一篇文章会在多个频道各挂一个 URL（路径不同、t日期_编号 相同），
    URL 去重拦不住，必须按文章 ID 去重（2026-10-14 老大反馈「新型研究型大学」重复展示，踩）"""
    m = re.search(r't\d{8}_(\d+)\.s?html', url)
    return m.group(1) if m else ''


def collect_jyb_articles():
    """edu.cn 首页 + 信息化资讯 + 理论研讨列表 → [(title, url, date)]，标题关键词过滤"""
    pool, seen, seen_ids = [], set(), set()
    for list_url in CERNET_LISTS:
        html = fetch(list_url)
        if not html:
            continue
        for m in re.finditer(r'<a[^>]+href="([^"]*202[5-6]\d{2}/t\d{8}_\d+\.shtml)"[^>]*>([^<]{6,80})</a>', html):
            url = urljoin(list_url, m.group(1))
            title = text_of(m.group(2))
            aid = article_id(url)
            if url in seen or (aid and aid in seen_ids) or not title:
                continue
            seen.add(url)
            if aid:
                seen_ids.add(aid)
            pool.append({'title': title, 'url': url, 'date': date_from_jyb_url(url)})
    _JYB_POOL_CACHE.extend(pool)
    print(f'CERNET 文章池：{len(pool)} 条（过滤前）')
    hit = [a for a in pool
           if any(k in a['title'] for k in KEYWORDS)
           and not any(b in a['title'] for b in BLOCKWORDS)]
    print(f'CERNET 关键词命中：{len(hit)} 条')
    # 按日期倒序（日期取自 URL，可靠）
    hit.sort(key=lambda a: a['date'], reverse=True)
    return hit



IMG_BLOCK = re.compile(r'logo|icon|Ad/|banner|avatar|user\.png|qrcode|share|gongan|beian', re.I)


def enrich_article(article):
    """抓文章详情：description 摘要 + 正文图（过滤 logo/广告）。
    www.edu.cn 对脚本请求经常读超时，改抓其 302 目标镜像 www.cernet.edu.cn（内容一致）。"""
    html = fetch(article['url'].replace('://www.edu.cn/', '://www.cernet.edu.cn/'), retries=1)
    if not html:
        return
    m = re.search(r'<meta[^>]+name="description"[^>]+content="([^"]{10,300})"', html)
    if m:
        article['summary'] = text_of(m.group(1))[:160]
    else:
        # 兜底：正文第一个有内容的段落（30 字以上）
        for mp in re.finditer(r'<p[^>]*>(.*?)</p>', html, re.S):
            para = text_of(mp.group(1))
            if len(para) >= 30:
                article['summary'] = para[:160]
                break
    # 图片：优先 og:image（必须是真实图片 URL——cernet 详情页 og:image 常是站点空值 'https://www.edu.cn'），
    # 其次正文内容图，过滤 logo/广告/公共徽章
    img = ''
    mog = re.search(r'<meta[^>]+property="og:image"[^>]+content="([^"]+\.(?:jpg|jpeg|png)[^"]*)"', html)
    if mog and not IMG_BLOCK.search(mog.group(1)):
        img = urljoin(article['url'], mog.group(1))
    if not img:
        candidates = []
        for mi in re.finditer(r'<img[^>]+src="([^"]+\.(?:jpg|jpeg|png))"', html):
            cand = urljoin(article['url'], mi.group(1))
            if IMG_BLOCK.search(cand):
                continue
            candidates.append(cand)
        # W0 内容图优先（jyb/TRS 正文配图的命名特征）
        content_imgs = [c for c in candidates if re.search(r'/W0\d+', c)]
        img = (content_imgs or candidates or [''])[0]
    article['image'] = img


def main():
    print(f'== 智库观察抓取 {datetime.now().isoformat(timespec="seconds")} ==')
    jyb_hit = collect_jyb_articles()
    jyb_hit_urls = {a['url'] for a in jyb_hit}

    # 关键词命中不足 12 条时，用 jyb 最新资讯回填（仍排除黑名单标题）
    articles = jyb_hit
    if len(articles) < MAX_ITEMS:
        pool_html_extra = _JYB_POOL_CACHE  # 上次抓的文章池（含未命中关键词的）
        backfill = [a for a in pool_html_extra
                    if a['url'] not in jyb_hit_urls
                    and not any(b in a['title'] for b in BLOCKWORDS)]
        backfill.sort(key=lambda a: a['date'], reverse=True)
        need = MAX_ITEMS - len(articles)
        articles += backfill[:need]
        print(f'回填 CERNET 最新资讯 {min(need, len(backfill))} 条')

    # 详情 enrich（限制请求量）
    for a in articles[:MAX_ARTICLES]:
        a.setdefault('summary', '')
        a.setdefault('image', '')
        enrich_article(a)
        print(f"  ✓ {a['title'][:40]} img={'Y' if a.get('image') else 'N'}")

    # 有图有摘优先（bool() 兜住未 enrich 条目的 None：None != '' 恒为 True 会导致未抓详情的条目反排最前）
    articles.sort(key=lambda a: (bool(a.get('image')), bool(a.get('summary')), a.get('date') or ''),
                  reverse=True)
    items, seen, seen_ids, used_imgs = [], set(), set(), set()
    for a in articles:
        aid = article_id(a['url'])
        if a['url'] in seen or (aid and aid in seen_ids):
            continue
        seen.add(a['url'])
        if aid:
            seen_ids.add(aid)
        img = a.get('image') or ''
        # 全局图片去重（keep-first）：同一图 URL 只保留排位最前的一条，其余置空走前端占位——
        # 旧口径「3+ 条才置空」会放过 2 条重复（2026-10-14 老大反馈两页图片重复，踩）
        if img and img in used_imgs:
            img = ''
        if img:
            used_imgs.add(img)
        items.append({
            'id': re.sub(r'[^A-Za-z0-9]', '', a['url'])[-40:] or str(len(items)),
            'title': a['title'],
            'url': a['url'],
            'image': img,
            'summary': a.get('summary') or '',
            'date': a.get('date') or '',
            'source': '中国教育和科研计算机网',
        })
        if len(items) >= MAX_ITEMS:
            break

    now = datetime.now(timezone(timedelta(hours=8))).isoformat(timespec='seconds')
    data = {'updatedAt': now, 'total': len(items), 'items': items}
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    with_img = sum(1 for i in items if i['image'])
    with_sum = sum(1 for i in items if i['summary'])
    print(f'== 写出 {OUT_PATH}：{len(items)} 条（图 {with_img} / 摘要 {with_sum}）==')
    if not items:
        raise SystemExit(1)  # 全空视为失败，让调用方知道


if __name__ == '__main__':
    main()
