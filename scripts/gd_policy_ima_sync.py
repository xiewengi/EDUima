#!/usr/bin/env python3
"""
政策自动采集上传 → IMA 知识库

数据源:
  1. 广东教育厅政策公开 API (edu.gd.gov.cn/gkmlpt/api/all/1620)
  2. 教育部最新文件列表 (moe.gov.cn/jyb_xxgk/zywj_btlj/)

流程:
  Step 1: 从 IMA 拉已有政策文件列表 → 构建去重集合 (按标题)
  Step 2: 爬广东教育厅 API → 找 PDF/Word 附件下载
  Step 3: 爬教育部列表 → 详情页没附件就保存 HTML
  Step 4: 过滤 N 天内新政策 + 去重 → 上传 IMA

IMA 目标位置:
  广东省政策 → KB folder_7508334957560424
  全国政策   → KB folder_7508334924008816

用法:
  python3 gd_policy_ima_sync.py                    # 默认: 最近 5 天 + 5 页
  python3 gd_policy_ima_sync.py --days 3           # 最近 3 天
  python3 gd_policy_ima_sync.py --pages 3          # 每个源只爬 3 页
  python3 gd_policy_ima_sync.py --dry-run         # 只采集 + 不去重 + 不上传
  python3 gd_policy_ima_sync.py --gd-only          # 只爬广东教育厅
  python3 gd_policy_ima_sync.py --moe-only         # 只爬教育部
  python3 gd_policy_ima_sync.py --all              # 所有分页 (广东教育厅全量 2 页, 教育部 20 页)
"""

import json, os, sys, re, time, argparse, subprocess, logging, hashlib, urllib.request
from datetime import datetime, timedelta
from pathlib import Path

# ========== 配置 ==========
SKILL_DIR = os.environ.get('IMA_SKILL_DIR', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ima-skill'))
CLIENT_ID = os.environ.get('IMA_CLIENT_ID', open(os.path.expanduser('~/.config/ima/client_id')).read().strip())
API_KEY = os.environ.get('IMA_API_KEY', open(os.path.expanduser('~/.config/ima/api_key')).read().strip())
OPTS = json.dumps({"clientId": CLIENT_ID, "apiKey": API_KEY})

KB_ID = "o9q3d7B3xA1WPfSaOLqGrp-EeJ9kTXGTWM0kqf9S274="   # 教育平台
FOLDER_GD  = "folder_7508334957560424"                      # 广东省内政策
FOLDER_MOE = "folder_7508334924008816"                      # 全国通用政策

WORK_DIR = '/tmp/ima_policy_sync'
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36',
    'Accept-Language': 'zh-CN,zh;q=0.9',
}

# ========== 日志 ==========
os.makedirs(LOG_DIR, exist_ok=True)
log_file = os.path.join(LOG_DIR, f'policy_{datetime.now().strftime("%Y%m%d")}.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler(sys.stdout),
    ]
)
log = logging


# ========== IMA API 工具 ==========
def ima_api(path, body):
    proc = subprocess.run(
        ['node', f'{SKILL_DIR}/ima_api.cjs', path, json.dumps(body, ensure_ascii=False), OPTS],
        capture_output=True, text=True, timeout=30
    )
    if proc.returncode != 0:
        log.error(f"IMA API错误 {path}: {proc.stderr.strip()[:200]}")
        return None
    try:
        resp = json.loads(proc.stdout.strip())
        if resp.get('code') != 0:
            log.error(f"IMA API业务错误 {path}: {resp.get('msg','unknown')[:200]}")
        return resp
    except Exception as e:
        log.error(f"IMA API JSON解析失败: {e}")
        return None


def preflight_check(file_path):
    proc = subprocess.run(
        ['node', f'{SKILL_DIR}/knowledge-base/scripts/preflight-check.cjs', '--file', file_path],
        capture_output=True, text=True, timeout=30
    )
    return json.loads(proc.stdout.strip())


