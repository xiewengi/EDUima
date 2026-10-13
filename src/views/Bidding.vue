<template>
  <div class="edu-bidding edu-page">
    <div class="edu-container">
      <!-- 页面标题 -->
      <div class="edu-page-header">
        <div>
          <h1 class="edu-page-title">
            <el-icon><Files /></el-icon> 招投标信息
          </h1>
          <p class="edu-page-subtitle">广东省教育行业招投标<b>中标（成交）结果公告</b>信息库，支持一键跳转政府采购网原文。</p>
        </div>
        <div class="edu-page-meta">
          <el-tag type="info">更新：{{ updated }}</el-tag>
          <el-tag type="success">中标 {{ winningCount }} 条</el-tag>
        </div>
      </div>

      <!-- 统计摘要 -->
      <div class="edu-bidding-summary edu-card">
        <div class="edu-bidding-summary__item">
          <div class="edu-bidding-summary__value edu-bidding-summary__value--orange">{{ winningCount }}</div>
          <div class="edu-bidding-summary__label">🏆 中标公告</div>
        </div>
        <div class="edu-bidding-summary__item">
          <div class="edu-bidding-summary__value edu-bidding-summary__value--blue">{{ regionCount }}</div>
          <div class="edu-bidding-summary__label">📍 覆盖地区</div>
        </div>
        <div class="edu-bidding-summary__item">
          <div class="edu-bidding-summary__value edu-bidding-summary__value--green">{{ schoolCount }}</div>
          <div class="edu-bidding-summary__label">🏫 涉及学校</div>
        </div>
        <div class="edu-bidding-summary__item">
          <div class="edu-bidding-summary__value edu-bidding-summary__value--gray">{{ linkedCount }}</div>
          <div class="edu-bidding-summary__label">🔗 原文链接</div>
        </div>
      </div>

      <!-- 筛选工具栏 -->
      <div class="edu-filter-bar edu-card">
        <el-input v-model="keyword" placeholder="搜索项目/学校..." :prefix-icon="Search" clearable class="edu-filter-search" />
        <el-select v-model="regionFilter" placeholder="地区" clearable class="edu-filter-select">
          <el-option v-for="r in regions" :key="r" :label="r" :value="r" />
        </el-select>
        <el-select v-model="stageFilter" placeholder="学段" clearable class="edu-filter-select">
          <el-option label="基础教育" value="基础教育" />
          <el-option label="职业教育" value="职业教育" />
          <el-option label="高等教育" value="高等教育" />
          <el-option label="学前教育" value="学前教育" />
        </el-select>
        <div class="edu-filter-bar__spacer"></div>
        <el-button :icon="Refresh" @click="resetFilter">重置</el-button>
      </div>

      <!-- 中标公告列表（全宽单列） -->
      <div class="edu-paired-view">
        <div class="edu-paired-view__col edu-paired-view__col--full">
          <div class="edu-paired-view__header edu-paired-view__header--right">
            <el-icon><Trophy /></el-icon>
            <span>中标公告</span>
            <el-tag size="small" type="success">{{ filteredWinning.length }}</el-tag>
          </div>
          <div class="edu-paired-list edu-paired-list--full">
            <template v-if="filteredWinning.length > 0">
              <div
                v-for="item in pagedWinning"
                :key="item.id"
                class="edu-paired-item edu-paired-item--winning"
              >
                <div class="edu-paired-item__status edu-paired-item__status--right">
                  <el-icon class="is-winning"><Trophy /></el-icon>
                </div>
                <div class="edu-paired-item__body">
                  <!-- 取值口径同医疗站：标题展示「项目名称」（确定性裁剪），悬浮显示完整原标题 -->
                  <h4 class="edu-paired-item__title" :title="item.title">{{ item.projectName || item.title }}</h4>
                  <div class="edu-paired-item__meta">
                    <span v-if="item.projectCode" class="edu-tag edu-tag--accent">{{ item.projectCode }}</span>
                    <span v-if="item.region" class="edu-tag">{{ item.region }}</span>
                    <span v-if="item.contractNo">📦 {{ item.contractNo }}</span>
                    <span v-if="item.attachCount || item.attachments?.length" class="edu-paired-item__attachs">📎 {{ item.attachCount || item.attachments?.length }} 份附件</span>
                  </div>
                  <div class="edu-paired-item__sub">
                    <div v-if="item.school" class="edu-paired-item__sub-row">
                      <el-icon><OfficeBuilding /></el-icon>
                      <span>{{ item.school }}</span>
                    </div>
                    <div v-if="item.stage" class="edu-paired-item__sub-row">
                      <span class="edu-paired-item__sub-label">学段</span>
                      <span>{{ item.stage }}</span>
                    </div>
                    <div v-if="item.winningBidder" class="edu-paired-item__sub-row">
                      <span class="edu-paired-item__sub-label">中标方</span>
                      <span>{{ item.winningBidder }}</span>
                    </div>
                    <!-- 摘要：摘自公告正文开头段落（gen-bids.py 定向挑段，只截取不改写），同医疗站 policy-summary -->
                    <div v-if="item.summary" class="edu-paired-item__sub-row">
                      <span class="edu-paired-item__sub-label">摘要</span>
                      <span class="edu-paired-item__summary">{{ item.summary }}</span>
                    </div>
                  </div>
                </div>
                <!-- 底部链接区：同医疗站 bidCard 的 foot 三件套 -->
                <div v-if="item.purchaseUrl || item.purchaseZipUrl || item.sourceUrl" class="edu-paired-item__links">
                  <a
                    v-if="item.purchaseUrl"
                    class="edu-paired-item__source"
                    :href="item.purchaseUrl"
                    target="_blank"
                    rel="noopener"
                    title="跳转到广东省政府采购网的对应采购公告页面"
                  >
                    <el-icon><Link /></el-icon> 采购公告
                  </a>
                  <a
                    v-if="item.purchaseZipUrl"
                    class="edu-paired-item__source"
                    :href="item.purchaseZipUrl"
                    download
                    :title="(item.purchaseZipName || '招标文件压缩包') + '（gdgpo 原件 zip，内含 Word 招标文件）'"
                  >
                    <el-icon><Download /></el-icon> 下载采购文件
                  </a>
                  <a
                    v-if="item.sourceUrl"
                    class="edu-paired-item__source"
                    :href="item.sourceUrl"
                    target="_blank"
                    rel="noopener"
                    title="跳转到广东省政府采购网的对应公告页面"
                  >
                    <el-icon><Link /></el-icon> 中标公告
                  </a>
                </div>
              </div>
            </template>
            <el-empty v-else description="暂无匹配的中标公告" />
          </div>
          <!-- 分页：每页 9 条（3 列 × 3 行） -->
          <div class="edu-paired-pagination" v-if="filteredWinning.length > PAGE_SIZE">
            <el-pagination
              v-model:current-page="currentPage"
              :page-size="PAGE_SIZE"
              :total="filteredWinning.length"
              layout="total, prev, pager, next"
              background
            />
          </div>
        </div>
      </div>

      <!-- 底部提示：老大指示不展示（2026-10-13） -->
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import {
  Files, Search, Refresh, Trophy, Link, Download, OfficeBuilding
} from '@element-plus/icons-vue'

