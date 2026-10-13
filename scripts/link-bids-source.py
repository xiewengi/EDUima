#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
link-bids-source.py —— 给 bidding.json 里的中标公告反查广东省政府采购网（gdgpo）原文链接
取值逻辑照抄医疗平台知识库站点的同名脚本（2026-10-13），仅两处适配：
  1. 输入/输出路径改为 policy-portal 的 public/data/bidding.json 与 data/_raw/；
  2. 网络走「直连优先 + Cloudflare Workers 反代兜底」（GitHub Actions 海外 runner 直连
     gdgpo 会超时，反代只映射 selectInfoForIndex；getInfoById 详情接口反代不可达）。

做法：
  1. 从 ima 条目标题提取项目编号（openTenderCode）与标题关键词；
  2. 调 gdgpo 列表接口 selectInfoForIndex（noticeType=00102 中标/成交结果）反查；
  3. 命中后拼 detail_url，写入 data/_raw/bids-source-urls.json（id → 链接映射）；
  4. 已匹配条目：用 gdgpo 权威标题裁剪出「项目名称」（projectName，复用 gen-bids.py）；
  5. 已匹配条目：按同一 openTenderCode 以 noticeType=00101 反查对应采购公告（purchaseUrl）。

说明：
  - 脚本幂等：已有映射且 matched=true 的条目跳过，可反复重跑补新条目；
  - gen-bids.py 生成期把映射合并进条目（sourceUrl / purchaseUrl / purchaseZipUrl 等字段）。