def cos_upload(file_path, cos_credential, content_type, max_retries=3):
    cred = cos_credential
    args = [
        'node', f'{SKILL_DIR}/knowledge-base/scripts/cos-upload.cjs',
        '--file', file_path,
        '--secret-id', cred['secret_id'],
        '--secret-key', cred['secret_key'],
        '--token', cred['token'],
        '--bucket', cred['bucket_name'],
        '--region', cred['region'],
        '--cos-key', cred['cos_key'],
        '--content-type', content_type,
        '--start-time', cred['start_time'],
        '--expired-time', cred['expired_time'],
        '--timeout', '300000',
    ]
    for attempt in range(1, max_retries + 1):
        proc = subprocess.run(args, capture_output=True, text=True, timeout=360)
        if proc.returncode == 0:
            return True
        err = (proc.stderr or proc.stdout or '').strip()
        if attempt < max_retries:
            log.warning(f"  COS重试 {attempt}: {err[:100]}")
            time.sleep(5)
        else:
            log.error(f"  COS上传失败: {err[:100]}")
    return False


def fetch_ima_existing_titles(folder_id):
    """拉 IMA 文件夹所有现有文件 → 标题集合 + media_id 集合 (用于去重)"""
    titles = set()
    media_ids = set()
    cursor = ''
    is_end = False
    while not is_end:
        r = ima_api('openapi/wiki/v1/get_knowledge_list', {
            'knowledge_base_id': KB_ID, 'folder_id': folder_id,
            'cursor': cursor, 'limit': 50
        })
        if not r or r.get('code') != 0:
            break
        items = r.get('data', {}).get('knowledge_list', [])
        for x in items:
            t = (x.get('title') or '').strip()
            if t:
                titles.add(t)
                # 清理标题: 去掉文件扩展名, 去掉尾部门户后缀
                clean = re.sub(r'\.(pdf|doc|docx|html?)$', '', t, flags=re.I)
                clean = re.sub(r'\s*[-—]\s*.*?(门户|官网|网站).*$', '', clean).strip()
                titles.add(clean)
            if x.get('media_id'):
                media_ids.add(x['media_id'])
        cursor = r['data'].get('next_cursor', '')
        is_end = r['data'].get('is_end', True)
        if not is_end:
            time.sleep(0.3)
    return titles, media_ids


# ========== 广东教育厅采集 ==========
GD_API = 'https://edu.gd.gov.cn/gkmlpt/api/all/1620'
GD_LIST_REFERER = 'https://edu.gd.gov.cn/gkmlpt/policy/'


def fetch_gd_policies(max_pages):
    """分页拉取广东教育厅政策 API"""
    all_articles = []
    page = 1
    while page <= max_pages:
        url = f'{GD_API}?page={page}&sid=168'
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': HEADERS['User-Agent'],
                'Referer': GD_LIST_REFERER,
            })
            with urllib.request.urlopen(req, timeout=15) as resp:
                d = json.loads(resp.read().decode('utf-8'))
        except Exception as e:
            log.error(f"广东教育厅 API 第{page}页失败: {e}")
            break

        articles = d.get('articles', [])
        if page == 1:
            total = d.get('total', 0)
            log.info(f"📋 广东教育厅政策 API: total={total}")
        log.info(f"  第{page}页: {len(articles)} 条 (offset={d.get('offset',0)})")
        all_articles.extend(articles)

        if not articles:
            break
        # 判断是否还有下一页
        offset = d.get('offset', 0) + len(articles)
        if offset >= d.get('total', 0):
            break
        page += 1
        time.sleep(0.3)
    return all_articles


