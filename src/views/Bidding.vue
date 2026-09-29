<template>
  <div class="edu-bidding edu-page">
    <div class="edu-container">
      <!-- 页面标题 -->
      <div class="edu-page-header">
        <div>
          <h1 class="edu-page-title">
            <el-icon><Files /></el-icon> 招投标信息
          </h1>
          <p class="edu-page-subtitle">广东省教育行业采购公告与中标公告智能配对视图。<span v-if="activeProcurement">当前选中：<strong>{{ activeProcurement.title }}</strong></span></p>
        </div>
        <div class="edu-page-meta">
          <el-tag type="info">更新：{{ updated }}</el-tag>
          <el-tag type="success">匹配 {{ matchedCount }} 项</el-tag>
        </div>
      </div>

      <!-- 统计摘要 -->
      <div class="edu-bidding-summary edu-card">
        <div class="edu-bidding-summary__item">
          <div class="edu-bidding-summary__value edu-bidding-summary__value--blue">{{ procurementCount }}</div>
          <div class="edu-bidding-summary__label">📋 采购公告</div>
        </div>
        <div class="edu-bidding-summary__item">
          <div class="edu-bidding-summary__value edu-bidding-summary__value--orange">{{ winningCount }}</div>
          <div class="edu-bidding-summary__label">🏆 中标项目</div>
        </div>
        <div class="edu-bidding-summary__item">
          <div class="edu-bidding-summary__value edu-bidding-summary__value--green">{{ matchedCount }}</div>
          <div class="edu-bidding-summary__label">✅ 已匹配</div>
        </div>
        <div class="edu-bidding-summary__item">
          <div class="edu-bidding-summary__value edu-bidding-summary__value--gray">{{ unmatchedProcurement }}</div>
          <div class="edu-bidding-summary__label">⏳ 待匹配</div>
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
        <el-select v-model="matchFilter" placeholder="匹配状态" clearable class="edu-filter-select">
          <el-option label="已匹配" value="matched" />
          <el-option label="待匹配" value="unmatched" />
        </el-select>
        <div class="edu-filter-bar__spacer"></div>
        <el-button :icon="Refresh" @click="resetFilter">重置</el-button>
      </div>

      <!-- ⭐ 核心：左右配对视图 -->
      <div class="edu-paired-view">
        <!-- 左侧：采购公告 -->
        <div class="edu-paired-view__col">
          <div class="edu-paired-view__header edu-paired-view__header--left">
            <el-icon><ShoppingCart /></el-icon>
            <span>采购公告</span>
            <el-tag size="small" type="info">{{ filteredProcurement.length }}</el-tag>
          </div>
          <div class="edu-paired-list edu-paired-list--left">
            <div
              v-for="item in filteredProcurement"
              :key="item.id"
              class="edu-paired-item"
              :class="{ 'is-matched': hasMatched(item), 'is-active': activeProcurementId === item.id }"
              @click="selectProcurement(item.id)"
            >
              <div class="edu-paired-item__status">
                <el-icon v-if="hasMatched(item)" class="is-matched"><CircleCheckFilled /></el-icon>
                <el-icon v-else class="is-unmatched"><QuestionFilled /></el-icon>
              </div>
              <div class="edu-paired-item__body">
                <h4 class="edu-paired-item__title">{{ item.title }}</h4>
                <div class="edu-paired-item__meta">
                  <span class="edu-tag">{{ item.type || '招标公告' }}</span>
                  <span v-if="item.region" class="edu-tag edu-tag--accent">{{ item.region }}</span>
                  <span v-if="item.stage">{{ item.stage }}</span>
                  <span v-if="item.matchedIds?.length" class="edu-paired-item__match-info">→ {{ item.matchedIds.length }} 个中标</span>
                </div>
                <div class="edu-paired-item__sub">
                  <el-icon><OfficeBuilding /></el-icon>
                  <span>{{ item.school || '待确认' }}</span>
                </div>
              </div>
            </div>
            <el-empty v-if="filteredProcurement.length === 0" description="暂无采购公告" />
          </div>
        </div>

        <!-- 中间连接符 -->
        <div class="edu-paired-view__connector">
          <div class="edu-paired-view__connector-inner" :class="{ 'is-connected': activeDisplayMode === 'single' && displayedWinning.length > 0 }">
            <el-icon :size="28"><Link /></el-icon>
          </div>
        </div>

        <!-- 右侧：中标公告（根据选中状态动态显示） -->
        <div class="edu-paired-view__col">
          <div class="edu-paired-view__header edu-paired-view__header--right">
            <el-icon><Trophy /></el-icon>
            <span>{{ activeDisplayMode === 'single' ? '匹配的中标公告' : '中标公告（全量）' }}</span>
            <el-tag size="small" type="success">{{ displayedWinning.length }}</el-tag>
            <el-button v-if="activeDisplayMode === 'single'" type="primary" link size="small" @click="clearSelection">↺ 查看全部</el-button>
          </div>
          <div class="edu-paired-list edu-paired-list--right">
            <!-- 有匹配结果 -->
            <template v-if="displayedWinning.length > 0">
              <div
                v-for="item in displayedWinning"
                :key="item.id"
                class="edu-paired-item edu-paired-item--winning"
              >
                <div class="edu-paired-item__status edu-paired-item__status--right">
                  <el-icon class="is-winning"><Trophy /></el-icon>
                </div>
                <div class="edu-paired-item__body">
                  <h4 class="edu-paired-item__title">{{ item.title }}</h4>
                  <div class="edu-paired-item__meta">
                    <span v-if="item.projectCode" class="edu-tag edu-tag--accent">{{ item.projectCode }}</span>
                    <span v-if="item.region" class="edu-tag">{{ item.region }}</span>
                    <span v-if="item.contractNo">📦 {{ item.contractNo }}</span>
                    <span class="edu-paired-item__attachs">📎 {{ item.attachCount || item.attachments?.length || 0 }} 份附件</span>
                  </div>
                  <div class="edu-paired-item__sub">
                    <el-icon><OfficeBuilding /></el-icon>
                    <span>{{ item.school || '待确认' }}</span>
                    <span class="edu-paired-item__divider">·</span>
                    <span>{{ item.stage }}</span>
                  </div>
                </div>
              </div>
            </template>
            <!-- 选中了采购但没匹配上 -->
            <div v-else-if="activeDisplayMode === 'single'" class="edu-paired-empty">
              <el-icon :size="48" color="#CBD5E1"><WarningFilled /></el-icon>
              <p class="edu-paired-empty__title">暂未匹配到中标公告</p>
              <p class="edu-paired-empty__desc">该采购公告可能尚未发布中标结果，或项目名称存在差异导致未自动关联。</p>
            </div>
            <!-- 全量模式 -->
            <el-empty v-else description="暂无中标公告数据" />
          </div>
        </div>
      </div>

      <!-- 底部提示 -->
      <div class="edu-bidding-tip edu-card">
        <el-icon><InfoFilled /></el-icon>
        <span>💡 <strong>使用提示：</strong>点击左侧任意采购公告，右侧将展示对应匹配的中标公告；点击"↺ 查看全部"可恢复全量视图。匹配逻辑基于学校名称 + 项目关键词自动关联，后续将通过解析 PDF/Docx 提取结构化字段提升准确率。</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import {
  Files, Search, Refresh, ShoppingCart, Trophy, CircleCheckFilled, QuestionFilled,
  Link, OfficeBuilding, WarningFilled, InfoFilled
} from '@element-plus/icons-vue'

