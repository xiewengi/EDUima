#!/usr/bin/env python3
"""
广东省政府采购网 → IMA知识库 采购公告自动化采集脚本

功能:
  1. 查询指定时间范围内(默认最近3天)的采购公告 (noticeType=00101)
  2. 遍历获取详情, 下载ZIP附件, 解压提取 .docx/.doc
  3. 调用IMA check_repeated_names 去重
  4. 批量上传到 IMA 「教育平台 → 采购公告（广东省）」

用法:
  python3 gd_gpo_ima_sync.py                 # 默认: 最近3天
  python3 gd_gpo_ima_sync.py --days 2        # 最近2天
  python3 gd_gpo_ima_sync.py --start 2026-09-17 --end 2026-09-24  # 自定义范围
  python3 gd_gpo_ima_sync.py --dry-run       # 只采集不上传
"""

import urllib.request, json, re, os, sys, zipfile, time, argparse, subprocess, logging
from urllib.parse import urlencode
from datetime import datetime, timedelta

# ========== 配置 ==========
SKILL_DIR = os.environ.get('IMA_SKILL_DIR', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ima-skill'))
CLIENT_ID = os.environ.get('IMA_CLIENT_ID') or open(os.path.expanduser('~/.config/ima/client_id')).read().strip()
API_KEY = os.environ.get('IMA_API_KEY') or open(os.path.expanduser('~/.config/ima/api_key')).read().strip()
OPTS = json.dumps({"clientId": CLIENT_ID, "apiKey": API_KEY})

# IMA 目标位置
KB_ID = "o9q3d7B3xA1WPfSaOLqGrp-EeJ9kTXGTWM0kqf9S274="   # 教育平台
FOLDER_ID = "folder_7508355157328511"                      # 采购公告（广东省）

# 广东省政府采购网 API
GPO_HEADERS = {
    'Accept': 'application/json',
    'Cookie': 'regionCode=440001; regionFullName=%E7%9C%81%E6%9C%AC%E7%BA%A7; regionRemark=1',
    'Referer': 'https://gdgpo.czt.gd.gov.cn/maincms-web/noticeInformationGd',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
}
BASE_LIST = 'https://broken-wildflower-accf.304997019.workers.dev'/gpcms/rest/web/v2/info/selectInfoForIndex'
BASE_DETAIL = 'https://gdgpo.czt.gd.gov.cn/gpcms/rest/web/v2/info/getInfoById'

# 本地工作目录
WORK_DIR = '/tmp/gdgpo_sync'
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')

# ========== 日志 ==========
os.makedirs(LOG_DIR, exist_ok=True)
log_file = os.path.join(LOG_DIR, f'sync_{datetime.now().strftime("%Y%m%d")}.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler(sys.stdout),
    ]
)
log = logging

# ========== 工具函数 ==========
def ima_api(path, body):
    """调用 IMA API"""
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
        log.error(f"IMA API JSON解析失败: {e}, output={proc.stdout[:200]}")
        return None

def preflight_check(file_path):
    proc = subprocess.run(
        ['node', f'{SKILL_DIR}/knowledge-base/scripts/preflight-check.cjs', '--file', file_path],
        capture_output=True, text=True, timeout=30
    )
    return json.loads(proc.stdout.strip())

def cos_upload(file_path, cos_credential, content_type, max_retries=3):
    """COS 上传带重试"""
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
            log.warning(f"  COS上传失败(第{attempt}次): {err[:100]}, 5秒后重试...")
            time.sleep(5)
        else:
            log.error(f"  COS上传失败(已重试{max_retries}次): {err[:100]}")
    return False

def safe_filename(name):
    return re.sub(r'[\\/:*?"<>|\n\r\t]', '_', str(name))[:100]

# ========== 核心流程 ==========
def fetch_notices(start_date, end_date):
    """分页查询采购公告列表"""
    params_base = {
        'title': '学校',
        'noticeType': '00101',
        'siteId': 'cd64e06a-21a7-4620-aebc-0576bab7e07a',
        'operationStartTime': f'{start_date} 00:00:00',
        'operationEndTime': f'{end_date} 23:59:59',
    }
    
    all_rows = []
    page = 1
    page_size = 20
    
    while True:
        params = dict(params_base)
        params['currPage'] = page
        params['pageSize'] = page_size
        
        url = f"{BASE_LIST}?{urlencode(params)}"
        try:
            req = urllib.request.Request(url, headers=GPO_HEADERS)
            with urllib.request.urlopen(req, timeout=15) as resp:
                d = json.loads(resp.read().decode('utf-8'))
        except Exception as e:
            log.error(f"列表查询失败 page={page}: {e}")
            break
        
        rows = d.get('data', {}).get('rows', [])
        total = d.get('data', {}).get('total', 0)
        
        if page == 1:
            log.info(f"📋 采购公告查询: {start_date} ~ {end_date}, 共 {total} 条")
        
        all_rows.extend(rows)
        log.info(f"  第{page}页: +{len(rows)} (累计{len(all_rows)}/{total})")
        
        if len(all_rows) >= total or len(rows) == 0:
            break
        page += 1
        time.sleep(0.3)
    
    return all_rows