// ─────────────────────────────────────────────────────────────────────────────
// 取值逻辑照抄医疗平台知识库站点（bids.html + app.js，2026-10-13）：
//   · 数据直接取自 ima 知识库「教育平台」招投标文件夹（fetch-bids.cjs 快照 + 正文存档），
//     由 gen-bids.py 字段化（projectName 裁剪 / 定向挑段摘要 / 采购结果抽取 / gdgpo 反查链接）
//   · 只展示中标（成交）结果公告（isAward 过滤口径同医疗站）
//   · 摘要、供应商、金额均摘自公告正文，只做选取不做推断；原文没有的留空
// ─────────────────────────────────────────────────────────────────────────────
const rawData = ref({ updatedAt: '—', items: [] })
const keyword = ref('')
const regionFilter = ref('')
const stageFilter = ref('')
const updated = ref('—')

// 分页：每页 9 条（3 列 × 3 行）
const PAGE_SIZE = 9
const currentPage = ref(1)

/** 只保留中标（成交）结果：group / 标题含「中标|结果|成交」（同医疗站 isAward） */
const isAward = (b) => {
  const hay = (b.group || '') + ' ' + (b.title || '')
  return hay.includes('中标') || hay.includes('结果') || hay.includes('成交')
}

const winningList = computed(() => (rawData.value.items || []).filter(isAward))

