#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
link_bidding_source.py —— 给 policy-portal 的 public/data/bidding.json 中标公告
补广东省政府采购网（gdgpo）原文链接。

做法：
  1. 读 public/data/bidding.json 的 winning 数组；
  2. 用条目的 projectCode / title 调 gdgpo 列表接口 selectInfoForIndex
     （noticeType=00102 中标/成交结果）反查；
  3. 命中后把 sourceUrl 直接写回该 winning 条目（其余键与 procurement 不动）。

说明：
  - 网络走 curl 子进程 + --noproxy（本机沙箱下 python 直连被代理劫持）；
  - 脚本幂等：已有 sourceUrl 的条目跳过，可反复重跑补新条目；
  - 前端 Bidding.vue 渲染「政府采购网原文」外链。
"""
import json, os, re, subprocess, sys, time, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BIDDING_JSON = os.path.join(ROOT, "public", "data", "bidding.json")

BASE = "https://gdgpo.czt.gd.gov.cn"
SITE_HOST = "gdgpo.czt.gd.gov.cn"
# 海外 runner（GitHub Actions）直连 gdgpo 会超时——每日爬虫同款 Cloudflare Workers 反代兜底
WORKER_BASE = "https://broken-wildflower-accf.304997019.workers.dev"
SITE_ID_FALLBACK = "cd64e06a-21a7-4620-aebc-0576bab7e07a"  # 与 gd_winning_ima_sync.py 一致
# 频道 ID：来自 gdgpo-award-ledger skill 实测可用的取值，别改
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
    故兜底时丢掉 /gpcms/... 路径、只保留查询串。
    """
    global _direct_ok
    last = None
    if _direct_ok:
        try:
            return curl_json(url)
        except Exception as direct_err:
            _direct_ok = False
            last = direct_err
    if url.startswith(BASE) and "?" in url:
        alt = WORKER_BASE + "?" + url.split("?", 1)[1]
        try:
            return curl_json(alt)
        except Exception as proxy_err:
            raise RuntimeError(f"直连失败({last}) 且反代失败({proxy_err})")
    raise RuntimeError(f"直连失败({last}) 且 URL 不支持反代兜底: {url[:80]}")

_site = None
def site_id():
    global _site
    if not _site:
        try:
            _site = fetch_json(f"{BASE}/gpcms/rest/web/v2/index/getDeploymentSiteId?domain={SITE_HOST}")["data"]["id"]
        except Exception:
            # siteId 实践中恒定，直连+反代都挂不成就用爬虫同款兜底值
            _site = SITE_ID_FALLBACK
    return _site

def clean_title(title):
    t = re.sub(r"\.(html|docx?|pdf).*$", "", title or "")
    t = re.sub(r"[（(].*$", "", t)
    return t.strip()[:30]

def query(code, kw):
    url = (f"{BASE}/gpcms/rest/web/v2/info/selectInfoForIndex?"
           + urllib.parse.urlencode({
               "title": kw, "siteId": site_id(), "channel": CHANNEL,
               "currPage": 1, "pageSize": 10,
               "noticeType": "00102", "regionCode": "", "cityOrArea": "",
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
            if (r.get("openTenderCode") or "").strip() == code:
                return r
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

def main():
    with open(BIDDING_JSON, encoding="utf-8") as f:
        data = json.load(f)
    winning = data.get("winning") or []

    hit = miss = skip = 0
    for it in winning:
        if it.get("sourceUrl"):
            skip += 1
            continue
        code = (it.get("projectCode") or "").strip()
        kw = clean_title(it.get("title"))
        try:
            rows = query(code, kw)
        except Exception as e:
            print(f"ERR {it.get('title','')[:30]} → {e}")
            miss += 1
            time.sleep(1)
            continue
        r = pick_row(rows, code, kw)
        if r:
            it["sourceUrl"] = detail_url(r)
            it["gdgpoOpenTenderCode"] = r.get("openTenderCode") or code
            hit += 1
            print(f"HIT {code!r:>22} → {r.get('title','')[:40]}")
        else:
            miss += 1
            print(f"MISS {code!r:>22} {it.get('title','')[:44]}")
        time.sleep(0.6)

    with open(BIDDING_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print(f"\n=== 命中 {hit} / 未中 {miss} / 跳过已有 {skip}（共 {len(winning)} 条中标） ===")
    print(f"已写回 {BIDDING_JSON}")

if __name__ == "__main__":
    main()
