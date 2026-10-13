'use strict';
/**
 * 抓取 ima 知识库「教育平台」的招投标两个文件夹（递归子文件夹）并拉取每份文件的正文，
 * 落盘快照 + Markdown 存档。取值逻辑照抄医疗平台知识库站点的 fetch-bids.js（2026-10-13）。
 *
 * 用法：
 *   node scripts/fetch-bids.js            # 增量：已有正文的跳过
 *   node scripts/fetch-bids.js --force    # 全量重抓正文
 *   node scripts/fetch-bids.js --no-content  # 只抓条目，不抓正文
 *
 * 产物：
 *   data/_raw/ima-bids.json   条目快照（含 folderPath、contentFile）
 *   data/_raw/bids-md/*.md    每份文件的正文（ima 返回的 Markdown 原文）
 *
 * 约定：正文原样落盘，不做清洗、改写或补全；抓不到就记空，不做推断。
 */
const fs = require('node:fs');
const path = require('node:path');
const { readToken } = require('./bids-lib/ima-cred.cjs');
const { ImaClient } = require('./bids-lib/ima-client.cjs');

// ⚠️ MCP 侧 knowledge_base_id 是数字形态（openapi 的 o9q3d7...= 在 MCP 不通用，220001 参数错误）。
// 数字 id 由 get_knowledge_base_list 查得（2026-10-13），即教育库条目 mediaId 的尾部后缀。
const BIDS_KB = '7508334806566436';
const KB_NAME = '教育平台';
// 只遍历招投标两个文件夹（库顶层的政策等其他文件夹不抓），folder_id 与 sync.js 保持一致
const BID_FOLDERS = [
  { id: 'folder_7508355157328511', name: '采购公告（广东省）' },
  { id: 'folder_7508418185135953', name: '中标公告（广东省）' },
];

const ROOT = path.join(__dirname, '..');
const RAW_DIR = path.join(ROOT, 'data', '_raw');
const MD_DIR = path.join(RAW_DIR, 'bids-md');
const SNAP_PATH = path.join(RAW_DIR, 'ima-bids.json');

const FORCE = process.argv.includes('--force');
const NO_CONTENT = process.argv.includes('--no-content');

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