def extract_word_files(rows, work_dir):
    """遍历详情, 下载ZIP, 提取Word文件"""
    word_files = []
    skip_count = 0
    error_count = 0
    
    for idx, row in enumerate(rows, 1):
        rid = row['id']
        title = row['title']
        safe_title = safe_filename(title)[:80]
        
        try:
            # 获取详情
            detail_url = f"{BASE_DETAIL}?id={rid}"
            req = urllib.request.Request(detail_url, headers=GPO_HEADERS)
            with urllib.request.urlopen(req, timeout=15) as resp:
                d = json.loads(resp.read().decode('utf-8'))
            
            if d.get('code') != '200' or not d.get('data'):
                log.warning(f"  [{idx}/{len(rows)}] 详情失败: {safe_title[:40]}")
                error_count += 1
                continue
            
            dd = d['data']
            attchs = dd.get('attchList', [])
            
            # 找 zip
            zip_attch = None
            for a in attchs:
                if a.get('fileExt', '').lower() == '.zip' or '.zip' in a.get('fileName', '').lower():
                    zip_attch = a
                    break
            
            if not zip_attch:
                # fallback: content 里找 zip
                content = dd.get('content', '') or ''
                zip_links = re.findall(r'href=[\'"]([^\'"]+freecms/download[^\'"]+\.zip[^\'"]*)[\'"]', content)
                if zip_links:
                    zip_attch = {'fileName': 'attachment.zip', 'fileUrl': zip_links[0]}
            
            if not zip_attch:
                log.info(f"  [{idx}/{len(rows)}] ⏭️ 无ZIP: {safe_title[:40]}")
                skip_count += 1
                continue
            
            # 下载 ZIP
            file_url = zip_attch.get('fileUrl', '')
            if not file_url.startswith('http'):
                file_url = 'https://gdgpo.czt.gd.gov.cn' + file_url
            
            zip_path = os.path.join(work_dir, f"{idx:03d}_{safe_title[:50]}.zip")
            req = urllib.request.Request(file_url, headers={
                'User-Agent': 'Mozilla/5.0',
                'Referer': 'https://gdgpo.czt.gd.gov.cn/',
            })
            with urllib.request.urlopen(req, timeout=60) as resp:
                zip_data = resp.read()
            
            if len(zip_data) < 1000:
                log.warning(f"  [{idx}/{len(rows)}] ZIP太小: {safe_title[:40]} ({len(zip_data)}B)")
                skip_count += 1
                continue
            
            with open(zip_path, 'wb') as f:
                f.write(zip_data)
            
            # 解压提取 Word
            word_found = False
            with zipfile.ZipFile(zip_path, 'r') as zf:
                for info in zf.infolist():
                    fname = info.filename
                    flower = fname.lower()
                    if flower.endswith('.docx') or flower.endswith('.doc'):
                        base = os.path.basename(fname)
                        safe_base = safe_filename(base)
                        if not safe_base:
                            continue
                        target = os.path.join(work_dir, f"{safe_title[:50]}_{safe_base}")
                        with zf.open(info) as src, open(target, 'wb') as dst:
                            dst.write(src.read())
                        word_files.append({
                            'path': target,
                            'title': title,
                            'notice_time': row.get('noticeTime', ''),
                            'source_id': rid,
                            'size': os.path.getsize(target),
                        })
                        word_found = True
                        break
            
            if word_found:
                log.info(f"  [{idx}/{len(rows)}] ✅ {safe_title[:45]}")
            else:
                log.info(f"  [{idx}/{len(rows)}] ⚠️ ZIP无Word: {safe_title[:45]}")
                skip_count += 1
            
            time.sleep(0.3)
            
        except Exception as e:
            log.error(f"  [{idx}/{len(rows)}] ❌ {safe_title[:40]}: {e}")
            error_count += 1
    
    log.info(f"📦 采集汇总: 总计{len(rows)} | ✅Word:{len(word_files)} | ⏭️跳过:{skip_count} | ❌错误:{error_count}")
    return word_files

