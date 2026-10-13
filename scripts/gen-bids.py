# -*- coding: utf-8 -*-
"""从 ima 知识库快照生成 policy-portal 的招投标数据 public/data/bidding.json。

取值逻辑照抄医疗平台知识库站点的 gen-bids.py（2026-10-13），差异只有三处：
  1. 数据源换成 ima 知识库「教育平台」的招投标两个文件夹（fetch-bids.js 快照）；
  2. 本站无后端：医疗站在 server/store.js 响应期合并的 gdgpo 反查链接
     （_raw/bids-source-urls.json）与「采购结果」抽取（_raw/bids-award-info.json）
     改为在本脚本生成期直接合并进条目；
  3. 兼容继承旧 bidding.json（parse_match.py 链路产物）里 winning 条目的
     region/stage/school/projectCode/publishDate —— 供页面地区/学段筛选继续工作。

数据来源：
    data/_raw/ima-bids.json
        —— ima 知识库「教育平台」招投标文件夹条目快照，
           由 scripts/fetch-bids.js 遍历后落盘（含正文存档指针）。
           正文存档：data/_raw/bids-md/*.md

约定（与医疗站 gen-bids.py 同一口径）：
    · 本脚本只做「清洗与字段化」，不做任何推断或补全。原文里没有的字段留空。
    · 摘要必须来自原文（正文存档或 ima 返回的 introduction），抓不到就留空，
      绝不推断、绝不补全。
"""
import json
import os
import re
from datetime import datetime, timedelta, timezone

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))     # policy-portal/
RAW_DIR = os.path.join(BASE, 'data', '_raw')
OUT_DIR = os.path.join(BASE, 'public', 'data')

CST = timezone(timedelta(hours=8))

SUMMARY_LIMIT = 220          # 摘要最大字数
MIN_PARA_LEN = 20            # 判定「有实质内容段落」的最小长度

KNOWLEDGE_BASE = {
    'label': '教育平台',
    'kbId': 'o9q3d7B3xA1WPfSaOLqGrp-EeJ9kTXGTWM0kqf9S274=',
    'shareId': '',
    'note': '招投标信息条目，直接取自该 ima 知识库的招投标文件夹。',
}

IMA_SHARE_PREFIX = 'https://ima.qq.com/wiki/?shareId='

PARSE_STATE = {1: '解析中', 2: '解析完成', 3: '解析失败'}

# 摘要正文里常见的排版残留符号名（同医疗站 gen-bids.py 的处理）
ARTIFACT_WORDS = ('blackdiamond|bullet|blackcircle|blacksquare|whitestar|blackstar'
                  '|blackright|blackleft|rightarrow|leftarrow|blacklozenge')


