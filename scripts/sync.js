#!/usr/bin/env node
/**
 * 数据同步脚本 — 从 IMA 知识库拉取最新数据 → 解析文件内容 → 精准匹配 → 更新 JSON
 * 
 * 用法: node scripts/sync.js           # 完整同步（推荐，定时任务用）
 *       node scripts/sync.js --dry-run  # 只拉列表不下载不解析（调试）
 *       node scripts/sync.js --skip-download  # 跳过下载（文件已存在时）
 */

import { execSync } from 'child_process'
import { writeFileSync, readFileSync, existsSync, mkdirSync, rmSync } from 'fs'
import { join, dirname, resolve } from 'path'
import { fileURLToPath } from 'url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const ROOT = resolve(__dirname, '..')

// ========== 配置 ==========
const CONFIG = {
  SKILL_DIR: process.env.IMA_SKILL || join(ROOT, 'scripts'),
  KB_ID: 'o9q3d7B3xA1WPfSaOLqGrp-EeJ9kTXGTWM0kqf9S274=',
  FOLDERS: {
    procurement: 'folder_7508355157328511', // 采购公告（广东省）
    winning:     'folder_7508418185135953', // 中标公告（广东省）
    gd_policy:   'folder_7508334957560424', // 广东省内政策
    nat_policy:  'folder_7508334924008816', // 全国通用政策
  },
  TMP_DIR: join(ROOT, '.sync_tmp'),
  DATA_DIR: join(ROOT, 'public', 'data'),
  LOG_FILE: join(ROOT, 'logs', 'sync.log'),
  PROGRESS_FILE: join(ROOT, '.sync_progress.json'), // 记录已下载文件的 media_id，实现增量
}

// ========== 日志 ==========
function log(msg, level = 'INFO') {
  const ts = new Date().toISOString().replace('T', ' ').slice(0, 19)
  const line = `[${ts}] [${level}] ${msg}`
  console.log(line)
  try {
    mkdirSync(join(ROOT, 'logs'), { recursive: true })
    writeFileSync(CONFIG.LOG_FILE, line + '\n', { flag: 'a' })
  } catch {}
}