/** 把标题清洗成安全的文件名主体 */
function sanitize(title, maxLen = 60) {
  let s = String(title)
    .replace(/\.(pptx?|docx?|pdf|txt|md|markdown|xlsx?)$/i, '')
    .replace(/[\\/:*?"<>|\u0000-\u001f]/g, '_')
    .replace(/\s+/g, ' ')
    .trim();
  if (s.length > maxLen) s = s.slice(0, maxLen).trim();
  return s || 'untitled';
}

/** 短哈希：给同名文件兜底去重 */
function shortHash(str) {
  let h = 0;
  for (let i = 0; i < str.length; i++) h = (h * 31 + str.charCodeAt(i)) | 0;
  return (h >>> 0).toString(36).slice(0, 6);
}

/** 翻页拉取某文件夹下的全部条目 */
async function listAll(client, folderId) {
  const out = [];
  let cursor = '';
  for (let page = 0; page < 20; page++) {
    const args = { knowledge_base_id: BIDS_KB, limit: 50 };
    if (folderId) args.folder_id = folderId;
    if (cursor) args.cursor = cursor;
    const data = await client.callTool('get_knowledge_list', args);
    const batch = data.knowledge_list || [];
    out.push(...batch);
    const next = data.next_cursor || '';
    if (data.is_end || !batch.length || !next || next === cursor) break;
    cursor = next;
  }
  return out;
}

/** 递归遍历：文件进 acc，文件夹继续下钻 */
async function walk(client, folderId, pathArr, acc, depth = 0) {
  const indent = '  '.repeat(depth + 1);
  const items = await listAll(client, folderId);
  const folders = items.filter((x) => x.media_type === 99);
  const files = items.filter((x) => x.media_type !== 99);
  console.log(`${indent}${pathArr[pathArr.length - 1] || KB_NAME} → 文件夹 ${folders.length}、文件 ${files.length}`);

  for (const f of files) {
    acc.push({ entry: f, folderPath: pathArr.slice() });
  }
  for (const d of folders) {
    const name = (d.folder_info && d.folder_info.name) || d.title;
    const fid = (d.folder_info && d.folder_info.folder_id) || d.media_id;
    if (depth < 3) {
      await walk(client, fid, pathArr.concat(name), acc, depth + 1);
    }
  }
}

(async () => {
  const cred = readToken();
  if (!cred) {
    console.error('!!! 读不到 ima 令牌，终止');
    process.exit(1);
  }
  const client = await new ImaClient(cred.token).connect();

  fs.mkdirSync(MD_DIR, { recursive: true });

  // ---------- 遍历两个招投标文件夹 ----------
  // ⚠️ MCP 的 get_knowledge_list 不认 openapi 那种带 folder_ 前缀的 id（220001 参数错误），
  // 要先列库顶层，按名字找到文件夹后用返回的 folder_info.folder_id（裸数字）。
  const topLevel = await listAll(client, '');
  const acc = [];
  for (const f of BID_FOLDERS) {
    const dir = topLevel.find((x) => x.media_type === 99
      && (((x.folder_info || {}).name) || x.title) === f.name);
    if (!dir) {
      console.error(`!!! 顶层找不到文件夹「${f.name}」，终止`);
      process.exit(1);
    }
    const fid = (dir.folder_info && dir.folder_info.folder_id) || dir.media_id;
    console.log(`▸ 遍历「${f.name}」（folder_id=${fid}）…`);
    await walk(client, fid, [f.name], acc);
  }
  console.log(`▸ 合计文件 ${acc.length} 个（含子文件夹）`);

  // ---------- 正文抓取（增量：已落盘的直接跳过） ----------
  const prev = new Map();
  if (fs.existsSync(SNAP_PATH)) {
    try {
      const old = JSON.parse(fs.readFileSync(SNAP_PATH, 'utf8'));
      for (const it of old.items || []) {
        if (it.contentFile) prev.set(it.id, it.contentFile);
      }
    } catch { /* 旧快照损坏则当空处理 */ }
  }

  let okCount = 0;
  let failCount = 0;
  let skipCount = 0;
  const items = [];

  for (let i = 0; i < acc.length; i++) {
    const { entry, folderPath } = acc[i];
    const idx = String(i + 1).padStart(3, '0');
    const title = entry.title || '';
    const mediaId = entry.media_id || '';

    let contentFile = '';
    if (!NO_CONTENT) {
      const fname = `${idx}_${sanitize(title)}_${shortHash(mediaId)}.md`;
      const fpath = path.join(MD_DIR, fname);
      const cached = prev.get(mediaId);

      if (!FORCE && cached && fs.existsSync(path.join(MD_DIR, cached))) {
        contentFile = cached;
        skipCount++;
      } else {
        try {
          const res = await client.callTool('fetch_media_content', { media_id: mediaId });
          const text = (res && res.content) || '';
          if (text) {
            fs.writeFileSync(fpath, text, 'utf8');
            contentFile = fname;
            okCount++;
            console.log(`  [${idx}/${acc.length}] OK  ${text.length} 字  ${title}`);
          } else {
            failCount++;
            console.log(`  [${idx}/${acc.length}] 空正文      ${title}`);
          }
        } catch (e) {
          failCount++;
          console.log(`  [${idx}/${acc.length}] 失败 ${e.message.slice(0, 60)}  ${title}`);
        }
        await sleep(120);
      }
    }

    items.push({
      id: mediaId,
      title,
      introduction: entry.introduction || '',
      mediaType: entry.media_type,
      mediaTypeName: (entry.media_type_info || {}).name || '',
      mediaTypeIcon: (entry.media_type_info || {}).icon || '',
      fileSize: Number(entry.file_size || 0),
      createTime: entry.create_time || '',
      mediaState: entry.media_state,
      parseProgress: entry.parse_progress ?? 0,
      folderPath,
      contentFile,
    });
  }

  const snapshot = {
    source: 'ima-mcp',
    knowledgeBase: { id: BIDS_KB, name: KB_NAME },
    fetchedAt: new Date().toISOString(),
    total: items.length,
    items,
  };
  fs.writeFileSync(SNAP_PATH, JSON.stringify(snapshot, null, 2), 'utf8');

  console.log('');
  console.log(`▸ 正文：成功 ${okCount}、跳过（已缓存）${skipCount}、失败或空 ${failCount}`);
  console.log('▸ 快照已写入:', SNAP_PATH);
  console.log('▸ 正文目录:', MD_DIR);
})().catch((e) => {
  console.error('!!! 抓取失败:', e.stack || e.message);
  process.exit(1);
});