const regions = computed(() => {
  const set = new Set()
  winningList.value.forEach(w => w.region && set.add(w.region))
  return [...set].sort()
})

const filteredWinning = computed(() => {
  let list = winningList.value
  if (regionFilter.value) list = list.filter(w => w.region === regionFilter.value)
  if (stageFilter.value) list = list.filter(w => w.stage === stageFilter.value)
  if (keyword.value) {
    // 搜索口径同医疗站：项目名称 / 原标题 / 编号 / 摘要 / 学校 / 分组
    const kw = keyword.value.toLowerCase()
    list = list.filter(w => [
      w.projectName, w.title, w.docNo, w.projectCode, w.summary, w.school, w.group,
    ].join(' ').toLowerCase().includes(kw))
  }
  return list
})

// 当前页切片：翻页 / 筛选都从这里出数据
const pagedWinning = computed(() => {
  const start = (currentPage.value - 1) * PAGE_SIZE
  return filteredWinning.value.slice(start, start + PAGE_SIZE)
})

// 筛选条件变化 → 回到第 1 页（避免停留在超出范围的空页）
watch([keyword, regionFilter, stageFilter], () => { currentPage.value = 1 })

const winningCount = computed(() => winningList.value.length)
const regionCount = computed(() => regions.value.length)
const schoolCount = computed(() => new Set(winningList.value.map(w => w.school).filter(Boolean)).size)
const linkedCount = computed(() => winningList.value.filter(w => w.sourceUrl).length)

const resetFilter = () => {
  keyword.value = ''
  regionFilter.value = ''
  stageFilter.value = ''
}

onMounted(async () => {
  try {
    const res = await fetch(import.meta.env.BASE_URL + 'data/bidding.json?v=' + Date.now())
    const data = await res.json()
    // 兼容两种结构：新链路 { updatedAt, items } / 旧链路 { updated, winning }
    rawData.value = data
    updated.value = data.updatedAt || data.updated || '—'
  } catch (e) {
    console.error('Failed to load bidding data:', e)
  }
})
</script>

<style scoped>
.edu-page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--edu-space-5);
  flex-wrap: wrap;
  gap: var(--edu-space-3);
}
.edu-page-title {
  display: flex;
  align-items: center;
  gap: var(--edu-space-2);
  font-size: var(--edu-font-2xl);
  font-weight: 700;
  margin: 0 0 var(--edu-space-1);
  color: var(--edu-text-primary);
}
.edu-page-subtitle {
  color: var(--edu-text-secondary);
  font-size: var(--edu-font-base);
  margin: 0;
}
.edu-page-subtitle strong {
  color: var(--edu-primary);
}

/* 统计摘要 */
.edu-bidding-summary {
  display: flex;
  align-items: stretch;
  justify-content: center;
  padding: var(--edu-space-4);
  gap: 0;
  margin-bottom: var(--edu-space-5);
  overflow: hidden;
}
.edu-bidding-summary__item {
  text-align: center;
  flex: 1;
  padding: var(--edu-space-3) var(--edu-space-4);
  border-right: 1px solid var(--edu-border-light);
}
.edu-bidding-summary__item:last-child { border-right: none; }
.edu-bidding-summary__value {
  font-size: 32px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  line-height: 1.2;
}
.edu-bidding-summary__value--blue { color: var(--edu-primary); }
.edu-bidding-summary__value--orange { color: var(--edu-accent-hover); }
.edu-bidding-summary__value--green { color: var(--edu-success); }
.edu-bidding-summary__value--gray { color: var(--edu-text-secondary); }
.edu-bidding-summary__label {
  font-size: var(--edu-font-sm);
  color: var(--edu-text-secondary);
  margin-top: 4px;
}

