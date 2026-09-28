#!/usr/bin/env python3
"""
解析 + 匹配模块
读取 .sync_tmp/ 里的 docx/pdf 文件和 meta.json → 输出 public/data/bidding.json
"""
import re, os, sys, json, glob
from os.path import join, dirname
from datetime import datetime

try:
    from docx import Document
except ImportError:
    print("⚠️  python-docx 未安装，请运行: pip3 install python-docx")
    sys.exit(1)

try:
    from pypdf import PdfReader
except ImportError:
    print("⚠️  pypdf 未安装，请运行: pip3 install pypdf")
    sys.exit(1)

# 路径
ROOT = dirname(dirname(os.path.abspath(__file__)))
TMP  = join(ROOT, '.sync_tmp')
OUT  = join(ROOT, 'public', 'data', 'bidding.json')

GENERIC = {
    '采购项目','项目','采购','招标','公告','工程','服务','设备','提升','建设',
    '实施','改造','运行','维护','管理','中心','基地','平台','系统','实训室',
    '实验室','场地','场室','园区','校区','智慧','数字化','信息化','设施',
    '采购包','合同包','结果','明细','附件','报价','投标','成交'
}

# ==================== DOCX 解析 ====================
def parse_docx(path):
    try:
        doc = Document(path)
        text = '\n'.join(p.text for p in doc.paragraphs if p.text.strip())
    except Exception as e:
        print(f"  [warn] docx 解析失败 {os.path.basename(path)}: {e}")
        return {}
    r = {}
    # 采购项目编号（广东标准格式）
    for pat in [r'采购[项目计划]*编号[：:\s]*([0-9]{6}-[0-9]{4}-[0-9]+)',
                r'采购[项目计划]*编号[：:\s]*(CZ\d{4}[-—]\d+)']:
        m = re.search(pat, text)
        if m: r['code'] = m.group(1).replace('—', '-'); break
    # 项目名称
    m = re.search(r'项目名称[：:\s]*([^\n\r]{4,80})', text)
    if m: r['project_name'] = m.group(1).strip()
    # 采购人
    m = re.search(r'采购人[：:\s]*([^\n\r（(\n]{2,40})', text)
    if m: r['buyer'] = m.group(1).strip()
    # 采购包
    packs = sorted(set(re.findall(r'采购包(\d)', text)))
    if packs: r['packs'] = packs
    # 预算
    m = re.search(r'预算金额[：:\s]*([0-9,.]+)\s*元', text)
    if m: r['budget'] = m.group(1).replace(',', '')
    # 投标截止日期
    m = re.search(r'([0-9]{4})年([0-9]{1,2})月([0-9]{1,2})[日号]', text)
    if m and '投标' in text[max(0, text.find(m.group(0))-30):text.find(m.group(0))]:
        r['bid_deadline'] = f"{m.group(1)}-{m.group(2).zfill(2)}-{m.group(3).zfill(2)}"
    return r

# ==================== PDF 解析 ====================
def parse_pdf(path, max_pages=3):
    try:
        reader = PdfReader(path)
        text = ''
        for page in reader.pages[:max_pages]:
            t = page.extract_text() or ''
            text += t + '\n'
    except Exception as e:
        print(f"  [warn] pdf 解析失败 {os.path.basename(path)}: {e}")
        return {}
    r = {}
    for pat in [r'采购[项目计划]*编号[：:\s]*([0-9]{6}-[0-9]{4}-[0-9]+)',
                r'采购[项目计划]*编号[：:\s]*(CZ\d{4}[-—]\d+)']:
        m = re.search(pat, text)
        if m: r['code'] = m.group(1).replace('—', '-'); break
    m = re.search(r'项目名称[：:\s]*([^\n\r]{4,80})', text)
    if m: r['project_name'] = m.group(1).strip()
    m = re.search(r'(?:采购人|招标人|采购单位)[：:\s]*([^\n\r（(\n]{2,40})', text)
    if m: r['buyer'] = m.group(1).strip()
    # 中标人（需要更多上下文）
    m = re.search(r'(?:中标|成交)[（(]?供应商[)）]?[：:\s]*([^\n\r（(\n]{2,40}?有限公司|[^\n\r（(\n]{2,30})', text)
    if not m: m = re.search(r'(?:中标|成交)[（(]?单位[)）]?[：:\s]*([^\n\r（(\n]{2,40})', text)
    if m: r['winner'] = m.group(1).strip()
    # 中标金额
    m = re.search(r'(?:中标|成交)[（(]?金额[)）]?[：:\s]*([0-9,.]+)\s*元', text)
    if m: r['amount'] = m.group(1).replace(',', '')
    # 合同包
    m = re.search(r'(?:合同包|采购包)[：:\s]*(\d)', text)
    if m: r['contract_no'] = '合同包' + m.group(1)
    # 发布日期
    m = re.search(r'(?:发布|公告)[^\n]{0,10}时间[：:\s]*([0-9]{4}[-/年][0-9]{1,2}[-/月][0-9]{1,2})', text)
    if not m: m = re.search(r'(2026[-/年][0-9]{1,2}[-/月][0-9]{1,2})', text)
    if m:
        d = m.group(1).replace('年','-').replace('月','-').replace('/','-').replace('日','')
        r['publish_date'] = d
    return r

