#!/bin/bash
# 数据同步一键入口 — 带日志、错误处理、锁文件防重入
# 用法: bash scripts/run.sh [--force] [--dry-run] [--skip-download]
#
# 手动跑一次: cd policy-portal && bash scripts/run.sh
# 定时跑(launchd已配置): 每天凌晨 3:00 自动执行

set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOCK="$ROOT/.sync_lock"
LOG="$ROOT/logs/run.log"

# 日志
log() {
  local ts
  ts=$(date '+%Y-%m-%d %H:%M:%S')
  echo "[$ts] $*" | tee -a "$LOG"
}

# 防重入
if [ -f "$LOCK" ]; then
  log "⚠️  已有同步进程在运行 (PID: $(cat "$LOCK"))，跳过"
  exit 0
fi
echo $$ > "$LOCK"
trap 'rm -f "$LOCK"' EXIT

cd "$ROOT"

# 依赖检查
if ! command -v node &>/dev/null; then
  log "❌ node 未找到"
  exit 1
fi
if ! command -v python3 &>/dev/null; then
  log "❌ python3 未找到"
  exit 1
fi

# 安装 Python 依赖（首次）
if ! python3 -c "import docx, pypdf" 2>/dev/null; then
  log "📦 安装 Python 依赖..."
  pip3 install python-docx pypdf -q 2>&1 | tee -a "$LOG"
fi

log "🚀 开始同步 (参数: $*)"

# 执行
node scripts/sync.js "$@" 2>&1 | tee -a "$LOG"
RC=${PIPESTATUS[0]}

if [ $RC -eq 0 ]; then
  log "✅ 政策数据同步完成"
else
  log "❌ 同步失败 (exit code: $RC)"
  exit $RC
fi

# ── 招投标数据（bidding.json）新链路（2026-10-13 切换，取值逻辑对齐医疗站）──
# fetch-bids.cjs 需要本机 WorkBuddy 的 ima 凭据（~/.workbuddy/connectors），
# GitHub Actions 上没有 → fetch 失败不阻断，用仓库里已提交的 data/_raw 快照继续跑后三步。
log "📥 拉取 ima 招投标快照与正文 (fetch-bids.cjs)..."
node scripts/fetch-bids.cjs 2>&1 | tee -a "$LOG" || log "⚠️ fetch-bids 失败（本地无 ima 凭据时正常），用既有快照继续"

gen_bids() { python3 scripts/gen-bids.py 2>&1 | tee -a "$LOG"; }

log "🧩 字段化生成 bidding.json (gen-bids.py)..."
gen_bids

log "🏆 抽取采购结果 (extract-award-info.py)..."
python3 scripts/extract-award-info.py 2>&1 | tee -a "$LOG" || log "⚠️ 采购结果抽取失败，不阻断"

log "🔗 反查政采网原文链接 (link-bids-source.py)..."
python3 scripts/link-bids-source.py 2>&1 | tee -a "$LOG" || log "⚠️ 原文链接反查失败，不阻断，明日自动重试"

log "🔁 重跑 gen-bids.py 合并链接与采购结果..."
gen_bids

# ── 重磅展会（exhibition.json）：jyb.cn + 教育装备采购网，失败不阻断 ──
log "🎪 抓取重磅展会资讯 (fetch-exhibition.py)..."
python3 scripts/fetch-exhibition.py 2>&1 | tee -a "$LOG" || log "⚠️ 展会抓取失败，不阻断，用仓库既有数据"


# ── 重磅展会（exhibition.json）：jyb.cn + 教育装备采购网，失败不阻断 ──
log "🎪 抓取重磅展会资讯 (fetch-exhibition.py)..."
python3 scripts/fetch-exhibition.py 2>&1 | tee -a "$LOG" || log "⚠️ 展会抓取失败，不阻断，用仓库既有数据"

