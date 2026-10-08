#!/usr/bin/env bash
# 云端 curl vs Python 对比测试政府采购网
set -e

BASE="https://gdgpo.czt.gd.gov.cn/gpcms/rest/web/v2/info/selectInfoForIndex"
COMMON="siteId=cd64e06a-21a7-4620-aebc-0576bab7e07a&title=%E5%AD%A6%E6%A0%A1&operationStartTime=2026-10-01%2000%3A00%3A00&operationEndTime=2026-10-08%2023%3A59%3A59&currPage=1&pageSize=3"

echo "=================================================="
echo " GitHub Actions 云端 → 政府采购网 连通性诊断"
echo " curl vs Python urllib 对比"
echo "=================================================="

echo ""
echo "【curl 测试】"
for nt in 00101 00102; do
  URL="${BASE}?noticeType=${nt}&${COMMON}"
  echo ""
  echo "  noticeType=${nt}:"
  for attempt in 1 2 3; do
    HTTP_CODE=$(curl -s -o /tmp/gpo_${nt}.json -w "%{http_code}" \
      -H "Accept: application/json" \
      -H "Cookie: regionCode=440001" \
      -H "Referer: https://gdgpo.czt.gd.gov.cn/maincms-web/noticeInformationGd" \
      -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36" \
      --connect-timeout 20 --max-time 30 \
      "${URL}" 2>/dev/null)
    if [ "$HTTP_CODE" = "200" ]; then
      COUNT=$(python3 -c "
import json
d = json.load(open('/tmp/gpo_${nt}.json'))
items = d.get('data',{}).get('list',d.get('data',{}).get('rows',[]))
if not items and isinstance(d.get('data'), list): items = d['data']
print(len(items))" 2>/dev/null || echo "parse_err")
      echo "    ✅ curl 第${attempt}次: HTTP 200 | ${COUNT} 条"
      break
    else
      echo "    ❌ curl 第${attempt}次: HTTP ${HTTP_CODE} | 超时/阻断"
    fi
    [ "$attempt" -lt 3 ] && sleep 2
  done
done

echo ""
echo "【Python urllib 测试】"
python3 scripts/cloud_gpo_test.py 2>&1 | tail -25 || echo "Python 测试也失败了"

echo ""
echo "=================================================="
echo " 诊断完毕"
echo "=================================================="