const rawData = ref({ procurement: [], winning: [], updated: '—' })
const keyword = ref('')
const regionFilter = ref('')
const stageFilter = ref('')
const matchFilter = ref('')
const activeProcurementId = ref(null) // null = 显示全部中标；有值 = 只显示该采购匹配的中标
const updated = ref('—')

const procurementList = computed(() => rawData.value.procurement || [])
const winningList = computed(() => rawData.value.winning || [])

const hasMatched = (procItem) => !!procItem.matchedIds && procItem.matchedIds.length > 0

const regions = computed(() => {
  const set = new Set()
  procurementList.value.forEach(p => p.region && set.add(p.region))
  winningList.value.forEach(w => w.region && set.add(w.region))
  return [...set].sort()
})

const filteredProcurement = computed(() => {
  return procurementList.value.filter(item => {
    if (keyword.value && !item.title?.toLowerCase().includes(keyword.value.toLowerCase()) &&
        !item.school?.includes(keyword.value)) return false
    if (regionFilter.value && item.region !== regionFilter.value) return false
    if (stageFilter.value && item.stage !== stageFilter.value) return false
    if (matchFilter.value === 'matched' && !hasMatched(item)) return false
    if (matchFilter.value === 'unmatched' && hasMatched(item)) return false
    return true
  })
})

const activeProcurement = computed(() =>
  activeProcurementId.value ? procurementList.value.find(p => p.id === activeProcurementId.value) : null
)

const activeDisplayMode = computed(() => activeProcurement.value ? 'single' : 'all')

const displayedWinning = computed(() => {
  if (activeDisplayMode.value === 'single') {
    const ids = activeProcurement.value?.matchedIds || []
    return winningList.value.filter(w => ids.includes(w.id))
  }
  // 全量视图也受左侧筛选条件影响
  let list = winningList.value
  if (regionFilter.value) list = list.filter(w => w.region === regionFilter.value)
  if (stageFilter.value) list = list.filter(w => w.stage === stageFilter.value)
  if (keyword.value) {
    const kw = keyword.value.toLowerCase()
    list = list.filter(w => w.title?.toLowerCase().includes(kw) || w.school?.includes(keyword.value))
  }
  return list
})

const procurementCount = computed(() => procurementList.value.length)
const winningCount = computed(() => winningList.value.length)
const matchedCount = computed(() => procurementList.value.filter(p => hasMatched(p)).length)
const unmatchedProcurement = computed(() => procurementCount.value - matchedCount.value)

const selectProcurement = (id) => {
  activeProcurementId.value = activeProcurementId.value === id ? null : id
}
const clearSelection = () => { activeProcurementId.value = null }

const resetFilter = () => {
  keyword.value = ''
  regionFilter.value = ''
  stageFilter.value = ''
  matchFilter.value = ''
}

onMounted(async () => {
  try {
    const res = await fetch(import.meta.env.BASE_URL + 'data/bidding.json')
    rawData.value = await res.json()
    updated.value = rawData.value.updated || '—'
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
  align-items: center;
  gap: 4px;
  font-size: var(--edu-font-xs);
  color: var(--edu-text-secondary);
}
.edu-paired-item__sub .el-icon { font-size: 12px; }
.edu-paired-item__divider { margin: 0 4px; color: var(--edu-border); }

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

/* 提示条 */
.edu-bidding-tip {
  display: flex;
  align-items: flex-start;
  gap: var(--edu-space-3);
  padding: var(--edu-space-3) var(--edu-space-4);
  background: #FFFBEB;
  border: 1px solid #FDE68A;
  color: #92400E;
  font-size: var(--edu-font-sm);
  line-height: 1.7;
}
.edu-bidding-tip .el-icon { flex-shrink: 0; font-size: 18px; padding-top: 2px; }

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
