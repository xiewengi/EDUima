#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
广东政府采购网 - 中标（成交）结果公告 → IMA 知识库
noticeType=00102，上传完整 HTML content
"""
import os, sys, json, re, time, tempfile, argparse, subprocess, logging
from datetime import datetime, timedelta
from urllib.parse import urlencode
import urllib.request

# ========= 配置 =========
SKILL_DIR = os.environ.get('IMA_SKILL_DIR', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ima-skill'))
IMA_API_CJS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ima_api.cjs')

FOLDER_ID = "folder_7508418185135953"
KB_ID = "o9q3d7B3xA1WPfSaOLqGrp-EeJ9kTXGTWM0kqf9S274="   # 教育平台（跟采购公告同一个）
NOTICE_TYPE = "00102"

GPO_HEADERS = {
    'Accept': 'application/json',
    'Cookie': 'regionCode=440001; regionFullName=%E7%9C%81%E6%9C%AC%E7%BA%A7; regionRemark=1',
    'Referer': 'https://gdgpo.czt.gd.gov.cn/maincms-web/noticeInformationGd',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
}

BASE_LIST = 'https://gdgpo.czt.gd.gov.cn/gpcms/rest/web/v2/info/selectInfoForIndex'
BASE_DETAIL = 'https://gdgpo.czt.gd.gov.cn/gpcms/rest/web/v2/info/getInfoById'

# ========= 日志 =========
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s', datefmt='%H:%M:%S')
log = logging.getLogger('winning')

# ========= IMA 凭据 =========
CLIENT_ID = os.environ.get('IMA_CLIENT_ID') or open(os.path.expanduser('~/.config/ima/client_id')).read().strip()
API_KEY = os.environ.get('IMA_API_KEY') or open(os.path.expanduser('~/.config/ima/api_key')).read().strip()
OPTS = json.dumps({"clientId": CLIENT_ID, "apiKey": API_KEY})

# ========= IMA API 调用 =========
def ima_api(path, body):
    proc = subprocess.run(
        ['node', IMA_API_CJS, path, json.dumps(body, ensure_ascii=False), OPTS],
        capture_output=True, text=True, timeout=30
    )
    if proc.returncode != 0:
        log.error(f"IMA API {path} 错误: {proc.stderr.strip()[:200]}")
        return None
    try:
        return json.loads(proc.stdout.strip())
    except:
        log.error(f"IMA API {path} 返回非 JSON: {proc.stdout.strip()[:200]}")
        return None

def cos_upload(file_path, cos_cred, content_type='text/html'):
    """用 COS credential 上传文件（动态查找 cos SDK）"""
    cred = cos_cred
    tmp_script = tempfile.NamedTemporaryFile(mode='w', suffix='.cjs', delete=False)
    tmp_script.write("""
