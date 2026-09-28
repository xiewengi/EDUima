#!/usr/bin/env python3
"""
政策数据补全（全流程）：
  1. 列表页翻页匹配 URL（教育部/教育厅）
  2. 必应兜底：列表页没找到的 → site:xxx 标题搜索
  3. 有 URL 后 → 抓文号 + 日期
  4. 缓存到 policy_cache.json，每次跑 8 条

同步流程里自动调用，每天凌晨 3 点 daemon 触发
"""
import json, re, urllib.parse, requests, time, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POLICY_JSON = ROOT / 'public/data/policy.json'
CACHE_FILE = ROOT / '.sync_tmp/policy_cache.json'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36',
    'Accept-Language': 'zh-CN,zh;q=0.9',
}

MAX_PER_RUN = 8

# ========== 列表页翻页 ==========
def fetch_moe_list():
    """教育部政策公开列表：翻 10 页"""
    items = []
    seen = set()
    for page in range(10):
        suffix = '' if page == 0 else f'_{page}'
        url = f'http://www.moe.gov.cn/jyb_xxgk/zywj_btlj/index{suffix}.html'
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            if r.status_code != 200: break
            r.encoding = r.apparent_encoding or 'utf-8'
            text = r.text
        except: break
        
        count = 0
        for m in re.finditer(r'<a[^>]+href="([^"]*t\d+_\d+\.html[^"]*)"[^>]*>([^<]{10,150})</a>', text):
            href, title = m.group(1), m.group(2).strip()
            full = href if href.startswith('http') else 'http://www.moe.gov.cn' + href.lstrip('/')
            if full in seen: continue
            seen.add(full)
            items.append({'url': full, 'title': re.sub(r'\s+', ' ', title)})
            count += 1
        if count == 0 and page > 0: break
    return items

def fetch_gd_list():
    """广东教育厅政策列表：前端渲染，需要额外处理。
    先用已有浏览器缓存的 40 条，不够再返回空。"""
    cache_key = ROOT / '.sync_tmp/gd_browser_list.json'
    try:
        return json.loads(cache_key.read_text())
    except:
        return []

# ========== 标题匹配 ==========
def title_match(item_title, candidates):
    """严格匹配：去掉书名号后互相包含"""
    plain = re.sub(r'[《》""\'\']', '', item_title).strip()
    for c in candidates:
        c_plain = re.sub(r'[《》""\'\']', '', c['title']).strip()
        if plain == c_plain: return c['url']
        if plain in c_plain or c_plain in plain: return c['url']
    # 后 30 字兜底（长标题前面多了部门名没关系）
    item_tail = plain[-30:] if len(plain) > 30 else plain
    for c in candidates:
        c_plain = re.sub(r'[《》""\'\']', '', c['title']).strip()
        c_tail = c_plain[-30:] if len(c_plain) > 30 else c_plain
        if item_tail == c_tail: return c['url']
    return None

# ========== 必应搜索兜底 ==========
def bing_search(title, site):
    """必应站内搜索，找目标站点第一个结果"""
    q = f'site:{site} "{title}"'
    url = f'https://www.bing.com/search?q={urllib.parse.quote(q)}'
    try:
        r = requests.get(url, headers={**HEADERS, 'Referer': 'https://www.bing.com/'}, timeout=12)
        if r.status_code != 200: return None
        links = re.findall(r'href="(https?://[^"]+)"', r.text)
        seen = set()
        for l in links:
            if 'bing.com' in l or 'baidu' in l or 'zhihu' in l or 'google' in l: continue
            if l in seen: continue
            seen.add(l)
            if site in l: return l
        return None
    except: return None

# ========== 文号 + 日期 ==========
def extract_date_from_url(url):
    m = re.search(r'(20\d{2})(\d{2})/t?(20\d{2})(\d{2})(\d{2})', url)
    if m: return f'{m.group(3)}-{m.group(4)}-{m.group(5)}'
    m = re.search(r'(20\d{2})/(\d{1,2})/(\d{1,2})', url)
    if m: return f'{m.group(1)}-{m.group(2).zfill(2)}-{m.group(3).zfill(2)}'
    return None

