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
  log "✅ 同步完成"
else
  log "❌ 同步失败 (exit code: $RC)"
  exit $RC
fi

# 政采网原文链接反查：sync.js/parse_match.py 每次会重新生成 bidding.json，
# sourceUrl 会丢，必须跟一脚本回写（幂等，已有链接的条目自动跳过）。
# 失败不阻断部署（线上数据仍为最新，链接明日重试自动补回）。
log "🔗 反查政采网原文链接 (link_bidding_source.py)..."
python3 scripts/link_bidding_source.py 2>&1 | tee -a "$LOG"
RC2=${PIPESTATUS[0]}
if [ $RC2 -eq 0 ]; then
  log "✅ 原文链接回写完成"
else
  log "⚠️ 原文链接反查失败 (exit code: $RC2)，不阻断本次部署，明日自动重试"
fi