def deduplicate_and_upload(word_files):
    """去重 + 批量上传 IMA"""
    if not word_files:
        log.info("📭 没有待上传文件")
        return {"success": 0, "fail": 0, "skip_dedup": 0}
    
    # Step 1: 批量 preflight + 重名检查
    log.info(f"🔍 重名检查 ({len(word_files)} 个文件)...")
    batch_params = []
    pf_results = []
    
    for w in word_files:
        pf = preflight_check(w['path'])
        pf_results.append(pf)
        if pf.get('pass'):
            batch_params.append({"name": pf['file_name'], "media_type": pf['media_type']})
        else:
            log.warning(f"  preflight失败: {os.path.basename(w['path'])}")
    
    rename_map = {}
    if batch_params:
        resp = ima_api("openapi/wiki/v1/check_repeated_names", {
            "params": batch_params,
            "knowledge_base_id": KB_ID,
            "folder_id": FOLDER_ID,
        })
        
        if resp and resp.get('code') == 0:
            results = resp.get('data', {}).get('results', [])
            ts = time.strftime("%Y%m%d%H%M%S")
            skip_indices = set()
            
            for i, r in enumerate(results):
                if r.get('is_repeated'):
                    original = word_files[i]['path']
                    fname = batch_params[i]['name']
                    name_base, ext = os.path.splitext(fname)
                    new_name = f"{name_base}_{ts}{ext}"
                    # 同时重命名本地文件
                    dir_path = os.path.dirname(original)
                    new_path = os.path.join(dir_path, new_name)
                    os.rename(original, new_path)
                    word_files[i]['path'] = new_path
                    rename_map[new_path] = new_name
                    log.info(f"  ⚠️ 重名改名: {fname[:40]}... → ..._{ts}...")
            
            if not rename_map:
                log.info("  ✅ 无重名")
    
    # Step 2: 逐个上传
    log.info(f"🚀 开始上传 {len(word_files)} 个文件...")
    success_count = 0
    fail_count = 0
    
    for idx, w in enumerate(word_files, 1):
        pf = pf_results[idx-1]
        if not pf.get('pass'):
            fail_count += 1
            continue
        
        file_name = pf['file_name']
        file_ext = pf['file_ext']
        file_size = pf['file_size']
        media_type = pf['media_type']
        content_type = pf['content_type']
        
        final_name = rename_map.get(w['path'], file_name)
        
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
        if not cos_upload(w['path'], cos_cred, content_type):
            log.error(f"  [{idx}/{len(word_files)}] COS上传失败: {final_name[:40]}")
            fail_count += 1
            continue
        
        # add_knowledge
        resp = ima_api("openapi/wiki/v1/add_knowledge", {
            "media_type": media_type,
            "media_id": media_id,
            "title": final_name,
            "knowledge_base_id": KB_ID,
            "folder_id": FOLDER_ID,
            "file_info": {
                "cos_key": cos_cred['cos_key'],
                "file_size": file_size,
                "file_name": final_name,
            }
        })
        
        if resp and resp.get('code') == 0:
            success_count += 1
            size_kb = file_size / 1024
            log.info(f"  [{idx}/{len(word_files)}] ✅ {final_name[:45]} ({size_kb:.0f}KB)")
        else:
            fail_count += 1
        
        time.sleep(0.5)
    
    log.info(f"📊 上传: ✅{success_count} ❌{fail_count}")
    return {"success": success_count, "fail": fail_count}

# ========== 主入口 ==========
def main():
    parser = argparse.ArgumentParser(description='广东政府采购网 → IMA 采购公告自动同步')
    parser.add_argument('--days', type=int, default=3, help='最近N天 (默认3)')
    parser.add_argument('--start', type=str, help='自定义开始日期 YYYY-MM-DD')
    parser.add_argument('--end', type=str, help='自定义结束日期 YYYY-MM-DD')
    parser.add_argument('--dry-run', action='store_true', help='只采集不上传')
    args = parser.parse_args()
    
    # 确定日期范围
    if args.start and args.end:
        start_date, end_date = args.start, args.end
    else:
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=args.days-1)).strftime('%Y-%m-%d')
    
    log.info(f"{'='*60}")
    log.info(f"🚀 广东政府采购网 → IMA 采购公告同步")
    log.info(f"   时间范围: {start_date} ~ {end_date}")
    log.info(f"   目标: 教育平台 → 采购公告（广东省）")
    if args.dry_run:
        log.info(f"   🧪 DRY RUN 模式 (不上传)")
    log.info(f"{'='*60}")
    
    # 工作目录
    work_dir = os.path.join(WORK_DIR, datetime.now().strftime('%Y%m%d_%H%M%S'))
    os.makedirs(work_dir, exist_ok=True)
    
    # Step 1: 查询列表
    rows = fetch_notices(start_date, end_date)
    if not rows:
        log.info("📭 无采购公告, 退出")
        return
    
    # Step 2: 采集 Word 文件
    word_files = extract_word_files(rows, work_dir)
    if not word_files:
        log.info("📭 无Word文件, 退出")
        return
    
    # Step 3: 去重 + 上传
    if args.dry_run:
        log.info(f"🧪 DRY RUN: 采集到 {len(word_files)} 个Word文件, 跳过上传")
    else:
        result = deduplicate_and_upload(word_files)
        log.info(f"✅ 完成! 上传 {result['success']} 个, 失败 {result['fail']} 个")
    
    log.info(f"📂 工作目录: {work_dir}")
    log.info(f"📝 日志: {log_file}")
    log.info(f"{'='*60}")

if __name__ == '__main__':
    main()
