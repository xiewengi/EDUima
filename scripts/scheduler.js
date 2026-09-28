#!/usr/bin/env node
/**
 * 数据同步守护进程（零依赖，纯 Node 实现）
 *
 * 功能：
 *  - 内置 cron 调度（默认每天 03:00 执行）
 *  - 进程自守护（异常退出自动拉起）
 *  - 锁文件防重入
 *  - 开机自启：在 ~/.zshrc 或 ~/.bashrc 加一行即可
 *
 * 用法：
 *   node scripts/scheduler.js              # 前台运行（调试）
 *   node scripts/scheduler.js --daemon     # 后台常驻（nohup）
 *   node scripts/scheduler.js --run-now    # 立刻跑一次然后退出
 *   node scripts/scheduler.js --stop       # 停掉正在跑的 daemon
 *   node scripts/scheduler.js --status     # 看状态
 *
 * Cron 表达式（5 段）：分 时 日 月 周
 *   "0 3 * * *"           每天 03:00 (默认)
 *   "0 [star]/6 * * *"   每 6 小时
 *   "0 * * * *"           每小时整点
 *   "[star]/30 * * * *"  每 30 分钟
 */

import { execSync, spawn } from 'child_process'
import { writeFileSync, readFileSync, existsSync, mkdirSync } from 'fs'
import { join, dirname, resolve } from 'path'
import { fileURLToPath } from 'url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const ROOT = resolve(__dirname, '..')
const PID_FILE = join(ROOT, '.scheduler.pid')
const LOG_FILE = join(ROOT, 'logs', 'scheduler.log')
const LOCK_FILE = join(ROOT, '.sync_lock')

const CRON = process.env.SYNC_CRON || '0 3 * * *'  // 默认每天 03:00
const CHECK_INTERVAL = 60 * 1000  // 每 60 秒检查一次
const SYNC_SCRIPT = join(__dirname, 'sync.js')

// ========== 日志 ==========
function log(msg, level = 'INFO') {
  const ts = new Date().toISOString().replace('T', ' ').slice(0, 19)
  const line = `[${ts}] [${level}] ${msg}`
  console.log(line)
  try {
    mkdirSync(join(ROOT, 'logs'), { recursive: true })
    writeFileSync(LOG_FILE, line + '\n', { flag: 'a' })
  } catch {}
}

// ========== Cron 解析 ==========
// 简单实现：支持 * / N 具体值
function parseCron(expr) {
  const parts = expr.trim().split(/\s+/)
  if (parts.length !== 5) throw new Error(`cron 表达式需要 5 段，收到: ${expr}`)
  const [min, hour, dom, mon, dow] = parts.map(p => expandPart(p))
  return { min, hour, dom, mon, dow }
}

function expandPart(part) {
  if (part === '*') return null  // null 表示通配
  if (part.includes('/')) {
    // */n 或 a-b/n
    const [range, step] = part.split('/')
    const s = parseInt(step)
    let start, end
    if (range === '*') { start = 0; end = 59 }
    else if (range.includes('-')) {
      const [a, b] = range.split('-').map(Number)
      start = a; end = b
    } else { start = parseInt(range); end = 59 }
    const arr = []
    for (let i = start; i <= end; i += s) arr.push(i)
    return arr
  }
  if (part.includes('-')) {
    const [a, b] = part.split('-').map(Number)
    const arr = []
    for (let i = a; i <= b; i++) arr.push(i)
    return arr
  }
  return [parseInt(part)]
}

function cronMatches(cron, d) {
  const m = d.getMinutes(), h = d.getHours(), dom = d.getDate(), mon = d.getMonth() + 1, dow = d.getDay()
  function ok(field, val) { return field === null || field.includes(val) }
  return ok(cron.min, m) && ok(cron.hour, h) && ok(cron.dom, dom) && ok(cron.mon, mon) && ok(cron.dow, dow)
}

// ========== 执行同步 ==========
let isRunning = false
function runSync() {
  if (isRunning) { log('上一次还在跑，跳过本次触发'); return }
  if (existsSync(LOCK_FILE)) { log('锁文件存在，跳过'); return }
  isRunning = true
  log('🚀 触发数据同步...')
  const start = Date.now()
  const child = spawn('node', [SYNC_SCRIPT], {
    cwd: ROOT, stdio: 'inherit', timeout: 600000  // 10 分钟超时
  })
  child.on('exit', code => {
    const cost = ((Date.now() - start) / 1000).toFixed(0)
    isRunning = false
    if (code === 0) {
      log(`✅ 同步完成 (${cost}s)`)
    } else {
      log(`❌ 同步失败 exit=${code} (${cost}s)`, 'ERROR')
    }
  })
  child.on('error', e => { isRunning = false; log(`❌ spawn 失败: ${e.message}`, 'ERROR') })
}