def download_gd_policy(article, work_dir):
    """下载广东政策：优先 PDF/Word 附件，否则下载详情页 HTML"""
    atts = article.get('attachment') or []
    title = article.get('title', '').strip()
    url = article.get('url', '')

    # 优先找 PDF，其次 Word 附件
    chosen = None
    for a in atts:
        t = (a.get('type') or '').lower()
        n = (a.get('name') or '').lower()
        if t == 'pdf' or n.endswith('.pdf'):
            chosen = a
            break
    if not chosen:
        for a in atts:
            t = (a.get('type') or '').lower()
            n = (a.get('name') or '').lower()
            if t in ('doc', 'docx') or n.endswith('.doc') or n.endswith('.docx'):
                chosen = a
                break

    safe_title = re.sub(r'[\\/:*?"<>|\n\r\t]', '_', title)[:80]

    if chosen:
        # 有附件 → 下载附件
        att_url = chosen.get('url', '')
        att_name = chosen.get('name') or f"{title[:30]}.pdf"
        safe_name = re.sub(r'[\\/:*?"<>|\n\r\t]', '_', att_name)[:120]
        out_path = os.path.join(work_dir, f"gd_{article['id']}_{safe_name}")
        try:
            req = urllib.request.Request(att_url, headers={
                'User-Agent': HEADERS['User-Agent'],
                'Referer': GD_LIST_REFERER,
            })
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = resp.read()
            if len(data) > 500:
                with open(out_path, 'wb') as f:
                    f.write(data)
                return out_path
        except Exception as e:
            log.warning(f"  附件下载失败: {safe_name[:30]}: {e}")
            # fallback 下载详情页 HTML

    # 无附件 or 附件下载失败 → 下载详情页 HTML (政策正文在页面里)
    if not url:
        return None
    out_path = os.path.join(work_dir, f"gd_{article['id']}_{safe_title}.html")
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': HEADERS['User-Agent'],
            'Referer': GD_LIST_REFERER,
        })
        with urllib.request.urlopen(req, timeout=30) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
        if len(html) < 500:
            return None
        meta_info = f"<!-- 来源: {url} -->\n<!-- 标题: {title} -->\n<!-- 文号: {article.get('document_number','')} -->\n\n"
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(meta_info + html)
        return out_path
    except Exception as e:
        log.warning(f"  详情页下载失败: {safe_title[:30]}: {e}")
        return None


# ========== 教育部采集 ==========
def fetch_moe_list(max_pages):
    """翻页拉取教育部最新文件列表"""
    all_items = []
    seen_urls = set()
    for page in range(1, max_pages + 1):
        suffix = '' if page == 1 else f'_{page}'
        url = f'http://www.moe.gov.cn/jyb_xxgk/zywj_btlj/index{suffix}.html'
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=15) as resp:
                html = resp.read().decode('utf-8', errors='ignore')
        except Exception as e:
            log.error(f"教育部列表第{page}页失败: {e}")
            break

        # 正则匹配政策链接
        matches = re.findall(
            r'<a[^>]+href="([^"]*t\d+_\d+\.html[^"]*)"[^>]*>\s*<span[^>]*>([^<]+)</span>',
            html, re.DOTALL
        )
        if not matches:
            matches = re.findall(
                r'<a[^>]+href="([^"]*t\d+_\d+\.html[^"]*)"[^>]*>([^<]{10,150})</a>',
                html
            )

        page_items = []
        for href, title in matches:
            title = re.sub(r'\s+', ' ', title).strip()
            full = href if href.startswith('http') else 'http://www.moe.gov.cn' + href.lstrip('/')
            if full in seen_urls:
                continue
            seen_urls.add(full)
            # 从 URL 提取日期 t20260923_xxx
            m = re.search(r't(\d{4})(\d{2})(\d{2})_', full)
            date_str = f'{m.group(1)}-{m.group(2)}-{m.group(3)}' if m else ''
            page_items.append({'title': title, 'url': full, 'date': date_str, 'source': 'moe'})

        log.info(f"  教育部第{page}页: {len(page_items)} 条")
        all_items.extend(page_items)
        if len(page_items) == 0:
            break
        time.sleep(0.3)

    return all_items