# ==================== 文件名解析 ====================
def extract_from_filename(filename):
    name = filename
    m = re.match(r'(\d+)_', name)
    num = m.group(1) if m else ''
    clean = re.sub(r'^\d+_', '', name)
    clean = re.sub(r'\.[^.]+$', '', clean)
    clean = re.sub(r'_z\d+$', '', clean)
    # 学校
    school = ''
    sm = re.match(r'(.+?(?:学校|学院|中职|中学|小学|幼儿园|技工学校|职业技术|理工学校|未来学校|中心))', clean)
    if sm:
        school = sm.group(1)
        rest = clean[len(school):].strip('—-_')
    else:
        rest = clean
    # 类型
    type_ = '招标公告'
    if '竞争性磋商' in clean: type_ = '竞争性磋商'
    elif '竞争性谈判' in clean: type_ = '竞争性谈判'
    elif '询价' in clean: type_ = '询价'
    title = re.sub(r'(招标|磋商|谈判|询价|单一来源)?公告$', '', rest).strip()
    # 地区
    region = ''
    cities = ['广州','东莞','深圳','佛山','珠海','中山','惠州','江门','茂名','湛江',
              '肇庆','清远','韶关','梅州','河源','阳江','潮州','揭阳','汕尾','云浮',
              '化州','普宁','清城','高唐','文德']
    for r in cities:
        if r in school + clean: region = r; break
    # 学段
    stage = '基础教育'
    s_text = school + title
    if '幼儿园' in s_text or '托儿所' in s_text: stage = '学前教育'
    elif any(k in s_text for k in ['技工学校','职业技术','中职','中专','职业学校']): stage = '职业教育'
    elif any(k in s_text for k in ['大学','学院','高等专科']): stage = '高等教育'
    return {'num': num, 'title': title, 'school': school, 'region': region,
            'type': type_, 'stage': stage, 'filename': name}

# ==================== 匹配算法 ====================
def school_norm(s):
    if not s: return ''
    s = s.strip()
    s = re.sub(r'[（(].*?[)）]', '', s)
    return s

def school_variants(s):
    if not s: return []
    variants = [s, school_norm(s)]
    cities = ['广州','东莞','深圳','佛山','珠海','中山','惠州','江门','茂名','湛江',
              '肇庆','清远','韶关','梅州','河源','阳江','潮州','揭阳','汕尾','云浮',
              '化州','普宁','广州市','东莞市','深圳市']
    norm = school_norm(s)
    for c in cities:
        if s.startswith(c) and len(s) > len(c): variants.append(s[len(c):])
        if norm.startswith(c) and len(norm) > len(c): variants.append(norm[len(c):])
    return list(set(v for v in variants if v and len(v) >= 2))

def project_keywords(title):
    if not title: return set()
    words = set()
    clean = re.sub(r'[^\u4e00-\u9fffA-Za-z0-9]', '', title)
    for L in [4, 3, 2]:
        for i in range(len(clean) - L + 1):
            w = clean[i:i+L]
            if w not in GENERIC: words.add(w)
    return words