def fetch_doc_and_date(url):
    result = {'doc_no': None, 'date': None}
    
    try:
        r = requests.get(url, headers=HEADERS, timeout=15, allow_redirects=True)
        if r.status_code != 200: return result
        r.encoding = r.apparent_encoding or 'utf-8'
        html = r.text
    except: return result
    
    # ====== 日期提取（按优先级） ======
    # 1. meta PubDate（广东政府网站）
    m = re.search(r'<meta[^>]+name=["\']PubDate["\'][^>]+content=["\']?(\d{4}[-/]\d{1,2}[-/]\d{1,2})', html, re.I)
    if m:
        d = m.group(1).replace('/', '-')
        result['date'] = f'{d.split("-")[0]}-{d.split("-")[1].zfill(2)}-{d.split("-")[2].zfill(2)}'
    
    # 2. URL 里的日期
    if not result['date']:
        m = re.search(r't(\d{4})(\d{2})(\d{2})_', url)
        if m: result['date'] = f'{m.group(1)}-{m.group(2)}-{m.group(3)}'
    if not result['date']:
        m = re.search(r'content/\d+/\d+/post_(\d{8})', url)
        if m:
            d = m.group(1)
            result['date'] = f'{d[:4]}-{d[4:6]}-{d[6:8]}'
    
    # 3. body 文本：发布日期/成文日期
    clean = re.sub(r'<script[^>]*>.*?</script>', '', html[:50000], flags=re.DOTALL)
    clean = re.sub(r'<style[^>]*>.*?</style>', '', clean, flags=re.DOTALL)
    clean = re.sub(r'<!--.*?-->', '', clean, flags=re.DOTALL)
    clean = re.sub(r'<[^>]+>', ' ', clean)
    clean = re.sub(r'\s+', ' ', clean)
    
    if not result['date']:
        for pat in [
            r'(?:发布日期|成文日期|印发日期|发文日期|签发日期)[^\d]{0,10}(\d{4})\s*[-年/.]\s*(\d{1,2})\s*[-月/.]\s*(\d{1,2})',
            r'(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日',
        ]:
            m = re.search(pat, clean[:3000])
            if m:
                result['date'] = f'{m.group(1)}-{m.group(2).zfill(2)}-{m.group(3).zfill(2)}'
                break
    
    # ====== 文号 ======
    # 只接受 2024-2026 年，避免侧边栏旧政策干扰
    pats = [
        # 5 groups: prefix, kind, bracket, year, num
        r'([\u4e00-\u9fff]{1,10})(函|字|规|令|发|教|委)([〔(（]\s*(202[4-6])\s*[)）〕])\s*(\d+)\s*号',
        # 4 groups: prefix, bracket, year, num
        r'([粤][\u4e00-\u9fff]{0,6}(?:厅|委|局|办)?[\u4e00-\u9fff]{0,6}?)\s*([〔(（]\s*(202[4-6])\s*[)）〕])\s*(\d+)\s*号',
    ]
    candidates = []
    for pat in pats:
        for m in re.finditer(pat, clean[:30000]):
            g = m.groups()
            if len(g) == 5:
                doc = re.sub(r'\s+', '', f'{g[0].strip()}{g[1]}{g[2]}{g[4]}号')
            else:
                doc = re.sub(r'\s+', '', f'{g[0].strip()}{g[1]}{g[3]}号')
            if 8 <= len(doc) <= 30:
                candidates.append((m.start(), doc))
    if candidates:
        candidates.sort(key=lambda x: x[0])
        result['doc_no'] = candidates[0][1]
        result['doc_no'] = re.sub(r'^.*?[：:]\s*', '', result['doc_no'])
    
    return result

# ========== 主流程 ==========
def load_cache():
    try: return json.loads(CACHE_FILE.read_text())
    except: return {}

def save_cache(c):
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(json.dumps(c, ensure_ascii=False, indent=2))