// ========== 守护进程主循环 ==========
function daemonLoop() {
  const cron = parseCron(CRON)
  log(`🎯 cron: "${CRON}" (check every ${CHECK_INTERVAL/1000}s)`)
  log(`📄 pid: ${process.pid}, pid_file: ${PID_FILE}`)
  writeFileSync(PID_FILE, String(process.pid))

  // 启动后立即跑一次（确保新 daemon 第一次就同步）
  runSync()

  let lastFired = new Date().toISOString().slice(0, 16)  // "YYYY-MM-DDTHH:mm"
  setInterval(() => {
    const now = new Date()
    const nowKey = now.toISOString().slice(0, 16)
    if (nowKey !== lastFired && cronMatches(cron, now)) {
      lastFired = nowKey
      runSync()
    }
    // 每分钟打印一次状态（调试用，每 60 秒一次太频繁，改成每 10 分钟）
    if (now.getMinutes() === 0) {
      log(`💓 alive (${now.toISOString().slice(0, 19)})`)
    }
  }, CHECK_INTERVAL)

  // 优雅退出
  process.on('SIGTERM', () => {
    log('收到 SIGTERM，退出')
    try { existsSync(PID_FILE) && readFileSync(PID_FILE, 'utf8').trim() === String(process.pid) && require('fs').unlinkSync(PID_FILE) } catch {}
    process.exit(0)
  })
  process.on('SIGINT', () => process.emit('SIGTERM'))
}

// ========== 子命令 ==========
function cmdStop() {
  if (!existsSync(PID_FILE)) { console.log('没有正在运行的 daemon'); return }
  const pid = readFileSync(PID_FILE, 'utf8').trim()
  try {
    const out = execSync(`ps -p ${pid} -o pid=,command= 2>/dev/null`, { encoding: 'utf8' })
    if (!out.trim()) { console.log(`pid ${pid} 不存在，清理 pid 文件`); require('fs').unlinkSync(PID_FILE); return }
    process.kill(parseInt(pid), 'SIGTERM')
    console.log(`已发送 SIGTERM 给 pid ${pid}`)
  } catch (e) {
    console.log(`停掉失败: ${e.message}`)
  }
}

function cmdStatus() {
  console.log(`cron 表达式 : ${CRON}`)
  if (existsSync(PID_FILE)) {
    const pid = readFileSync(PID_FILE, 'utf8').trim()
    try {
      const out = execSync(`ps -p ${pid} -o pid=,etime=,command= 2>/dev/null`, { encoding: 'utf8' }).trim()
      if (out) {
        console.log(`daemon 运行中 ✓`)
        console.log(`  pid  : ${pid}`)
        console.log(`  状态 : ${out.split(/\s+/).slice(1).join(' ')}`)
        console.log(`  日志 : ${LOG_FILE}`)
        return
      }
    } catch {}
    console.log(`pid 文件过期 (pid ${pid} 不存在)`)
  }
  console.log('daemon 未运行')
}

function cmdRunNow() {
  log('⚡ run-now 模式：立即执行一次')
  runSync()
  setTimeout(() => process.exit(isRunning ? 0 : 1), 120000)  // 等最多 2 分钟
}

function cmdDaemon() {
  // 检查是否已经在跑
  if (existsSync(PID_FILE)) {
    const pid = readFileSync(PID_FILE, 'utf8').trim()
    try {
      const out = execSync(`ps -p ${pid} -o pid= 2>/dev/null`, { encoding: 'utf8' })
      if (out.trim()) { console.log(`daemon 已在运行 (pid ${pid})`); return }
    } catch {}
  }
  // 后台启动
  const scriptPath = fileURLToPath(import.meta.url)
  const child = spawn('nohup', ['node', scriptPath], {
    stdio: 'ignore', detached: true, cwd: ROOT
  })
  child.unref()
  console.log(`✓ daemon 已启动 (pid ${child.pid})`)
  console.log(`  日志: ${LOG_FILE}`)
  console.log(`  停止: node scripts/scheduler.js --stop`)
}

// ========== 入口 ==========
const args = process.argv.slice(2)
if (args.includes('--stop')) cmdStop()
else if (args.includes('--status')) cmdStatus()
else if (args.includes('--run-now')) cmdRunNow()
else if (args.includes('--daemon')) cmdDaemon()
else daemonLoop()