def download_moe_policy(item, work_dir):
    """下载教育部政策详情页 → 优先附件 PDF/Word，否则保存为 .html"""
    title = item['title']
    url = item['url']
    safe_title = re.sub(r'[\\/:*?"<>|\n\r\t]', '_', title)[:80]

    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=30) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
    except Exception as e:
        log.warning(f"  教育部详情页下载失败: {safe_title[:30]}: {e}")
        return None

    # 先找 PDF/Word 附件
    att_matches = re.findall(
        r'<a[^>]+href="([^"]+\.(pdf|doc|docx)(?:\?[^"]*)?)"[^>]*>([^<]{3,100})</a>',
        html, re.IGNORECASE
    )
    if att_matches:
        href, ext, att_name = att_matches[0]
        full = href if href.startswith('http') else urllib.request.urljoin(url, href)
        try:
            req2 = urllib.request.Request(full, headers=HEADERS)
            with urllib.request.urlopen(req2, timeout=60) as resp:
                data = resp.read()
            if len(data) > 500:
                out_path = os.path.join(work_dir, f"moe_{safe_title}.{ext.lower()}")
                with open(out_path, 'wb') as f:
                    f.write(data)
                return out_path
        except Exception as e:
            log.warning(f"  附件下载失败: {att_name[:30]}: {e}")

    # 没附件 → 保存为 .html（政策正文就在页面里）
    out_path = os.path.join(work_dir, f"moe_{safe_title}.html")
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(f'<!-- 来源: {url} -->\n<!-- 标题: {title} -->\n\n{html}')
    return out_path


# ========== 过滤 ==========
def within_days(date_str, days):
    """判断日期是否在 N 天内"""
    if not date_str:
        return True  # 没日期的保守通过
    try:
        dt = datetime.strptime(date_str, '%Y-%m-%d')
        return (datetime.now() - dt).days <= days
    except:
        return True


def seconds_to_date(ts):
    try:
        return datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
    except:
        return ''


# ========== 主上传流程 ==========
def deduplicate_and_upload(file_records, folder_id, ima_existing_titles, dry_run=False):
    """
    file_records: [{path, title, date, source_url, source}]
    """
    # 过滤已存在
    new_records = []
    skip_exist = 0
    for r in file_records:
        clean_title = re.sub(r'\.(pdf|doc|docx|html?)$', '', r['title'], flags=re.I).strip()
        if r['title'] in ima_existing_titles or clean_title in ima_existing_titles:
            skip_exist += 1
            continue
        new_records.append(r)

    log.info(f"🔍 IMA 去重: {len(file_records)} → {len(new_records)} (跳过已存在 {skip_exist})")

    if dry_run:
        log.info(f"🧪 DRY-RUN: 以下 {len(new_records)} 个文件待上传, 跳过:")
        for r in new_records[:20]:
            log.info(f"  {r['date']} | {r['title'][:50]}")
        if len(new_records) > 20:
            log.info(f"  ... 还有 {len(new_records)-20} 个")
        return {"success": 0, "fail": 0, "skip_dedup": skip_exist}

    if not new_records:
        log.info("📭 没有新政策需要上传")
        return {"success": 0, "fail": 0, "skip_dedup": skip_exist}

    # preflight
    log.info(f"🔍 文件预检 ({len(new_records)} 个)...")
    pf_results = []
    for r in new_records:
        pf = preflight_check(r['path'])
        pf_results.append(pf)
        if not pf.get('pass'):
            log.warning(f"  preflight 失败: {os.path.basename(r['path'])}")

    # 重名检查
    batch_params = []
    valid_indices = []
    for i, pf in enumerate(pf_results):
        if pf.get('pass'):
            batch_params.append({"name": pf['file_name'], "media_type": pf['media_type']})
            valid_indices.append(i)

    rename_map = {}
    if batch_params:
        resp = ima_api("openapi/wiki/v1/check_repeated_names", {
            "params": batch_params,
            "knowledge_base_id": KB_ID,
            "folder_id": folder_id,
        })
        if resp and resp.get('code') == 0:
            results = resp.get('data', {}).get('results', [])
            ts = time.strftime("%Y%m%d%H%M%S")
            for i, r in enumerate(results):
                if r.get('is_repeated'):
                    vi = valid_indices[i]
                    pf = pf_results[vi]
                    name_base, ext = os.path.splitext(pf['file_name'])
                    new_name = f"{name_base}_{ts}{ext}"
                    orig = new_records[vi]['path']
                    dir_path = os.path.dirname(orig)
                    new_path = os.path.join(dir_path, new_name)
                    os.rename(orig, new_path)
                    new_records[vi]['path'] = new_path
                    rename_map[new_path] = new_name
                    log.info(f"  ⚠️ 重名改名: {pf['file_name'][:40]}... → ..._{ts}{ext}")

    # 逐个上传
    log.info(f"🚀 开始上传 {len(new_records)} 个政策文件...")
    success_count = 0
    fail_count = 0

    for idx, r in enumerate(new_records):
        pf = pf_results[idx]
        if not pf.get('pass'):
            fail_count += 1
            continue

        file_name = pf['file_name']
        file_ext = pf['file_ext']
        file_size = pf['file_size']
        media_type = pf['media_type']
        content_type = pf['content_type']
        final_name = rename_map.get(r['path'], file_name)

        # create_media
        resp = ima_api("openapi/wiki/v1/create_media", {
            "file_name": final_name,
            "file_size": file_size,
            "content_type": content_type,
            "knowledge_base_id": KB_ID,
            "file_ext": file_ext,
        })
        if not resp or resp.get('code') != 0:
            fail_count += 1
            continue

        data = resp['data']
        media_id = data['media_id']
        cos_cred = data['cos_credential']

        # COS 上传
        if not cos_upload(r['path'], cos_cred, content_type):
            log.error(f"  [{idx+1}/{len(new_records)}] COS失败: {final_name[:40]}")
            fail_count += 1
            continue

        # add_knowledge
        resp = ima_api("openapi/wiki/v1/add_knowledge", {
            "media_type": media_type,
            "media_id": media_id,
            "title": final_name,
            "knowledge_base_id": KB_ID,
            "folder_id": folder_id,
            "file_info": {
                "cos_key": cos_cred['cos_key'],
                "file_size": file_size,
                "file_name": final_name,
            }
        })

        if resp and resp.get('code') == 0:
            success_count += 1
            size_kb = file_size / 1024
            log.info(f"  [{idx+1}/{len(new_records)}] ✅ {final_name[:45]} ({size_kb:.0f}KB)")
        else:
            log.error(f"  [{idx+1}/{len(new_records)}] add_knowledge 失败: {final_name[:40]}")
            fail_count += 1

        time.sleep(0.3)

    log.info(f"📊 上传: ✅{success_count} ❌{fail_count}")
    return {"success": success_count, "fail": fail_count, "skip_dedup": skip_exist}