def main():
    policy = json.loads(POLICY_JSON.read_text())
    cache = load_cache()
    ran = 0
    new_url = 0
    new_doc = 0
    new_dt = 0
    
    # 1. 拉列表
    print('  📋 拉教育部列表...')
    moe_list = fetch_moe_list()
    print(f'    → {len(moe_list)} 条')
    print('  📋 拉广东教育厅列表...')
    gd_list = fetch_gd_list()
    print(f'    → {len(gd_list)} 条（浏览器缓存）')
    
    for cat in policy['categories']:
        is_gd = cat['id'] == 'guangdong'
        site = 'edu.gd.gov.cn' if is_gd else 'moe.gov.cn'
        candidates = gd_list if is_gd else moe_list
        
        for item in cat['items']:
            if ran >= MAX_PER_RUN: break
            mid = item.get('mediaId') or item.get('title', '')[:40]
            cached = cache.get(mid)
            
            # 已有 URL → 直接抓文号日期
            url = item.get('url', '')
            if not url.startswith('http'):
                url = (cached or {}).get('url', '')
            
            # 没 URL → 尝试找
            if not url.startswith('http'):
                # 先列表页匹配
                url = title_match(item['title'], candidates)
                if url:
                    item['url'] = url
                    cache[mid] = cache.get(mid, {})
                    cache[mid]['url'] = url
                    save_cache(cache)
                    new_url += 1
                    print(f'  🔗 列表匹配: {item["title"][:35]}')
                
                # 再必应兜底
                if not url.startswith('http') and not (cached or {}).get('bing_tried'):
                    if ran >= MAX_PER_RUN: break
                    ran += 1
                    title_plain = re.sub(r'[《》""\'\']', '', item['title']).strip()
                    print(f'  🔍 必应搜: {title_plain[:40]}')
                    burl = bing_search(title_plain, site)
                    if burl:
                        item['url'] = burl
                        url = burl
                        cache[mid] = cache.get(mid, {})
                        cache[mid]['url'] = burl
                        new_url += 1
                        print(f'    ✅ {burl[:70]}')
                    else:
                        cache[mid] = cache.get(mid, {})
                        cache[mid]['bing_tried'] = True
                        print(f'    ❌ 没找到')
                    save_cache(cache)
                    time.sleep(2)
            
            # 有 URL → 抓文号日期
            if url.startswith('http'):
                url = item.get('url') or url
                need_no = not item.get('doc_no')
                need_dt = not item.get('date')
                
                # 缓存查一下
                if cached:
                    if cached.get('doc_no') and not item.get('doc_no'): item['doc_no'] = cached['doc_no']
                    if cached.get('date') and not item.get('date'): item['date'] = cached['date']
                    need_no = not item.get('doc_no')
                    need_dt = not item.get('date')
                
                if not (need_no or need_dt): continue
                
                if ran >= MAX_PER_RUN: break
                ran += 1
                print(f'  📥 抓 {"文号" if need_no else ""}{"日期" if need_dt else ""}: {item["title"][:35]}')
                info = fetch_doc_and_date(url)
                if info['doc_no'] and not item.get('doc_no'):
                    item['doc_no'] = info['doc_no']
                    new_doc += 1
                    print(f'    ✅ {info["doc_no"]}')
                if info['date'] and not item.get('date'):
                    item['date'] = info['date']
                    new_dt += 1
                    print(f'    ✅ {info["date"]}')
                cache[mid] = {'url': url, 'doc_no': item.get('doc_no',''), 'date': item.get('date',''), 'tried': True}
                save_cache(cache)
                time.sleep(1)
    
    POLICY_JSON.write_text(json.dumps(policy, ensure_ascii=False, indent=2))
    
    gd = policy['categories'][0]['items']
    nat = policy['categories'][1]['items']
    gd_u = sum(1 for x in gd if x.get('url','').startswith('http'))
    gd_n = sum(1 for x in gd if x.get('doc_no'))
    gd_d = sum(1 for x in gd if x.get('date'))
    nat_u = sum(1 for x in nat if x.get('url','').startswith('http'))
    nat_n = sum(1 for x in nat if x.get('doc_no'))
    nat_d = sum(1 for x in nat if x.get('date'))
    print(f'\n  enrich: +{new_url} URL  +{new_doc} 文号  +{new_dt} 日期  (本轮 {ran} 条)')
    print(f'  广东: {gd_u}/20 URL | {gd_n}/20 文号 | {gd_d}/20 日期')
    print(f'  全国: {nat_u}/21 URL | {nat_n}/21 文号 | {nat_d}/21 日期')

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f'  enrich err: {e}', file=sys.stderr)
        sys.exit(0)