const path = require('path');
const fs = require('fs');
let cosModulePath = '';
let dir = path.resolve(__dirname);
for (let i = 0; i < 5 && dir !== path.dirname(dir); i++) {
  const p = path.join(dir, 'node_modules', 'cos-nodejs-sdk-v5');
  if (fs.existsSync(p)) { cosModulePath = p; break; }
  dir = path.dirname(dir);
}
if (!cosModulePath) { console.error('cos-nodejs-sdk-v5 not found'); process.exit(1); }
const COS = require(cosModulePath);
const cred = """ + json.dumps(cred) + """;
const cos = new COS({
  SecretId: cred.secret_id,
  SecretKey: cred.secret_key,
  SecurityToken: cred.token || '',
});
cos.uploadFile({
  Bucket: cred.bucket_name,
  Region: cred.region,
  Key: cred.cos_key,
  FilePath: """ + json.dumps(file_path) + """,
  ContentType: """ + json.dumps(content_type) + """,
}).then(() => { process.exit(0); }).catch(e => { console.error(e); process.exit(1); });
""")
    tmp_script.close()
    proc = subprocess.run(['node', tmp_script.name], capture_output=True, text=True, timeout=120)
    os.unlink(tmp_script.name)
    if proc.returncode != 0:
        log.error(f"COS 上传失败: {(proc.stderr or proc.stdout or '').strip()[:300]}")
        return False
    return True

def gpo_get(url):
    req = urllib.request.Request(url, headers=GPO_HEADERS)
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode('utf-8'))

def fetch_list(days=7, keyword=''):
    end = datetime.now()
    start = end - timedelta(days=days)
    params_base = {
        'noticeType': NOTICE_TYPE,
        'siteId': 'cd64e06a-21a7-4620-aebc-0576bab7e07a',
        'title': keyword,
        'operationStartTime': start.strftime('%Y-%m-%d') + ' 00:00:00',
        'operationEndTime': end.strftime('%Y-%m-%d') + ' 23:59:59',
    }
    all_rows, page = [], 1
    while True:
        params = dict(params_base, currPage=page, pageSize=20)
        d = None
        for attempt in range(1, 4):
            try:
                d = gpo_get(f"{BASE_LIST}?{urlencode(params)}")
                break
            except Exception as e:
                if attempt < 3:
                    log.warning(f"  列表查询 page={page} 超时，第{attempt}次重试...")
                    time.sleep(2)
                else:
                    log.error(f"列表查询失败 page={page} (3次都超时): {e}")
                    break
        if d is None:
            break
        rows = d.get('data', {}).get('rows', [])
        total = d.get('data', {}).get('total', 0)
        if page == 1:
            log.info(f"📋 中标公告: {start.date()} ~ {end.date()}, 共 {total} 条")
        all_rows.extend(rows)
        if len(all_rows) >= total or len(rows) == 0:
            break
        page += 1
        time.sleep(0.3)
    return all_rows

def fetch_detail(rid):
    for attempt in range(1, 4):
        try:
            d = gpo_get(f"{BASE_DETAIL}?id={rid}")
            if d.get('code') == '200' and d.get('data'):
                return d['data']
            return None
        except Exception as e:
            if attempt < 3:
                time.sleep(2)
            else:
                log.error(f"详情失败 id={rid} (3次超时): {e}")
    return None

# ========= 上传到 IMA =========
def upload_to_ima(title, content_html, pub_date):
    """把中标公告 HTML 上传到 IMA"""
    # 构造完整 HTML
    safe_title = re.sub(r'[\\/:*?"<>|\s]+', '_', title)[:80] or 'untitled'
    html_content = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>{title}</title></head>
<body style="font-family: 'Microsoft YaHei', sans-serif; max-width: 900px; margin: 0 auto; padding: 20px;">
<h1 style="border-bottom: 2px solid #333; padding-bottom: 10px;">{title}</h1>
<p style="color: #888; font-size: 14px;">发布日期：{pub_date or '未知'}</p>
<hr/>
{content_html}
</body></html>"""

    tmpdir = tempfile.mkdtemp(prefix='ima_winning_')
    file_name = f"{safe_title}.html"
    file_path = os.path.join(tmpdir, file_name)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    file_size = os.path.getsize(file_path)
    file_ext = '.html'

    # 1) check_repeated_names
    resp = ima_api("openapi/wiki/v1/check_repeated_names", {
        "params": [{"name": file_name}],
        "knowledge_base_id": KB_ID,
        "folder_id": FOLDER_ID,
    })
    if resp and resp.get('code') == 0:
        results = resp.get('data', {}).get('results', [])
        if results and results[0].get('is_repeated'):
            log.info(f"  ⏭️ 已存在: {title[:40]}")
            return False

    # 2) create_media
    resp = ima_api("openapi/wiki/v1/create_media", {
        "file_name": file_name,
        "file_size": file_size,
        "content_type": "text/html",
        "knowledge_base_id": KB_ID,
        "file_ext": file_ext.lstrip("."),
    })
    if not resp or resp.get('code') != 0:
        log.error(f"  ❌ create_media 失败: {resp}")
        return False
    media_id = resp['data']['media_id']
    cos_cred = resp['data']['cos_credential']

    # 3) COS 上传
    if not cos_upload(file_path, cos_cred, 'text/html'):
        log.error(f"  ❌ COS 上传失败")
        return False

    # 4) add_knowledge
    resp = ima_api("openapi/wiki/v1/add_knowledge", {
        "media_type": 1,
        "media_id": media_id,
        "title": title,
        "knowledge_base_id": KB_ID,
        "folder_id": FOLDER_ID,
        "file_info": {
            "cos_key": cos_cred['cos_key'],
            "file_size": file_size,
            "file_name": file_name,
        },
    })
    if resp and resp.get('code') == 0:
        log.info(f"  ✅ 上传成功: {title[:50]}")
        return True
    else:
        log.error(f"  ❌ add_knowledge 失败: {resp}")
        return False

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--days', type=int, default=7)
    ap.add_argument('--keyword', default='学校')
    ap.add_argument('--limit', type=int, default=0)
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()

    log.info("=" * 50)
    log.info("广东中标公告采集 → IMA")
    log.info(f"最近 {args.days} 天, 关键词='{args.keyword}', 上限={args.limit or '全部'}")
    log.info(f"IMA folder: {FOLDER_ID}")
    log.info("=" * 50)

    rows = fetch_list(days=args.days, keyword=args.keyword)
    if not rows:
        log.warning("没有找到中标公告")
        return

    if args.limit > 0:
        rows = rows[:args.limit]

    success = skip = fail = 0
    for idx, row in enumerate(rows, 1):
        title = row['title']
        log.info(f"\n[{idx}/{len(rows)}] {title[:60]}")

        detail = fetch_detail(row['id'])
        if not detail:
            fail += 1; continue

        content_html = detail.get('content', '')
        pub_date = detail.get('operationTime') or detail.get('publishTime') or row.get('operationTime', '')
        clean_title = detail.get('title') or title

        if not content_html:
            log.warning(f"  ⚠️  无 content"); fail += 1; continue

        if args.dry_run:
            log.info(f"  📄 {len(content_html)} 字符 (dry-run)")
            success += 1; continue

        if upload_to_ima(clean_title, content_html, pub_date):
            success += 1
        else:
            skip += 1
        time.sleep(0.5)

    log.info(f"\n完成! ✅={success} ⏭️={skip} ❌={fail}")

if __name__ == '__main__':
    main()
