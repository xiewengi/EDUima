#!/bin/bash
# 一次性：安装并加载招投标数据同步的 launchd 任务（WorkBuddy 沙箱进程创建的文件
# 带 com.apple.provenance 标，launchd 拒收，故由 Terminal 执行本脚本完成安装）
set -e
cp /Users/yyym/Desktop/IMA/policy-portal/scripts/com.ima.policy-sync.plist ~/Library/LaunchAgents/com.ima.policy-sync.plist
launchctl bootout gui/$(id -u)/com.ima.policy-sync 2>/dev/null || true
launchctl load ~/Library/LaunchAgents/com.ima.policy-sync.plist
echo "─── 安装结果 ───"
launchctl list | grep ima
echo "SETUP-DONE-OK"