// ========== IMA API ==========
function imaApi(apiPath, body) {
  const bodyStr = JSON.stringify(body).replace(/'/g, "'\\''")
  const cmd = `node "${CONFIG.SKILL_DIR}/ima_api.cjs" "${apiPath}" '${bodyStr}'`
  return JSON.parse(execSync(cmd, { encoding: 'utf8', maxBuffer: 30 * 1024 * 1024 }))
}

function fetchAll(folderId, label) {
  const items = []
  let cursor = '', isEnd = false
  do {
    const r = imaApi('openapi/wiki/v1/get_knowledge_list', {
      knowledge_base_id: CONFIG.KB_ID, folder_id: folderId, cursor, limit: 50
    })
    if (r.code !== 0) { log(`IMA API 错误: ${r.msg || JSON.stringify(r)}`, 'ERROR'); break }
    items.push(...r.data.knowledge_list)
    cursor = r.data.next_cursor
    isEnd = r.data.is_end
  } while (!isEnd)
  log(`${label}: ${items.length} 条`)
  return items
}

// ========== 进度文件（增量下载） ==========
function loadProgress() {
  try { return JSON.parse(readFileSync(CONFIG.PROGRESS_FILE, 'utf8')) }
  catch { return { downloaded: {}, lastSync: null } }
}
function saveProgress(prog) {
  writeFileSync(CONFIG.PROGRESS_FILE, JSON.stringify(prog, null, 2))
}

// ========== 下载文件 ==========
function downloadFile(mediaId, outPath) {
  try {
    const r = imaApi('openapi/wiki/v1/get_media_info', { media_id: mediaId })
    if (r.code !== 0 || !r.data?.url_info?.url) return false
    const url = r.data.url_info.url
    const cmd = `curl -sL -H "X-IMA-Platform: H5" -o "${outPath}" "${url}"`
    execSync(cmd, { stdio: 'pipe', timeout: 90000 })
    return true
  } catch (e) {
    return false
  }
}

function downloadAll(items, prefix, prog) {
  let newCount = 0, skipCount = 0, failCount = 0
  items.forEach((x, i) => {
    const ext = x.title.match(/\.(\w+)$/)?.[1] || 'bin'
    const outPath = join(CONFIG.TMP_DIR, `${prefix}_${i}.${ext}`)
    // 增量：media_id 已下载过就跳过
    if (prog.downloaded[x.media_id] && existsSync(outPath)) {
      skipCount++
      return
    }
    const ok = downloadFile(x.media_id, outPath)
    if (ok) {
      prog.downloaded[x.media_id] = { prefix, idx: i, ext, title: x.title }
      newCount++
    } else {
      failCount++
    }
    process.stdout.write(`  ${prefix}_${i}/${items.length} ${ok ? '✓' : '✗'}\r`)
  })
  console.log()
  log(`${prefix}: 新增 ${newCount}, 跳过 ${skipCount}, 失败 ${failCount}`)
  return { newCount, skipCount, failCount }
}

// ========== 生成元数据 ==========
function saveMeta(procList, winList) {
  const meta = {
    updated: new Date().toISOString().slice(0, 10),
    procurement: procList.map((x, i) => ({
      idx: i, title: x.title, media_id: x.media_id,
      file: `proc_${i}.${x.title.match(/\.(\w+)$/)?.[1]}`
    })),
    winning: winList.map((x, i) => ({
      idx: i, title: x.title, media_id: x.media_id,
      file: `win_${i}.${x.title.match(/\.(\w+)$/)?.[1]}`
    })),
  }
  writeFileSync(join(CONFIG.TMP_DIR, 'meta.json'), JSON.stringify(meta, null, 2))
}

// ========== Python 解析 ==========
function runPython() {
  const pyPath = join(__dirname, 'parse_match.py')
  const cmd = `python3 "${pyPath}"`
  log(`执行 Python 解析...`)
  execSync(cmd, { stdio: 'inherit' })
}

function cleanTitle(t) {
  if (!t) return ''
  // 清理全国政策标题末尾的"门户"后缀
  let s = t.replace(/\s*[-—]\s*.*?(?:门户|官网|网站).*$/g, '').trim()
  return s
}

function updatePolicyJson(gdList, natList) {
  let oldPolicy = null
  try { oldPolicy = JSON.parse(readFileSync(join(CONFIG.DATA_DIR, 'policy.json'), 'utf8')) } catch {}
  
  // 建旧数据索引：mediaId → 条目
  const oldGdMap = new Map()
  const oldNatMap = new Map()
  ;(oldPolicy?.categories?.find(c => c.id === 'guangdong')?.items || []).forEach(o => {
    if (o.mediaId) oldGdMap.set(o.mediaId, o)
    if (o.title) oldGdMap.set(`title:${o.title.slice(0, 30)}`, o)
  })
  ;(oldPolicy?.categories?.find(c => c.id === 'national')?.items || []).forEach(o => {
    if (o.mediaId) oldNatMap.set(o.mediaId, o)
    if (o.title) oldNatMap.set(`title:${o.title.slice(0, 30)}`, o)
  })
  
  function merge(rawItems, oldMap, source) {
    return rawItems.map(x => {
      // 优先 mediaId 精确匹配，再标题前缀兜底
      let oldMatch = oldMap.get(x.media_id) || oldMap.get(`title:${x.title?.slice(0, 30)}`)
      // 再兜底：标题互相包含（防止旧数据也被清理过）
      if (!oldMatch) {
        for (const [k, v] of oldMap) {
          if (k.startsWith('title:') && x.title && (x.title.includes(v.title?.slice(0, 25)) || v.title?.includes(x.title.slice(0, 25)))) {
            oldMatch = v; break
          }
        }
      }
      return {
        title: cleanTitle(x.title),
        mediaId: x.media_id,
        doc_no: oldMatch?.doc_no || '',
        date: oldMatch?.date || '',
        url: oldMatch?.url || '',
        source,
      }
    }).sort((a, b) => (b.date || '').localeCompare(a.date || ''))  // 按日期倒序
  }

  const today = new Date().toISOString().slice(0, 10)
  const policy = {
    site: { ...(oldPolicy?.site || { title: '教育政策资料库' }), updated: today },
    updated: today,
    categories: [
      { id: 'guangdong', name: '广东省内政策', source: 'https://edu.gd.gov.cn/gkmlpt/policy/',
        items: merge(gdList, oldGdMap, '广东省教育厅') },
      { id: 'national', name: '全国通用政策', source: 'http://www.moe.gov.cn/jyb_xxgk/zywj_btlj/index.html',
        items: merge(natList, oldNatMap, '教育部') },
    ],
  }
  writeFileSync(join(CONFIG.DATA_DIR, 'policy.json'), JSON.stringify(policy, null, 2))
  const total = policy.categories.reduce((s, c) => s + c.items.length, 0)
  const withNo = policy.categories.reduce((s, c) => s + c.items.filter(i => i.doc_no).length, 0)
  const withDt = policy.categories.reduce((s, c) => s + c.items.filter(i => i.date).length, 0)
  log(`✓ policy.json: ${total} 条 (文号${withNo} 日期${withDt})`)
}

// ========== 主流程 ==========
function main() {
  const args = process.argv.slice(2)
  const DRY_RUN = args.includes('--dry-run')
  const SKIP_DOWNLOAD = args.includes('--skip-download')

  mkdirSync(CONFIG.TMP_DIR, { recursive: true })
  mkdirSync(CONFIG.DATA_DIR, { recursive: true })
  
  log('═══════════════════════════════════════')
  log('🚀 教育平台数据同步开始')
  log('═══════════════════════════════════════')

  try {
    // 1. 拉列表
    log('Step 1: 从 IMA 拉取文件列表...')
    const procList = fetchAll(CONFIG.FOLDERS.procurement, '采购公告')
    const winList  = fetchAll(CONFIG.FOLDERS.winning,  '中标公告')
    const gdList   = fetchAll(CONFIG.FOLDERS.gd_policy, '广东政策')
    const natList  = fetchAll(CONFIG.FOLDERS.nat_policy, '全国政策')

    if (DRY_RUN) { log('[dry-run] 跳过下载和解析'); return }

    // 2. 下载（增量）
    if (!SKIP_DOWNLOAD) {
      log('Step 2: 下载文件（增量）...')
      const prog = loadProgress()
      downloadAll(procList, 'proc', prog)
      downloadAll(winList,  'win',  prog)
      prog.lastSync = new Date().toISOString()
      saveProgress(prog)
    }

    // 3. 保存元数据
    saveMeta(procList, winList)

    // 4. Python 解析 + 匹配 → 生成 bidding.json
    log('Step 3: Python 解析文件内容 + 精准匹配...')
    runPython()

    // 5. 更新 policy.json（保留已有文号/日期/URL 合并）
    log('Step 4: 更新 policy.json...')
    updatePolicyJson(gdList, natList)

    // 6. 政策数据补全（URL 抓文号+日期，缓存，每次 5 条）
    log('Step 5: 政策文号/日期自动补全...')
    const enrichPath = join(__dirname, 'policy_enrich.py')
    if (existsSync(enrichPath)) {
      try {
        execSync(`python3 "${enrichPath}"`, { stdio: 'inherit' })
      } catch (e) {
        log(`补全跳过（不阻塞主流程）: ${e.message}`)
      }
    }

    log('═══════════════════════════════════════')
    log('✅ 同步完成！所有 JSON 已更新')
    log(`⏰ 下次同步: 每天凌晨 3:00 (launchd)`)
    log('═══════════════════════════════════════')
  } catch (e) {
    log(`❌ 同步失败: ${e.message}`, 'ERROR')
    process.exit(1)
  }
}

main()