# ========== 主入口 ==========
def main():
    parser = argparse.ArgumentParser(description='政策自动采集上传 → IMA 知识库')
    parser.add_argument('--days', type=int, default=30, help='只处理最近 N 天的政策 (默认 30)')
    parser.add_argument('--pages', type=int, default=5, help='每个源爬多少页 (默认 5)')
    parser.add_argument('--dry-run', action='store_true', help='只采集+去重, 不上传')
    parser.add_argument('--gd-only', action='store_true', help='只爬广东教育厅')
    parser.add_argument('--moe-only', action='store_true', help='只爬教育部')
    parser.add_argument('--all', action='store_true', help='所有分页 (广东 2 页, 教育部 20 页)')
    args = parser.parse_args()

    max_pages = 20 if args.all else args.pages
    gd_pages = 2 if args.all else max_pages  # 广东总共才 2 页
    moe_pages = 20 if args.all else max_pages

    log.info(f"{'='*70}")
    log.info(f"🚀 政策自动采集 → IMA 知识库")
    log.info(f"   日期范围: 最近 {args.days} 天")
    log.info(f"   分页: 广东教育厅 {gd_pages} 页, 教育部 {moe_pages} 页")
    if args.dry_run:
        log.info(f"   🧪 DRY-RUN (不上传)")
    log.info(f"{'='*70}")

    work_dir = os.path.join(WORK_DIR, datetime.now().strftime('%Y%m%d_%H%M%S'))
    os.makedirs(work_dir, exist_ok=True)

    # ========== Step 1: IMA 去重集合 ==========
    log.info("Step 1: 从 IMA 拉取已有政策文件 (去重用)...")
    gd_existing, _ = fetch_ima_existing_titles(FOLDER_GD)
    moe_existing, _ = fetch_ima_existing_titles(FOLDER_MOE)
    log.info(f"   广东政策已存在 {len(gd_existing)} 条 (标题集合)")
    log.info(f"   全国政策已存在 {len(moe_existing)} 条 (标题集合)")

    gd_files = []   # [{path, title, date, source_url, source}]
    moe_files = []

    # ========== Step 2: 广东教育厅 ==========
    if not args.moe_only:
        log.info(f"\n{'='*70}")
        log.info("Step 2: 爬广东教育厅政策 API...")
        log.info(f"{'='*70}")

        articles = fetch_gd_policies(gd_pages)
        log.info(f"   共抓取 {len(articles)} 条")

        for idx, art in enumerate(articles):
            ts = art.get('date') or art.get('first_publish_time') or 0
            date_str = seconds_to_date(ts)
            title = art.get('title', '').strip()

            # 日期过滤
            if not within_days(date_str, args.days):
                continue

            # 下载: 优先 PDF/Word 附件, 无附件则保存详情页 HTML
            file_path = download_gd_policy(art, work_dir)
            if file_path:
                gd_files.append({
                    'path': file_path,
                    'title': title,
                    'date': date_str,
                    'source_url': art.get('url', ''),
                    'source': '广东省教育厅',
                })
                atts = art.get('attachment') or []
                kind = '📎' if atts else '📄'
                log.info(f"  [{idx+1}/{len(articles)}] ✅ {date_str} {kind} | {title[:45]}")
            else:
                log.warning(f"  [{idx+1}/{len(articles)}] ❌ 下载失败: {title[:45]}")

        log.info(f"   广东教育厅: 符合条件 {len(gd_files)} 个文件")

    # ========== Step 3: 教育部 ==========
    if not args.gd_only:
        log.info(f"\n{'='*70}")
        log.info("Step 3: 爬教育部最新文件列表...")
        log.info(f"{'='*70}")

        moe_items = fetch_moe_list(moe_pages)
        log.info(f"   共抓取 {len(moe_items)} 条")

        for idx, item in enumerate(moe_items):
            date_str = item['date']
            title = item['title']

            if not within_days(date_str, args.days):
                continue

            file_path = download_moe_policy(item, work_dir)
            if file_path:
                moe_files.append({
                    'path': file_path,
                    'title': title,
                    'date': date_str,
                    'source_url': item['url'],
                    'source': '教育部',
                })
                log.info(f"  [{idx+1}/{len(moe_items)}] ✅ {date_str} | {title[:45]}")
            else:
                log.info(f"  [{idx+1}/{len(moe_items)}] ⏭️ 下载失败: {title[:45]}")

        log.info(f"   教育部: 符合条件 {len(moe_files)} 个文件")

    # ========== Step 4: 去重 + 上传 ==========
    log.info(f"\n{'='*70}")
    log.info("Step 4: 去重 + 上传 IMA")
    log.info(f"{'='*70}")

    results = {}
    if gd_files:
        log.info(f"\n📁 上传广东省政策 ({len(gd_files)} 个)...")
        results['gd'] = deduplicate_and_upload(gd_files, FOLDER_GD, gd_existing, args.dry_run)

    if moe_files:
        log.info(f"\n📁 上传全国政策 ({len(moe_files)} 个)...")
        results['moe'] = deduplicate_and_upload(moe_files, FOLDER_MOE, moe_existing, args.dry_run)

    # ========== 汇总 ==========
    log.info(f"\n{'='*70}")
    log.info(f"📊 完成汇总")
    log.info(f"{'='*70}")
    total_succ = sum(r.get('success', 0) for r in results.values())
    total_fail = sum(r.get('fail', 0) for r in results.values())
    total_skip = sum(r.get('skip_dedup', 0) for r in results.values())
    log.info(f"   ✅ 新上传: {total_succ}")
    log.info(f"   ❌ 失败: {total_fail}")
    log.info(f"   ⏭️ 跳过(已存在): {total_skip}")
    if args.dry_run:
        log.info(f"   (DRY-RUN: 实际未上传)")
    log.info(f"   📂 工作目录: {work_dir}")
    log.info(f"   📝 日志: {log_file}")
    log.info(f"{'='*70}")


if __name__ == '__main__':
    main()
