#!/bin/bash
# 守护进程管理：start / stop / restart / status / run-now / log
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

ACTION=${1:-status}

case "$ACTION" in
  start)   node scripts/scheduler.js --daemon ;;
  stop)    node scripts/scheduler.js --stop ;;
  restart) node scripts/scheduler.js --stop 2>/dev/null; sleep 1; node scripts/scheduler.js --daemon ;;
  status)  node scripts/scheduler.js --status ;;
  run)     node scripts/scheduler.js --run-now ;;
  log)     tail -f "$ROOT/logs/scheduler.log" ;;
  *)
    echo "用法: $0 {start|stop|restart|status|run|log}"
    exit 1
    ;;
esac