def clean_md(text):
    """去掉 markdown 标记与排版残留，得到可读纯文本。"""
    # 公告正文存档源自网页，常带 HTML 转义实体（如 &lt;招标代理…&gt;），
    # 不解码的话 esc() 之后页面上会原样露出「&lt;」字样。仅解码常见五件套，属清洗不改写。
    for ent, ch in (('&lt;', '<'), ('&gt;', '>'), ('&quot;', '"'),
                    ('&#39;', "'"), ('&amp;', '&')):
        text = text.replace(ent, ch)
    text = re.sub(r'```.*?```', ' ', text, flags=re.S)
    text = re.sub(r'!\[[^\]]*\]\([^)]*\)', ' ', text)
    text = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', text)
    text = re.sub(r'^#{1,6}\s*', '', text, flags=re.M)
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'[`>#*$\\]', '', text)
    text = re.sub(r'(?i)\b(?:' + ARTIFACT_WORDS + r')\s*(?=[\u4e00-\u9fff0-9])', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return re.sub(r'^[/•·\-—\s]+', '', text)


def clip(text, limit):
    text = (text or '').strip()
    if not text:
        return ''
    return text[:limit].rstrip() + ('…' if len(text) > limit else '')


def first_meaningful(text, limit=SUMMARY_LIMIT):
    """从正文里挑一段有实质内容的文字作摘要。只做选取与截断，不改写不补全；
    挑不出合格段落就返回空串（退回 introduction，由调用方处理）。作为定向挑段的兜底。"""
    paras = []
    for chunk in re.split(r'\n\s*\n', text or ''):
        if '![' in chunk or 'graph TD' in chunk or 'graph LR' in chunk:
            continue
        c = clean_md(chunk)
        if len(c) < MIN_PARA_LEN:
            continue
        if c.count('|') > 2:                                   # 表格行压平后不适合当摘要
            continue
        if re.match(r'^[\d\s.、,，|]+$', c):                    # 纯页码 / 纯编号
            continue
        paras.append(c)
    if not paras:
        return ''
    for p in paras:
        if 40 <= len(p) <= 400:
            return clip(p, limit)
    return clip(paras[0], limit)


# -------------------------------------------------------------- 定向挑段摘要
# 公告正文是相对固定的版式（gdgpo 九段式结果公告 / 招标文件式采购公告），
# 与其取「开头一段」（常是联系方式、专家名单），不如定向抽取「项目内容」：
# 主要标的信息（品目/采购标的/服务时间）、预算金额、履约期限等。
# 只做「从原文选取与字段化」，值一律原样保留（含转档乱码，不猜不改写）。

SEC_HEAD_RE = re.compile(r'^\s*#{0,6}\s*([一二三四五六七八九十]{1,3})\s*[、.．]\s*(.{1,24}?)\s*#*\s*$')

# 摘要里值得展示的字段（顺序即展示顺序）。AWARD_FIELDS 只在 awardBlock 没覆盖时才进摘要，
# 避免与卡片的「采购结果」块重复展示供应商/金额。
WANTED_KEYS = ('品目名称', '采购标的', '品牌', '规格型号', '数量', '服务时间',
               '合同履行期限', '预算金额', '采购方式', '供应商名称', '中标(成交)金额',
               '中标（成交）金额')
AWARD_FIELDS = {'供应商名称', '中标(成交)金额', '中标（成交）金额'}
KEY_DISPLAY = {'中标(成交)金额': '中标金额', '中标（成交）金额': '中标金额'}

PLACEHOLDER_EXACT = {'', '无', '/', '—', '-', '不涉及', '详见招标文件', '详见第二章',
                     '完全按照招标文件要求', '完全响应招标文件要求', '不适用', '——'}


def is_placeholder(v):
    """占位值 / 乱码值判定：不进摘要（丢字段不丢信息，正文里本来就没有实际内容）。"""
    v = v.strip()
    if v in PLACEHOLDER_EXACT:
        return True
    if re.fullmatch(r'[?？□②₂①③*。，、:：;；·\s]+', v):        # 转档乱码 / 空值
        return True
    if v.startswith('详见'):
        return True
    if re.fullmatch(r'完全(?:按照|响应)招标文件(?:要求)?', v):
        return True
    return False


def split_sections(text):
    """按「一、二、…」编号标题行切段，返回 [(段名, 段正文)]，段外文字记段名为 ''。"""
    secs, cur_name, cur = [], '', []
    for line in (text or '').splitlines():
        m = SEC_HEAD_RE.match(line)
        if m:
            secs.append((cur_name, '\n'.join(cur)))
            cur_name, cur = m.group(2).strip().rstrip('：:'), [line]
        else:
            cur.append(line)
    secs.append((cur_name, '\n'.join(cur)))
    return secs


# 表头单元格特征：短字段名，无金额/编号等数据特征。用于在一个连续表格块里识别多张子表
# （如 gdgpo 结果公告的「采购结果」段常连排 供应商表 + 品目表，中间无空行）。
HEADER_CELL_RE = re.compile(
    r'^(品目号|品目名称|采购标的|品牌|规格型号|数量.*|单价.*|总价.*|供应商名称|供应商地址'
    r'|中标[（(]成交[)）]金额|成交金额|服务范围|服务要求|服务时间|服务标准|序号|合同包号'
    r'|合同包名称|收取对象|代理服务.*|项目名称|项目编号|联系方式)$')


def looks_header(cells):
    return (len(cells) >= 2
            and all(HEADER_CELL_RE.match(c) for c in cells)
            and len(set(cells)) == len(cells))


def table_kv(chunk, include_award_fields=True):
    """抽段内表格为 key-value 列表。支持 md 竖线表与 tab 分隔表；
    只保留 WANTED_KEYS 且非占位的值，返回 [(展示名, 值)]。
    一个连续表格块里允许多张子表（按表头特征行切分）。
    include_award_fields=False 时丢弃供应商/金额字段（卡片「采购结果」块已展示）。"""
    lines = chunk.splitlines()
    rows, i = [], 0
    while i < len(lines):
        line = lines[i]
        if '\t' in line:
            block = []
            while i < len(lines) and '\t' in lines[i]:
                block.append([c.strip() for c in lines[i].split('\t')])
                i += 1
            header = None
            for cells in block:
                if looks_header(cells):
                    header = cells
                    continue
                if header is None:                         # 块首没有表头特征行，兜底当表头
                    header = cells
                    continue
                rows.append((header, cells))
            continue
        if '|' in line and line.strip().startswith('|'):
            block = []
            while i < len(lines) and '|' in lines[i] and lines[i].strip().startswith('|'):
                if re.fullmatch(r'[|\s:\-]+', lines[i]):   # |---|---| 分隔行
                    i += 1
                    continue
                block.append([c.strip() for c in lines[i].strip().strip('|').split('|')])
                i += 1
            header = None
            for cells in block:
                if looks_header(cells):
                    header = cells
                    continue
                if header is None:
                    header = cells
                    continue
                rows.append((header, cells))
            continue
        i += 1
    out, seen = [], set()
    for header, values in rows:
        for k, v in zip(header, values):
            k = k.strip()
            if k not in WANTED_KEYS or is_placeholder(v):
                continue
            if not include_award_fields and k in AWARD_FIELDS:
                continue
            display = KEY_DISPLAY.get(k, k)
            v = v.strip().rstrip('。')
            if not v or (display, v) in seen:
                continue
            seen.add((display, v))
            out.append((display, v))
    return out


INVITE_RE = re.compile(r'(?P<sentence>[^\n。]{0,60}受[^\n。]{2,40}的委托，采用[^\n。]{2,14}方式组织采购[^\n。]{2,80}?)。')
FIELD_LINE_RE = re.compile(r'^\s*#*\s*(预算金额|合同履行期限|采购方式)\s*[：:]\s*(.{1,80}?)\s*$')


def project_digest(body, has_award=False):
    """定向挑段生成「项目内容」摘要，只做选取与字段化，不改写不补全；挑不出返回空串。

    中标/结果公告（九段式）→ 「四、主要标的信息」段的表格字段；
      has_award=False 时再补「三、采购结果」的供应商与金额（awardBlock 没覆盖的条目）。
    采购公告（招标文件式）→ 邀请句 + 预算金额/履约期限 + 标的表格。
    """
    secs = split_sections(body)
    by_kw = {}
    for name, chunk in secs:
        if name:
            for kw in ('主要标的', '采购结果', '项目概况', '项目内容及需求'):
                if kw in name and kw not in by_kw:
                    by_kw[kw] = chunk

    parts = []

    # —— 九段式：主要标的信息
    if '主要标的' in by_kw:
        parts.extend('%s：%s' % (k, v) for k, v in table_kv(by_kw['主要标的'],
                                                           include_award_fields=not has_award))
    # 个别公告缺「主要标的」段，品目表直接放在「采购结果」段里——
    # 即使 awardBlock 已覆盖（has_award=True）也抽品目字段，但跳过供应商/金额避免重复
    elif '采购结果' in by_kw:
        parts.extend('%s：%s' % (k, v) for k, v in table_kv(by_kw['采购结果'],
                                                           include_award_fields=not has_award))

    # —— 招标文件式：邀请句 + 预算/期限
    if not parts:
        m = INVITE_RE.search(body or '')
        if m:
            parts.append(m.group('sentence').strip())
        for line in (body or '').splitlines():
            fm = FIELD_LINE_RE.match(line)
            if fm and not is_placeholder(fm.group(2)):
                parts.append('%s：%s' % (fm.group(1), fm.group(2).strip().rstrip('。')))
        # 标的表格藏在「项目内容及需求」段
        if '项目内容及需求' in by_kw:
            parts.extend('%s：%s' % (k, v) for k, v in table_kv(by_kw['项目内容及需求']))

    if not parts:
        return ''
    text = '；'.join(parts)
    if len(text) > SUMMARY_LIMIT:
        text = clip(text, SUMMARY_LIMIT)
    return text


def summarize(body, intro, has_award):
    """摘要总入口：定向挑段优先，挑不出退回「第一段有实质内容的文字」，再退回 introduction。"""
    if body:
        s = project_digest(body, has_award=has_award) or first_meaningful(body)
        if s:
            return s
    return clip(clean_md(intro), SUMMARY_LIMIT) if intro else ''


def ms_to_iso(ms):
    try:
        return datetime.fromtimestamp(int(ms) / 1000, CST).isoformat(timespec='seconds')
    except Exception:
        return ''


def read_text(path):
    if path and os.path.exists(path):
        try:
            with open(path, encoding='utf-8') as f:
                return f.read()
        except Exception:
            return ''
    return ''


def parse_title(stem):
    """从文件名解析编号前缀（如「01-xxx」里的 01）。取不到返回空串，不做猜测。"""
    doc_no = ''
    m = re.match(r'^(\d{2,4})\s*[-.、]\s*', stem)
    if m:
        doc_no = m.group(1)
    return doc_no


# 公告类型后缀词：尾部反复剥，剥到没有为止（含「结果」「公告」被截断的形态）。
# 不写成一条嵌套可选组的正则——CPython re 对「外层组整体加 ? 再接 $」有怪癖：
# 组内靠前的可选组命中、靠后的可选组匹配空时会错误失配（((b)?(c))?$ 匹配不上 'b'）。
NOTICE_SUFFIX_WORD_RE = re.compile(
    r'(公开招标|竞争性磋商|竞争性谈判|邀请招标|询价|单一来源|中标|成交|结果|公告)$')


def strip_notice_suffix(t):
    for _ in range(4):
        t2 = NOTICE_SUFFIX_WORD_RE.sub('', t).strip(' 　-—_·.、')
        if t2 == t:
            return t
        t = t2
    return t


def project_name(title):
    """从公告标题确定性裁剪出「项目名称」：剥掉尾部文件后缀、编号括号、公告类型后缀。
    括号常被公告类型后缀压在后面（如「…（项目编号：xxx）中标公告」），
    所以「剥后缀 → 剥括号」循环到收敛。只做裁剪、不做推断；
    裁完剩余太短（<6 字）就整体放弃，返回空串（前端回退原标题）。"""
    t = (title or '').strip()
    if not t:
        return ''
    for _ in range(4):
        prev = t
        # 文件后缀（ima 标题可能带 .html / .docx 等）
        t = re.sub(r'\.(html?|docx?|pdf|md|markdown|txt|pptx?|xlsx?)$', '', t, flags=re.I)
        # 尾部下划线/空格接编号的截断形态（如「…结果公告_0835-260Z187」）
        t = re.sub(r'[\s_]+[0-9]{3,4}-[0-9A-Za-z\-]{4,}$', '', t)
        # 尾部公告类型后缀
        t = strip_notice_suffix(t)
        # 尾部「（项目编号：…）」，含被截断没闭合括号的形态
        t = re.sub(r'[（(]\s*项目编号[:：][^）)]*[）)]?\s*$', '', t)
        # 尾部纯编号括号（可能连排多个，如「（四次）（0724-2631Z3354387）」）
        p2 = None
        while p2 != t:
            p2 = t
            t = re.sub(r'[（(][0-9A-Za-z\-、,，/\s]{4,}[）)]\s*$', '', t)
        # 剩余若是没闭合的编号括号尾巴，剥掉
        t = re.sub(r'[（(][0-9A-Za-z\-]{4,}$', '', t).strip(' 　-—_·.、')
        if t == prev:
            break
    return t if len(t) >= 6 else ''


def load_json(path, fallback):
    if os.path.exists(path):
        try:
            with open(path, encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return fallback


def load_award_ids():
    """读 extract-award-info.py 产物，返回已有「采购结果」抽取数据的条目 id 集合。
    这些条目的卡片已单独展示供应商/金额，摘要不再重复，只挑「主要标的信息」。"""
    path = os.path.join(RAW_DIR, 'bids-award-info.json')
    ids = set()
    data = load_json(path, {})
    for k, v in (data or {}).items():
        if isinstance(v, dict) and v.get('packages'):
            ids.add(str(k))
    return ids


def load_source_urls():
    """读 link-bids-source.py 产物（gdgpo 反查映射）。"""
    return load_json(os.path.join(RAW_DIR, 'bids-source-urls.json'), {}) or {}


def load_legacy_winning():
    """读旧链路（parse_match.py 产物）的 winning 条目，
    供兼容继承 region/stage/school/projectCode/publishDate —— 页面地区/学段筛选继续工作。
    优先读 data/_raw/bidding-legacy.json（旧 bidding.json 的存档，切换链路时由 git 落一份）；
    没有再兜底读当前 public/data/bidding.json。旧链路退役后此函数可整体移除。"""
    for path in (os.path.join(RAW_DIR, 'bidding-legacy.json'),
                 os.path.join(OUT_DIR, 'bidding.json')):
        data = load_json(path, {})
        if not isinstance(data, dict):
            continue
        out = []
        for w in data.get('winning') or []:
            if isinstance(w, dict) and w.get('title'):
                out.append(w)
        if out:
            return out
    return []


def inherit_legacy(legacy, title):
    """按标题匹配旧 winning 条目：先精确（去扩展名相等），再 25 字前缀互相包含。"""
    if not legacy:
        return {}
    key = re.sub(r'\.(html?|docx?|pdf|md|txt)$', '', title or '', flags=re.I).strip()
    for w in legacy:
        if (w.get('title') or '').strip() == key:
            return w
    head = key[:25]
    if not head:
        return {}
    for w in legacy:
        t = (w.get('title') or '').strip()
        if t and (t[:25] == head or head in t or t in key):
            return w
    return {}


def load_items():
    path = os.path.join(RAW_DIR, 'ima-bids.json')
    raw = load_json(path, None)
    if not raw:
        return [], None

    award_ids = load_award_ids()
    source_urls = load_source_urls()
    legacy = load_legacy_winning()
    items = []
    for it in raw.get('items', []):
        raw_title = it.get('title', '')
        title = re.sub(r'\.(md|markdown|docx?|pdf|txt|pptx?|xlsx?)$', '', raw_title, flags=re.I)
        intro = it.get('introduction', '')

        content_file = it.get('contentFile', '') or ''
        cpath = os.path.join(RAW_DIR, 'bids-md', content_file) if content_file else ''
        body = read_text(cpath)
        # 摘要：定向挑「项目内容」段（主要标的/预算/履约期限），兜底取首段，再退 introduction
        summary = summarize(body, intro, has_award=str(it.get('id', '')) in award_ids)

        media_id = it.get('id', '')
        folder_path = it.get('folderPath') or []
        # 分组 = 一级文件夹名（「采购公告（广东省）」/「中标公告（广东省）》）；
        # 子文件夹里再嵌套时仍取最外层，与医疗站口径一致
        group = folder_path[0] if folder_path else ''
        item = {
            'id': media_id,
            'title': title,
            'projectName': project_name(title),
            'docNo': parse_title(title),
            'group': group,
            'summary': summary,
            'tags': [],
            'mediaType': it.get('mediaTypeName', ''),
            'mediaTypeIcon': it.get('mediaTypeIcon', ''),
            'fileSize': int(it.get('fileSize') or 0),
            'createdAt': ms_to_iso(it.get('createTime')),
            'parseState': PARSE_STATE.get(it.get('mediaState'), ''),
            'imaMediaId': media_id,
            'imaLink': '',
            'from': 'ima',
            'sourceKey': 'bids',
            'sourceLabel': KNOWLEDGE_BASE['label'],
            'contentFile': content_file,
            'contentPath': ('_raw/bids-md/' + content_file) if content_file else '',
            'hasContent': bool(body),
        }

        # —— 合并 gdgpo 反查链接（医疗站在 store.js 做的，本站无后端，生成期做）
        u = source_urls.get(media_id) or {}
        if u.get('matched'):
            item['sourceUrl'] = u.get('sourceUrl') or ''
            if u.get('projectName'):
                item['projectName'] = u['projectName']       # gdgpo 权威标题裁剪结果优先
            if u.get('purchaseUrl'):
                item['purchaseUrl'] = u['purchaseUrl']
            if u.get('purchaseZipUrl'):
                item['purchaseZipUrl'] = u['purchaseZipUrl']
            if u.get('purchaseZipName'):
                item['purchaseZipName'] = u['purchaseZipName']
            if u.get('openTenderCode'):
                item['projectCode'] = u['openTenderCode']
            if u.get('noticeTime'):
                item['publishDate'] = str(u['noticeTime'])[:10]

        # —— 合并「采购结果」抽取，并铺出页面模板字段（winningBidder/contractNo）
        info = load_json(os.path.join(RAW_DIR, 'bids-award-info.json'), {}).get(media_id) or {}
        packages = info.get('packages') if isinstance(info, dict) else None
        if packages:
            item['awardInfo'] = packages
            first = packages[0] or {}
            if first.get('supplier'):
                item['winningBidder'] = first['supplier']
            if first.get('amount'):
                item['winningAmount'] = first['amount']
            if first.get('pkg'):
                item['contractNo'] = '合同包' + str(first['pkg']) if not str(first['pkg']).startswith('合同包') else str(first['pkg'])

        # —— 兼容继承旧链路的页面增强字段（region/stage/school/projectCode/publishDate）
        old = inherit_legacy(legacy, title)
        for k in ('region', 'stage', 'school'):
            if old.get(k) and not item.get(k):
                item[k] = old[k]
        if old.get('projectCode') and not item.get('projectCode'):
            item['projectCode'] = old['projectCode']
        if old.get('publishDate') and not item.get('publishDate'):
            item['publishDate'] = old['publishDate']
        # 旧条目的附件（ima mediaId 清单）也带上，页面「N 份附件」计数继续可用
        if old.get('attachments'):
            item['attachments'] = old['attachments']

        items.append(item)
    return items, raw.get('knowledgeBase')


def main():
    items, kb_info = load_items()
    now = datetime.now(CST).isoformat(timespec='seconds')
    now_date = now[:10]

    # 中标（成交）结果口径与医疗站一致：group / 标题含「中标|结果|成交」
    def is_award(i):
        hay = (i.get('group') or '') + ' ' + (i.get('title') or '')
        return ('中标' in hay) or ('结果' in hay) or ('成交' in hay)

    payload = {
        'updatedAt': now,
        'updated': now_date,                       # 兼容旧字段（Bidding.vue 的 updated）
        'total': len(items),
        'counts': {
            'bids': len(items),
            'winning': sum(1 for i in items if is_award(i)),
            'withContent': sum(1 for i in items if i['hasContent']),
        },
        'items': items,
    }
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, 'bidding.json'), 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    # ------------------------------------------------------------------ 回执
    print('已生成: public/data/bidding.json')
    print('知识库「%s」(KB %s): %d 条（含正文 %d，其中中标 %d）' % (
        KNOWLEDGE_BASE['label'], KNOWLEDGE_BASE['kbId'], len(items),
        sum(1 for i in items if i['hasContent']), payload['counts']['winning']))
    if kb_info:
        print('快照知识库名: %s' % kb_info.get('name', ''))
    groups = {}
    for i in items:
        groups[i['group'] or '(顶层)'] = groups.get(i['group'] or '(顶层)', 0) + 1
    print('分组分布:')
    for g, c in sorted(groups.items(), key=lambda kv: -kv[1]):
        print('  · %s: %d' % (g, c))
    n_link = sum(1 for i in items if i.get('sourceUrl'))
    n_award = sum(1 for i in items if i.get('awardInfo'))
    print('反查链接 %d 条、采购结果抽取 %d 条' % (n_link, n_award))


if __name__ == '__main__':
    main()