"""
import json, re, subprocess, sys, time, urllib.parse, os, importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BIDS_JSON = os.path.join(ROOT, "public", "data", "bidding.json")
MAP_JSON = os.path.join(ROOT, "data", "_raw", "bids-source-urls.json")

# 复用 gen-bids.py 的 project_name()（文件名带连字符不能直接 import，走 importlib）
_spec = importlib.util.spec_from_file_location("gen_bids", os.path.join(HERE, "gen-bids.py"))
_gen_bids = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_gen_bids)
project_name = _gen_bids.project_name

BASE = "https://gdgpo.czt.gd.gov.cn"
SITE_HOST = "gdgpo.czt.gd.gov.cn"
# 海外 runner（GitHub Actions）直连 gdgpo 会超时——每日爬虫同款 Cloudflare Workers 反代兜底
WORKER_BASE = "https://broken-wildflower-accf.304997019.workers.dev"
SITE_ID_FALLBACK = "cd64e06a-21a7-4620-aebc-0576bab7e07a"  # 与 gd_winning_ima_sync.py 一致
# 频道 ID（省级采购 + 深圳专区？）：来自 gdgpo-award-ledger skill 实测可用的取值，别改
CHANNEL = ("fca71be5-fc0c-45db-96af-f513e9abda9d,"
           "95ff31f3-a1af-4bc4-b1a2-54c894476193")
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")

def curl_json(url):
    p = subprocess.run(
        ["curl", "-sS", "--noproxy", "*", "-m", "20", "-H", f"User-Agent: {UA}",
         "-H", "Referer: https://gdgpo.czt.gd.gov.cn/maincms-web/noticeInformationGd", url],
        capture_output=True, text=True, timeout=30)
    if p.returncode != 0:
        raise RuntimeError(f"curl exit {p.returncode}: {p.stderr[:120]}")
    return json.loads(p.stdout)

_direct_ok = True  # 直连一次失败后置 False，后续直接走反代，省掉每条 20s 超时

def fetch_json(url):
    """直连优先（本机可用）；超时/连不上时换 Workers 反代（Actions 海外 runner 用）。

    反代只映射根路径 → gdgpo selectInfoForIndex（每日爬虫同款拼法 WORKER?params），
    故兜底时丢掉 /gpcms/... 路径、只保留查询串。getInfoById（详情）反代不可达，
    直连不可用时 zip 直链补充环节只能放弃，不做编造。"""
    global _direct_ok
    if _direct_ok:
        try:
            return curl_json(url)
        except Exception:
            _direct_ok = False
    if "/selectInfoForIndex" in url:
        q = urllib.parse.urlparse(url).query
        return curl_json(f"{WORKER_BASE}?{q}")
    raise RuntimeError("直连不可用且该接口无反代兜底")

_site = None
def site_id():
    global _site
    if not _site:
        try:
            _site = fetch_json(f"{BASE}/gpcms/rest/web/v2/index/getDeploymentSiteId?domain={SITE_HOST}")["data"]["id"]
        except Exception:
            _site = SITE_ID_FALLBACK
    return _site

def extract_code(title):
    m = re.search(r"项目编号[:：]\s*([A-Za-z0-9\-]+)", title)
    if m: return m.group(1)
    m = re.search(r"[（(]([0-9]{3,4}-[0-9A-Za-z\-]+)[）)]", title)
    if m: return m.group(1)
    m = re.search(r"[（(]([A-Z]{2,}[0-9][0-9A-Za-z\-]*)[）)]", title)
    if m: return m.group(1)
    # 标题尾部形态：「…结果公告_0835-260Z187.html」（ima 入库时标题被截断，编号只有前缀）
    m = re.search(r"[ _]([0-9]{4}-[0-9A-Z]{3,}[0-9]+)(?:\.(?:html|docx?|pdf))?$", title)
    if m: return m.group(1)
    return ""

def clean_title(title):
    t = re.sub(r"\.(html|docx?|pdf).*$", "", title)
    t = re.sub(r"[（(].*$", "", t)
    return t.strip()[:30]

def query(code, kw, notice_type="00102"):
    url = (f"{BASE}/gpcms/rest/web/v2/info/selectInfoForIndex?"
           + urllib.parse.urlencode({
               "title": kw, "siteId": site_id(), "channel": CHANNEL,
               "currPage": 1, "pageSize": 10,
               "noticeType": notice_type, "regionCode": "", "cityOrArea": "",
               "purchaseManner": "!9", "openTenderCode": code, "purchaser": "",
               "agency": "", "purchaseNature": "",
               "operationStartTime": "", "operationEndTime": "",
               "verifyCode": "", "subChannel": "false"}))
    d = fetch_json(url)
    return (d.get("data") or {}).get("rows") or []

def pick_row(rows, code, kw):
    """优先 openTenderCode 精确相等（编号截断时用前缀匹配）；否则标题包含关键词。"""
    if code:
        for r in rows:
            c = (r.get("openTenderCode") or "").strip()
            if c == code:
                return r
        # ima 标题截断导致编号只有前缀（≥8 位才启用，避免误配）
        if len(code) >= 8:
            for r in rows:
                if (r.get("openTenderCode") or "").strip().startswith(code):
                    return r
    k = kw[:12]
    for r in rows:
        if k and k in (r.get("title") or ""):
            return r
    return rows[0] if len(rows) == 1 else None

def detail_url(r):
    return (f"{BASE}/maincms-web/noticeGd?type=notice&id={r.get('id')}"
            f"&channel={r.get('channel')}"
            f"&openTenderCode={urllib.parse.quote(r.get('openTenderCode') or '无')}"
            f"&channelName={urllib.parse.quote(r.get('channelName') or '')}")


def detail_atts(nid):
    """调 gdgpo 详情接口，返回附件清单 attchList（含 fileName/fileExt/fileUrl 直链）。"""
    url = f"{BASE}/gpcms/rest/web/v2/info/getInfoById?id={nid}&siteId={site_id()}"
    d = curl_json(url)
    return (d.get("data") or {}).get("attchList") or []


def pick_tender_zip(atts):
    """从附件清单里挑「招标文件 zip」：优先文件名含 招标文件/磋商/谈判/采购文件 的 zip，
    否则取第一个 .zip。没有 zip 返回 None（pdf/xlsx 等散件不收，口径只给主件）。"""
    zips = [a for a in atts if (a.get("fileExt") or "").lower() == ".zip" and a.get("fileUrl")]
    if not zips:
        return None
    for a in zips:
        name = a.get("fileName") or ""
        if any(k in name for k in ("招标文件", "采购文件", "磋商文件", "谈判文件", "询价文件")):
            return a
    return zips[0]

def main():
    data = json.load(open(BIDS_JSON))
    items = data["items"] if isinstance(data, dict) else data
    awards = [i for i in items if i.get("group") == "中标公告（广东省）"]

    mapping = {}
    if os.path.exists(MAP_JSON):
        try: mapping = json.load(open(MAP_JSON))
        except Exception: mapping = {}

    hit = miss = skip = 0
    for it in awards:
        bid = it["id"]
        old = mapping.get(bid)
        if old and old.get("matched"):
            skip += 1
            continue
        code = extract_code(it["title"])
        kw = clean_title(it["title"])
        try:
            rows = query(code, kw)
        except Exception as e:
            print(f"ERR {it['title'][:30]} → {e}")
            miss += 1
            time.sleep(1)
            continue
        r = pick_row(rows, code, kw)
        if r:
            mapping[bid] = {
                "matched": True, "sourceUrl": detail_url(r),
                "gdgpoId": r.get("id"), "openTenderCode": r.get("openTenderCode") or code,
                "gdgpoTitle": r.get("title") or "",
                "noticeTime": r.get("noticeTime") or "",
            }
            hit += 1
            print(f"HIT {code!r:>20} → {r.get('title','')[:36]}")
        else:
            mapping[bid] = {"matched": False, "openTenderCode": code, "triedKw": kw}
            miss += 1
            print(f"MISS {code!r:>20} {it['title'][:44]}")
        time.sleep(0.6)

    print(f"\n=== 原文链接：命中 {hit} / 未中 {miss} / 跳过已匹配 {skip}（共 {len(awards)} 条中标） ===")

    # ------------------------------------------------ 补充 1：项目名称
    # 已匹配条目用 gdgpo 权威标题裁剪；未匹配条目用 ima 标题裁剪。裁不出留空，不编造。
    pn = 0
    for it in awards:
        m = mapping.get(it["id"])
        if not m or not m.get("matched"):
            continue
        if m.get("projectName"):
            continue
        name = project_name(m.get("gdgpoTitle") or "") or project_name(it["title"] or "")
        if name:
            m["projectName"] = name
            pn += 1
    print(f"=== 项目名称：本轮补 {pn} 条 ===")

    # ------------------------------------------------ 补充 2：采购公告反查
    # 同一 openTenderCode 在 gdgpo 以 noticeType=00101（采购公告）再查一次；
    # 只查已匹配条目（编号可信），查不到留空，绝不编链接。幂等：已有 purchaseUrl 的跳过。
    p_hit = p_miss = p_skip = 0
    for it in awards:
        m = mapping.get(it["id"])
        if not m or not m.get("matched"):
            continue
        if m.get("purchaseUrl"):
            p_skip += 1
            continue
        code = (m.get("openTenderCode") or "").strip()
        if not code:
            p_miss += 1
            continue
        # ⚠️ 关键词必须用「项目名称」：gdgpo 标题检索是 AND 匹配，拿中标公告标题
        # （以「结果公告」结尾）去搜采购公告（标题是「招标公告」结尾）必然 0 条 —— 2026-10-13 医疗站实测。
        kw = (m.get("projectName")
              or project_name(m.get("gdgpoTitle") or it["title"])
              or clean_title(m.get("gdgpoTitle") or it["title"]))
        try:
            rows = query(code, kw, notice_type="00101")
        except Exception as e:
            print(f"P-ERR {code!r:>20} → {e}")
            p_miss += 1
            time.sleep(1)
            continue
        r = pick_row(rows, code, kw)
        if r:
            m["purchaseUrl"] = detail_url(r)
            m["purchaseGdgpoTitle"] = r.get("title") or ""
            m["gdgpoIdP"] = r.get("id") or ""     # 采购公告 gdgpo id，补充 3 取附件要用
            p_hit += 1
            print(f"P-HIT {code!r:>20} → {r.get('title','')[:36]}")
        else:
            p_miss += 1
            print(f"P-MISS {code!r:>20} {kw[:36]}")
        time.sleep(0.6)

    print(f"=== 采购公告：命中 {p_hit} / 未中 {p_miss} / 跳过已有 {p_skip} ===")

    # ------------------------------------------------ 补充 3：采购文件 zip 直链
    # 已匹配采购公告的条目，调详情接口取 attchList，挑「招标文件 zip」直链存 purchaseZipUrl。
    # 幂等：已有 purchaseZipUrl（含"确认无 zip"标记）的跳过。
    z_hit = z_nozip = z_err = z_skip = 0
    for it in awards:
        m = mapping.get(it["id"])
        if not m or not m.get("purchaseUrl"):
            continue
        if "purchaseZipUrl" in m:
            z_skip += 1
            continue
        nid = m.get("gdgpoIdP") or ""
        if not nid:
            # 老映射没存采购公告 id：从 purchaseUrl 的 query 里解析兜底
            try:
                nid = (urllib.parse.parse_qs(urllib.parse.urlparse(m["purchaseUrl"]).query)
                       .get("id") or [""])[0]
            except Exception:
                nid = ""
        if not nid:
            z_err += 1
            continue
        try:
            a = pick_tender_zip(detail_atts(nid))
        except Exception as e:
            print(f"Z-ERR {(m.get('openTenderCode') or '')[:22]} → {e}")
            z_err += 1
            time.sleep(1)
            continue
        if a:
            m["purchaseZipUrl"] = a["fileUrl"]
            m["purchaseZipName"] = a.get("fileName") or ""
            z_hit += 1
            print(f"Z-HIT {(m.get('openTenderCode') or '')[:22]} → {(a.get('fileName') or '')[:44]}")
        else:
            m["purchaseZipUrl"] = ""          # 详情正常但没有 zip：记空串防重查
            z_nozip += 1
            print(f"Z-NONE {(m.get('openTenderCode') or '')[:22]} 无 zip 附件")
        time.sleep(0.5)

    print(f"=== 采购文件 zip：命中 {z_hit} / 无 zip {z_nozip} / 失败 {z_err} / 跳过已有 {z_skip} ===")

    os.makedirs(os.path.dirname(MAP_JSON), exist_ok=True)
    json.dump(mapping, open(MAP_JSON, "w"), ensure_ascii=False, indent=1)
    print(f"\n映射已写入 {MAP_JSON}")

if __name__ == "__main__":
    main()
