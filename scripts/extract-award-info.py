#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extract-award-info.py —— 从中标公告正文存档中抽取「采购结果」（中标供应商/金额）
取值逻辑照抄医疗平台知识库站点的同名脚本（2026-10-13），仅路径适配 policy-portal。

输入：public/data/bidding.json（识别中标条目）+ data/_raw/bids-md/<contentFile>（正文存档）
输出：data/_raw/bids-award-info.json   映射 bid id → {"packages":[{pkg,pkgName,supplier,amount}]}

只做原文抽取，不做任何推断；抽不到的条目不写入（前端回退展示摘要）。
幂等可重跑：ima 同步出新条目后再跑一次即可补齐。

正文存档有三种版式（均实测存在）：
  A. markdown 表格：|供应商名称|供应商地址|中标(成交)金额|（前后各一竖线）
  B. 制表符表格：  供应商名称\t供应商地址\t中标（成交）金额  → 数据行以 \t 分隔
  C. 行内键值：    中标（成交）供应商名称：xxx / 中标金额：xxx
金额可能是金额（…元）也可能是 折扣率：xx% / 费率：xx%，原样保留。
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BIDS_JSON = os.path.join(ROOT, "public", "data", "bidding.json")
MD_DIR = os.path.join(ROOT, "data", "_raw", "bids-md")
OUT_JSON = os.path.join(ROOT, "data", "_raw", "bids-award-info.json")

SEC_START = re.compile(r"采购结果")
SEC_END = re.compile(r"主要标的|评审专家|代理服务收|公告期限|其他补充|凡对本次|联络?方式|^#{1,4}\s*[一二三四五六七八九十]、")
PKG_LINE = re.compile(r"合同包\s*(\d+)\s*[（(]([^）)]*)[）)]\s*[:：]?")
MD_ROW = re.compile(r"^\s*\|(.+)\|\s*$")
KEY_SUP = re.compile(r"中标\s*[（(]\s*成交\s*[)）]\s*供应商名称\s*[:：]\s*(.+)")
HDR_SUP = re.compile(r"供应商名称")
HDR_AMT = re.compile(r"金额")

def clean(s):
    return re.sub(r"\s+", " ", (s or "").strip()).strip("　\t|")

def parse_section(sec):
    """在采购结果段内抽 [(pkg, pkgName, supplier, amount)]，三种版式统一处理。"""
    out = []
    lines = sec.split("\n")
    cur_pkg, cur_name = "", ""
    i = 0
    while i < len(lines):
        ln = lines[i]
        mp = PKG_LINE.search(ln)
        if mp:
            cur_pkg, cur_name = mp.group(1), clean(mp.group(2))

        # 版式 A：markdown 表格行
        mm = MD_ROW.match(ln)
        if mm:
            cells = [clean(c) for c in mm.group(1).split("|")]
            if any(HDR_SUP.search(c or "") for c in cells) and any(HDR_AMT.search(c or "") for c in cells):
                i += 1
                while i < len(lines):
                    m2 = MD_ROW.match(lines[i])
                    if not m2:
                        break
                    c2 = [clean(c) for c in m2.group(1).split("|")]
                    joined = "".join(c2)
                    if set(joined) <= set("-—"):        # 跳过 |---|---| 分隔行
                        i += 1
                        continue
                    # 列数对不齐的脏行（如孤立的地址残片）直接丢弃
                    if len(c2) >= 2 and c2[0]:
                        sup = c2[0]
                        amt = c2[-1] if len(c2) >= 3 else ""
                        out.append({"pkg": cur_pkg, "pkgName": cur_name, "supplier": sup, "amount": amt})
                    i += 1
                continue

        # 版式 B：制表符表格 —— 表头行含「供应商名称」「金额」，其后若干 \t 分隔数据行
        if "\t" in ln and HDR_SUP.search(ln) and HDR_AMT.search(ln):
            ncols = ln.count("\t") + 1
            i += 1
            while i < len(lines):
                nxt = lines[i]
                if not nxt.strip() or "\t" not in nxt:
                    break
                c2 = [clean(c) for c in nxt.split("\t")]
                if SEC_END.search(c2[0]) and len(c2) < ncols:
                    break
                if c2 and c2[0]:
                    sup = c2[0]
                    amt = c2[-1] if len(c2) >= 3 else ""
                    out.append({"pkg": cur_pkg, "pkgName": cur_name, "supplier": sup, "amount": amt})
                i += 1
            continue

        # 版式 C：行内键值
        ms = KEY_SUP.search(ln)
        if ms:
            sup = clean(ms.group(1))
            amt = ""
            for j in range(i + 1, min(i + 4, len(lines))):
                ma = re.search(r"(?:中标|成交)金额\s*[:：]\s*(.+)", lines[j])
                if ma:
                    amt = clean(ma.group(1))
                    break
            out.append({"pkg": cur_pkg, "pkgName": cur_name, "supplier": sup, "amount": amt})

        i += 1
    return out

def extract(txt):
    """「采购结果」可能在文中出现多次（套话「对采购结果有异议」/正文重复），
    逐个出现位置尝试切段，取第一个能抽到数据的。"""
    for m in SEC_START.finditer(txt):
        tail = txt[m.start() + len("采购结果"):]
        em = SEC_END.search(tail)
        sec = tail[:em.start()] if em else tail
        rows = parse_section(sec)
        if rows:
            return rows
    return []

def main():
    data = json.load(open(BIDS_JSON))
    items = data["items"] if isinstance(data, dict) else data
    awards = [i for i in items if i.get("group") == "中标公告（广东省）"]

    out = {}
    ok = miss = 0
    for it in awards:
        cf = it.get("contentFile")
        p = os.path.join(MD_DIR, cf) if cf else None
        if not p or not os.path.exists(p):
            miss += 1
            continue
        txt = open(p, encoding="utf-8", errors="replace").read()
        rows = extract(txt)
        # 清洗：供应商非空、非表头残留
        rows = [r for r in rows if r["supplier"] and not HDR_SUP.search(r["supplier"])]
        if rows:
            out[it["id"]] = {"packages": rows}
            ok += 1
        else:
            miss += 1
            print(f"MISS {it['title'][:48]}")

    json.dump(out, open(OUT_JSON, "w"), ensure_ascii=False, indent=1)
    print(f"\n=== 抽到采购结果 {ok} / {len(awards)}，未抽到 {miss} ===")
    print(f"已写入 {OUT_JSON}")

if __name__ == "__main__":
    main()
