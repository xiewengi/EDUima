'use strict';

/**
 * ima 授权令牌读取（只读，不落盘）
 * ------------------------------------------------------------------
 * WorkBuddy 客户端把连接器凭据加密存放在：
 *   ~/.workbuddy/connectors/<userId>/connector-states.v3.json
 *   ~/.workbuddy/connectors/<userId>/connector-states.json      （v4 新版，存在则优先）
 *   ~/.workbuddy/connectors/<userId>/.master.key                 （32B 随机主密钥）
 *
 * 加解密口径与 WorkBuddy 官方实现保持一致：
 *   AES key = HKDF-SHA256(ikm = masterKey ‖ userId, salt = header.salt,
 *                         info = "workbuddy-oauth-credentials-v1", 32B)
 *   AAD     = `${userId}|connector-states:headerOverrides:<serverId>|<fieldName>`
 *
 * ⚠️ 安全约定（改动本文件前先读）：
 *   · 令牌仅在内存中短暂存在，**绝不写盘、绝不经接口返回、绝不进日志**
 *   · 每次同步都重新读取文件，WorkBuddy 刷新令牌后本服务自动跟上
 *   · 读取失败一律返回 null 并降级，不抛异常、不影响本地数据刷新
 */

const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const crypto = require('node:crypto');

const CONNECTORS_ROOT = path.join(os.homedir(), '.workbuddy', 'connectors');
const HKDF_INFO = Buffer.from('workbuddy-oauth-credentials-v1', 'utf8');
const AAD_SCOPE_HEADER = 'connector-states:headerOverrides';
const KEY_BYTES = 32;

/** 按优先级枚举所有可用状态文件（v4 优先于 v3） */
function candidateStateFiles() {
  let dirs;
  try {
    dirs = fs.readdirSync(CONNECTORS_ROOT, { withFileTypes: true })
      .filter((d) => d.isDirectory())
      .map((d) => path.join(CONNECTORS_ROOT, d.name));
  } catch {
    return [];
  }

  const out = [];
  for (const dir of dirs) {
    for (const name of ['connector-states.json', 'connector-states.v3.json']) {
      const p = path.join(dir, name);
      if (fs.existsSync(p)) out.push({ dir, file: p, userId: path.basename(dir) });
    }
  }
  return out;
}

function deriveAesKey(masterKey, userId, salt) {
  const ikm = Buffer.concat([masterKey, Buffer.from(userId, 'utf8')]);
  return Buffer.from(crypto.hkdfSync('sha256', ikm, salt, HKDF_INFO, KEY_BYTES));
}

function buildAad(userId, serverId, fieldName) {
  return Buffer.from(`${userId}|${AAD_SCOPE_HEADER}:${serverId}|${fieldName}`, 'utf8');
}

function decryptField(envelope, aesKey, userId, serverId, fieldName) {
  const iv = Buffer.from(envelope.iv, 'base64');
  const tag = Buffer.from(envelope.tag, 'base64');
  const ct = Buffer.from(envelope.ct, 'base64');
  const decipher = crypto.createDecipheriv('aes-256-gcm', aesKey, iv);
  decipher.setAAD(buildAad(userId, serverId, fieldName));
  decipher.setAuthTag(tag);
  return Buffer.concat([decipher.update(ct), decipher.final()]).toString('utf8');
}

function isEnvelope(v) {
  return v && typeof v === 'object' && typeof v.iv === 'string'
    && typeof v.tag === 'string' && typeof v.ct === 'string';
}

/**
 * 读取指定连接器的 Authorization 令牌。
 * @param {string} serverId 连接器 id，如 'ima-mcp'
 * @returns {string|null} 令牌；任一环节失败返回 null
 */
function readToken(serverId = 'ima-mcp') {
  for (const cand of candidateStateFiles()) {
    let raw;
    try {
      raw = JSON.parse(fs.readFileSync(cand.file, 'utf8'));
    } catch {
      continue;
    }
    const enc = raw.encryption;
    const node = raw.headerOverrides && raw.headerOverrides[serverId] && raw.headerOverrides[serverId].Authorization;
    if (!enc || !enc.salt || !node || !isEnvelope(node)) continue;

    let masterKey;
    try {
      masterKey = fs.readFileSync(path.join(cand.dir, '.master.key'));
    } catch {
      continue;
    }
    if (masterKey.length !== KEY_BYTES) continue;

    try {
      const salt = Buffer.from(enc.salt, 'base64');
      const aesKey = deriveAesKey(masterKey, cand.userId, salt);
      const token = decryptField(node, aesKey, cand.userId, serverId, 'Authorization');
      if (token && token.length > 0) {
        return { token, userId: cand.userId, source: path.basename(cand.file) };
      }
    } catch {
      // 该凭据条目不可解（格式变更或已失效），继续尝试下一个
      continue;
    }
  }
  return null;
}

/** 令牌是否可得（供健康检查与前端提示使用，不返回令牌本身） */
function availability(serverId = 'ima-mcp') {
  const r = readToken(serverId);
  return r ? { available: true, userId: r.userId, source: r.source } : { available: false };
}

module.exports = { readToken, availability, CONNECTORS_ROOT };
