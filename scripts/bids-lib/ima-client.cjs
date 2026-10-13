'use strict';

/**
 * ima 知识库 MCP 客户端（极简，零依赖）
 * ------------------------------------------------------------------
 * 直连 WorkBuddy 使用的同一个远程 MCP 端点：https://ima.qq.com/mcp
 * 协议：JSON-RPC 2.0 over streamable HTTP（响应可能是 SSE 或裸 JSON，两种都处理）
 *
 * 本模块只暴露读操作需要的两个能力：列库、列条目。
 * 令牌由调用方传入（见 ima-cred.js），本模块不负责获取与存储。
 */

const ENDPOINT = 'https://ima.qq.com/mcp';
const PROTOCOL_VERSION = '2025-06-18';
const TIMEOUT_MS = Number(process.env.IMA_TIMEOUT_MS || 20000);

/** SSE 与裸 JSON 都能解析 */
function parsePayload(text) {
  const dataLines = text.split('\n').filter((l) => l.startsWith('data:'));
  const body = dataLines.length ? dataLines.map((l) => l.slice(5).trim()).join('') : text;
  try {
    return JSON.parse(body);
  } catch {
    return null;
  }
}

class ImaClient {
  constructor(token) {
    if (!token) throw new Error('ima 令牌缺失');
    this.token = token;
    this.sessionId = null;
    this.nextId = 1;
  }

  async #rpc(method, params) {
    const headers = {
      'Content-Type': 'application/json',
      Accept: 'application/json, text/event-stream',
      Authorization: this.token,
    };
    if (this.sessionId) headers['Mcp-Session-Id'] = this.sessionId;

    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);
    let res;
    try {
      res = await fetch(ENDPOINT, {
        method: 'POST',
        headers,
        body: JSON.stringify({ jsonrpc: '2.0', id: this.nextId++, method, params }),
        signal: controller.signal,
      });
    } finally {
      clearTimeout(timer);
    }

    const sid = res.headers.get('mcp-session-id');
    if (sid) this.sessionId = sid;

    const text = await res.text();
    if (!res.ok) {
      throw new Error(`ima 接口返回 HTTP ${res.status}${text ? '：' + text.slice(0, 160) : ''}`);
    }

    const json = parsePayload(text);
    if (!json) throw new Error('ima 接口响应无法解析（既非 JSON 也非 SSE）');
    if (json.error) throw new Error(`ima 接口错误：${json.error.message || JSON.stringify(json.error)}`);
    return json.result;
  }

  async connect() {
    await this.#rpc('initialize', {
      protocolVersion: PROTOCOL_VERSION,
      capabilities: {},
      clientInfo: { name: 'medical-portal', version: '1.0.0' },
    });
    return this;
  }

  async callTool(name, args) {
    const result = await this.#rpc('tools/call', { name, arguments: args || {} });
    const text = (result && result.content ? result.content : [])
      .map((c) => c.text || '')
      .join('');
    if (result && result.isError) throw new Error(`ima 工具 ${name} 执行失败：${text.slice(0, 200)}`);
    try {
      return JSON.parse(text);
    } catch {
      return { _raw: text };
    }
  }

  /** 拉取某知识库的条目列表（自动翻页，最多 maxPages 页） */
  async listKnowledge(kbId, { limit = 50, maxPages = 10 } = {}) {
    const items = [];
    let cursor = '';
    let total = null;
    let kbInfo = null;

    for (let page = 0; page < maxPages; page++) {
      const data = await this.callTool('get_knowledge_list', {
        knowledge_base_id: kbId,
        limit,
        sort_type: 'UPDATE_TS_DESC_SORT_TYPE',
        cursor,
      });
      const batch = data.knowledge_list || data.list || [];
      items.push(...batch);
      if (total === null) total = Number(data.total_size ?? data.total ?? batch.length);
      if (!batch.length) break;

      cursor = data.cursor || data.next_cursor || '';
      if (!cursor) break;
    }

    return { items, total: total === null ? items.length : total, knowledgeBase: kbInfo };
  }

  /** 读取知识库基本信息 */
  async getKnowledgeBase(kbId) {
    const data = await this.callTool('get_knowledge_base_list', { params: [{ limit: 100, type: 'KBT_MINE_KB' }] });
    const list = data.knowledge_base_list || data.list || [];
    return list.find((k) => String(k.id || k.knowledge_base_id) === String(kbId)) || null;
  }
}

module.exports = { ImaClient, ENDPOINT };