# ==================== 主流程 ====================
def main():
    meta_path = join(TMP, 'meta.json')
    if not os.path.exists(meta_path):
        print("❌ 找不到 meta.json，请先运行 sync.js")
        sys.exit(1)
    meta = json.load(open(meta_path))

    print(f"📂 解析目录: {TMP}")

    # ---- 采购公告 ----
    print("\n📋 解析采购公告 docx...")
    proc_items = []
    for m in meta['procurement']:
        path = join(TMP, m['file'])
        if not os.path.exists(path):
            print(f"  [skip] 文件不存在: {m['file']}")
            continue
        parsed = parse_docx(path)
        ff = extract_from_filename(m['title'])
        item = {
            'id': f"P{ff['num'].zfill(3)}",
            'num': ff['num'],
            'title': parsed.get('project_name') or ff['title'],
            'school': parsed.get('buyer') or ff['school'],
            'region': ff['region'],
            'type': ff['type'],
            'stage': ff['stage'],
            'procCode': parsed.get('code', ''),
            'budget': parsed.get('budget'),
            'packs': parsed.get('packs', ['1']),
            'bidDeadline': parsed.get('bid_deadline'),
            'docFile': m['title'],
            'mediaId': m['media_id'],
            'matchedIds': [],
        }
        proc_items.append(item)
        print(f"  {item['id']} [{item['procCode'] or '':16s}] {item['school']}")

    # ---- 中标公告 ----
    print("\n🏆 解析中标公告 pdf...")
    win_items = []
    for m in meta['winning']:
        path = join(TMP, m['file'])
        num = m['title'].split('_')[0] if m['title'].startswith(tuple('0123456789')) else ''
        parsed = parse_pdf(path) if os.path.exists(path) else {}
        ff = extract_from_filename(m['title'])
        attach = {'type': 'main', 'file': m['title'], 'mediaId': m['media_id']}
        if '报价明细' in m['title']: attach['type'] = '报价明细附件'
        elif '中小企业声明' in m['title']: attach['type'] = '中小企业声明函'
        elif '本国产品' in m['title']: attach['type'] = '本国产品声明函'
        elif '分项报价' in m['title']: attach['type'] = '分项报价表'

        existing = next((x for x in win_items if x['num'] == num), None)
        if existing:
            existing['attachments'].append(attach)
            if parsed.get('contract_no') and parsed['contract_no'] not in existing['contractNos']:
                existing['contractNos'].append(parsed['contract_no'])
            # 补充字段
            if not existing.get('projectCode') and parsed.get('code'): existing['projectCode'] = parsed['code']
            if not existing.get('winningBidder') and parsed.get('winner'): existing['winningBidder'] = parsed['winner']
            if not existing.get('winningAmount') and parsed.get('amount'): existing['winningAmount'] = parsed['amount']
            if not existing.get('school') and (parsed.get('buyer') or ff['school']):
                existing['school'] = parsed.get('buyer') or ff['school']
            if not existing.get('title') and (parsed.get('project_name') or ff['title']):
                existing['title'] = parsed.get('project_name') or ff['title']
        else:
            item = {
                'id': f"W{num.zfill(3)}",
                'num': num,
                'title': parsed.get('project_name') or ff['title'],
                'school': parsed.get('buyer') or ff['school'],
                'region': ff['region'],
                'projectCode': parsed.get('code', ''),
                'stage': ff['stage'],
                'winningBidder': parsed.get('winner'),
                'winningAmount': parsed.get('amount'),
                'publishDate': parsed.get('publish_date'),
                'contractNos': [parsed.get('contract_no', '合同包1')],
                'attachments': [attach],
            }
            win_items.append(item)

    # 排序
    win_items.sort(key=lambda x: int(x['num'] or 0))
    for w in win_items:
        w['contractNo'] = '/'.join(sorted(set(w['contractNos'])))
        w['attachCount'] = len(w['attachments'])
        del w['contractNos']
        print(f"  {w['id']} [{w.get('projectCode') or '':16s}] {w['school']} | 中标:{(w.get('winningBidder') or '?')[:15]} | {w['attachCount']}附件")

    # ---- 精准匹配 ----
    print(f"\n{'='*50}")
    print("🔗 精准匹配（学校精确 + 核心词交集）")
    print(f"{'='*50}")
    for p in proc_items:
        p['matchedIds'] = []
        p_sv = school_variants(p['school'])
        p_kw = project_keywords(p['title'])
        for w in win_items:
            w_sv = school_variants(w['school'])
            w_kw = project_keywords(w['title'])
            school_ok = bool(set(p_sv) & set(w_sv))
            kw_overlap = p_kw & w_kw
            kw_ok = len(kw_overlap) >= 1
            if school_ok and kw_ok:
                p['matchedIds'].append(w['id'])

    matched_proc = [p for p in proc_items if p['matchedIds']]
    unmatched_proc = [p for p in proc_items if not p['matchedIds']]

    # 中标反向关联
    for w in win_items:
        w['matchedProcurementIds'] = [p['id'] for p in proc_items if w['id'] in p['matchedIds']]

    print(f"📊 匹配结果: {len(matched_proc)}/{len(proc_items)} 精准匹配")
    for p in matched_proc:
        matched_w = [w for w in win_items if w['id'] in p['matchedIds']]
        for w in matched_w:
            print(f"  📋 {p['school'][:12]}... → 🏆 {w['school'][:12]}... | 核心词交集 OK")

    # ---- 输出 ----
    out = {
        'updated': datetime.now().strftime('%Y-%m-%d'),
        'matchStats': {
            'procurementTotal': len(proc_items),
            'winningTotal': len(win_items),
            'matchedCount': len(matched_proc),
            'unmatchedCount': len(unmatched_proc),
            'matchedWinIds': [w['id'] for w in win_items if w['matchedProcurementIds']],
        },
        'procurement': proc_items,
        'winning': win_items,
    }
    os.makedirs(dirname(OUT), exist_ok=True)
    json.dump(out, open(OUT, 'w'), ensure_ascii=False, indent=2)
    print(f"\n✓ 已写入 {OUT}")
    print(f"  采购: {len(proc_items)} 条 | 中标: {len(win_items)} 项目 | 匹配: {len(matched_proc)}")

if __name__ == '__main__':
    main()