/* 筛选栏 */
.edu-filter-bar {
  display: flex;
  gap: var(--edu-space-2);
  padding: var(--edu-space-3);
  margin-bottom: var(--edu-space-5);
  flex-wrap: wrap;
  align-items: center;
}
.edu-filter-search { min-width: 200px; flex: 0 0 auto; }
.edu-filter-select { width: 130px; }
.edu-filter-bar__spacer { flex: 1; min-width: 0; }

/* 配对视图 */
.edu-paired-view {
  display: flex;
  gap: var(--edu-space-3);
  margin-bottom: var(--edu-space-5);
}
.edu-paired-view__col--full { flex: 1 1 100%; width: 100%; }
/* 三列网格：中标公告卡片 */
.edu-paired-list.edu-paired-list--full {
  max-height: none;
  overflow-y: visible;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--edu-space-3);
  padding: var(--edu-space-3);
}
.edu-paired-list--full .edu-paired-item,
.edu-paired-list--full .edu-paired-item:last-child {
  flex-direction: column;
  align-items: stretch;
  gap: var(--edu-space-2);
  border: 1px solid var(--edu-border-light);
  border-radius: var(--edu-radius-md);
  margin: 0;
  transition: box-shadow 0.2s, transform 0.2s;
}
.edu-paired-list--full .edu-paired-item:hover {
  background: #fff;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
  transform: translateY(-2px);
}
.edu-paired-list--full .edu-paired-item__status { padding-top: 0; }
.edu-paired-list--full .edu-paired-item__title {
  -webkit-line-clamp: 3;
  min-height: 3.2em;
}
.edu-paired-item__source {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  align-self: flex-start;
  font-size: var(--edu-font-xs);
  font-weight: 600;
  color: var(--edu-primary);
  text-decoration: none;
  padding: 5px 10px;
  border: 1px solid var(--edu-primary-light);
  border-radius: var(--edu-radius-md);
  background: var(--edu-primary-lighter);
  transition: all 0.2s;
  white-space: nowrap;
}
.edu-paired-item__source .el-icon { font-size: 13px; }
.edu-paired-item__source:hover {
  color: #fff;
  background: var(--edu-primary);
  border-color: var(--edu-primary);
}
/* 卡片底部链接区：采购公告 / 下载采购文件 / 中标公告 三件套（同医疗站 bidCard foot） */
.edu-paired-item__links {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
/* 摘要正文：最多 3 行，超出省略 */
.edu-paired-item__summary {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
@media (max-width: 1200px) {
  .edu-paired-list--full { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 720px) {
  .edu-paired-list--full { grid-template-columns: 1fr; }
}

/* 分页条 */
.edu-paired-pagination {
  display: flex;
  justify-content: center;
  padding: var(--edu-space-3) 0 var(--edu-space-2);
}
.edu-paired-view__col {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}
.edu-paired-view__connector {
  width: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.edu-paired-view__connector-inner {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--edu-primary-light);
  color: var(--edu-primary);
  transition: all 0.3s;
}
.edu-paired-view__connector-inner.is-connected {
  background: var(--edu-success-light);
  color: var(--edu-success);
  transform: scale(1.1);
}

.edu-paired-view__header {
  display: flex;
  align-items: center;
  gap: var(--edu-space-2);
  padding: var(--edu-space-2) var(--edu-space-3);
  font-size: var(--edu-font-base);
  font-weight: 600;
  border-radius: var(--edu-radius-md) var(--edu-radius-md) 0 0;
  flex-wrap: wrap;
}
.edu-paired-view__header--left {
  background: var(--edu-primary-lighter);
  color: var(--edu-primary);
  border: 1px solid var(--edu-primary-light);
  border-bottom: none;
}
.edu-paired-view__header--right {
  background: #FEF3E2;
  color: var(--edu-accent-hover);
  border: 1px solid #FDE8CC;
  border-bottom: none;
}

.edu-paired-list {
  flex: 1;
  background: #fff;
  border-radius: 0 0 var(--edu-radius-md) var(--edu-radius-md);
  border: 1px solid var(--edu-border-light);
  border-top: none;
  max-height: 680px;
  overflow-y: auto;
}

.edu-paired-item {
  display: flex;
  align-items: flex-start;
  gap: var(--edu-space-3);
  padding: var(--edu-space-3);
  border-bottom: 1px solid var(--edu-border-light);
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}
.edu-paired-item:last-child { border-bottom: none; }
.edu-paired-item:hover { background: var(--edu-bg-hover); }
.edu-paired-item.is-matched { border-left: 3px solid var(--edu-success); }
.edu-paired-item.is-active { background: var(--edu-primary-lighter); border-left: 3px solid var(--edu-primary); }

.edu-paired-item__status {
  flex-shrink: 0;
  padding-top: 4px;
}
.edu-paired-item__status .is-matched { color: var(--edu-success); font-size: 18px; }
.edu-paired-item__status .is-unmatched { color: var(--edu-text-placeholder); font-size: 18px; }
.edu-paired-item__status .is-winning { color: var(--edu-accent); font-size: 18px; }

.edu-paired-item__body { flex: 1; min-width: 0; }
.edu-paired-item__title {
  font-size: var(--edu-font-sm);
  font-weight: 600;
  color: var(--edu-text-primary);
  margin: 0 0 6px;
  line-height: 1.5;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}
.edu-paired-item__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  font-size: var(--edu-font-xs);
  color: var(--edu-text-secondary);
  margin-bottom: 4px;
  align-items: center;
}
.edu-paired-item__match-info {
  color: var(--edu-primary);
  font-weight: 600;
}
.edu-paired-item__attachs {
  color: var(--edu-text-placeholder);
}
.edu-paired-item__sub {
  display: flex;
  flex-direction: column;
  gap: 5px;
  font-size: var(--edu-font-xs);
  color: var(--edu-text-secondary);
}
.edu-paired-item__sub-row {
  display: flex;
  align-items: baseline;
  gap: 6px;
  line-height: 1.5;
}
.edu-paired-item__sub-row .el-icon {
  font-size: 12px;
  align-self: center;
  flex-shrink: 0;
}
.edu-paired-item__sub-label {
  flex-shrink: 0;
  color: var(--edu-text-placeholder);
}
.edu-paired-item__sub-row span:last-child {
  word-break: break-all;
}

/* 空状态 */
.edu-paired-empty {
  padding: 48px 24px;
  text-align: center;
  color: var(--edu-text-secondary);
}
.edu-paired-empty__title {
  font-size: var(--edu-font-md);
  font-weight: 600;
  margin: var(--edu-space-3) 0 var(--edu-space-1);
  color: var(--edu-text-secondary);
}
.edu-paired-empty__desc {
  font-size: var(--edu-font-sm);
  color: var(--edu-text-placeholder);
  margin: 0;
  line-height: 1.6;
}

@media (max-width: 1200px) {
  .edu-bidding-summary__value { font-size: 26px; }
}
@media (max-width: 960px) {
  .edu-paired-view { flex-direction: column; }
  .edu-paired-view__connector { display: none; }
  .edu-bidding-summary__item { padding: var(--edu-space-2) var(--edu-space-2); }
  .edu-bidding-summary__value { font-size: 22px; }
}
@media (max-width: 640px) {
  .edu-filter-bar { gap: 6px; }
  .edu-filter-search { width: 100%; }
  .edu-filter-select { width: calc(50% - 6px); }
  .edu-bidding-summary { flex-wrap: wrap; }
  .edu-bidding-summary__item { flex: 0 0 50%; border-right: none; border-bottom: 1px solid var(--edu-border-light); padding: var(--edu-space-2); }
}
</style>
