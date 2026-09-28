<template>
  <div class="edu-policy edu-page">
    <div class="edu-container">
      <!-- 页面标题 -->
      <div class="edu-page-header">
        <div>
          <h1 class="edu-page-title">
            <el-icon><Document /></el-icon> 政策动态
          </h1>
          <p class="edu-page-subtitle">汇聚教育部及广东省教育厅发布的教育政策文件，持续同步更新。</p>
        </div>
        <div class="edu-page-meta">
          <el-tag type="info">数据更新：{{ updated }}</el-tag>
          <el-tag type="success">共 {{ total }} 条</el-tag>
        </div>
      </div>

      <!-- Tab 切换 -->
      <el-tabs v-model="activeTab" class="edu-tabs" @tab-change="handleTabChange">
        <el-tab-pane label="全部政策" name="all">
          <template #label>
            <span class="edu-tab-label"><el-icon><Grid /></el-icon> 全部 <span class="edu-tab-count">{{ total }}</span></span>
          </template>
        </el-tab-pane>
        <el-tab-pane label="广东省内" name="guangdong">
          <template #label>
            <span class="edu-tab-label"><el-icon><LocationFilled /></el-icon> 广东省 <span class="edu-tab-count">{{ gdCount }}</span></span>
          </template>
        </el-tab-pane>
        <el-tab-pane label="全国通用" name="national">
          <template #label>
            <span class="edu-tab-label"><el-icon><School /></el-icon> 全国 <span class="edu-tab-count">{{ nationalCount }}</span></span>
          </template>
        </el-tab-pane>
      </el-tabs>

      <!-- 筛选工具栏 -->
      <div class="edu-filter-bar edu-card">
        <el-input
          v-model="keyword"
          placeholder="搜索政策标题..."
          :prefix-icon="Search"
          clearable
          style="width: 280px"
          @input="applyFilter"
        />
        <el-select v-model="typeFilter" placeholder="政策类型" clearable style="width: 160px" @change="applyFilter">
          <el-option label="通知" value="通知" />
          <el-option label="办法" value="办法" />
          <el-option label="意见" value="意见" />
          <el-option label="规划" value="规划" />
          <el-option label="指南" value="指南" />
        </el-select>
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          style="width: 280px"
          @change="applyFilter"
        />
        <el-button :icon="Refresh" @click="resetFilter">重置</el-button>
      </div>

      <!-- 政策列表 -->
      <div class="edu-policy-list">
        <div
          v-for="item in filteredList"
          :key="item.title"
          class="edu-policy-item edu-card"
          @click="openOriginal(item)"
        >
          <div class="edu-policy-item__left">
            <div class="edu-policy-item__date" :class="{ 'is-empty': !item.date }">
              <template v-if="item.date">
                <div class="edu-policy-item__day">{{ formatDay(item.date) }}</div>
                <div class="edu-policy-item__month">{{ formatMonth(item.date) }}</div>
              </template>
              <template v-else>
                <div class="edu-policy-item__day">—</div>
                <div class="edu-policy-item__month">—</div>
              </template>
            </div>
          </div>
          <div class="edu-policy-item__content">
            <h3 class="edu-policy-item__title">{{ item.title }}</h3>
            <div class="edu-policy-item__meta">
              <span v-if="item.doc_no" class="edu-docno-tag">{{ item.doc_no }}</span>
              <span v-if="item.doc_no || item.date" class="edu-text-sep">·</span>
              <span v-if="item.date" class="edu-text-muted">
                <el-icon><Clock /></el-icon> {{ item.date }}
              </span>
              <span v-if="item.doc_no || item.date" class="edu-text-sep">·</span>
              <span class="edu-text-muted">
                <el-icon><School /></el-icon> {{ item.category === 'guangdong' ? '广东省教育厅' : '教育部' }}
              </span>
            </div>
          </div>
          <div class="edu-policy-item__action">
            <el-button
              :icon="item.url ? Link : Search"
              :type="item.url ? 'primary' : 'default'"
              :plain="!item.url"
              circle
              @click.stop="openOriginal(item)"
            />
          </div>
        </div>
        <el-empty v-if="filteredList.length === 0" description="暂无匹配的政策数据" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Document, Grid, LocationFilled, School, Search, Refresh, Link, Clock, OfficeBuilding } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const rawData = ref({ categories: [], site: {} })
const activeTab = ref('all')
const keyword = ref('')
const typeFilter = ref('')
const dateRange = ref([])
const updated = ref('—')

const gdCategory = computed(() => rawData.value.categories.find(c => c.id === 'guangdong') || { items: [] })
const nationalCategory = computed(() => rawData.value.categories.find(c => c.id === 'national') || { items: [] })

const allList = computed(() => {
  const gd = (gdCategory.value.items || []).map(i => ({ ...i, source: '广东省教育厅', category: 'guangdong' }))
  const nat = (nationalCategory.value.items || []).map(i => ({ ...i, source: '教育部', category: 'national' }))
  return [...gd, ...nat].sort((a, b) => (b.date || '').localeCompare(a.date || ''))
})

const filteredList = computed(() => {
  let list = allList.value
  if (activeTab.value === 'guangdong') list = list.filter(i => i.category === 'guangdong')
  if (activeTab.value === 'national') list = list.filter(i => i.category === 'national')
  if (keyword.value) {
    const kw = keyword.value.toLowerCase()
    list = list.filter(i => i.title?.toLowerCase().includes(kw))
  }
  if (dateRange.value && dateRange.value.length === 2) {
    const [start, end] = dateRange.value
    list = list.filter(i => {
      if (!i.date) return false
      const d = new Date(i.date)
      return d >= start && d <= end
    })
  }
  return list
})

const total = computed(() => allList.value.length)
const gdCount = computed(() => gdCategory.value.items?.length || 0)
const nationalCount = computed(() => nationalCategory.value.items?.length || 0)

const formatDay = (date) => {
  if (!date) return '—'
  return date.slice(8, 10) || '—'
}
const formatMonth = (date) => {
  if (!date) return '—'
  return date.slice(0, 7) || '—'
}

const handleTabChange = () => applyFilter()
const applyFilter = () => { /* 计算属性自动响应 */ }
const resetFilter = () => {
  keyword.value = ''
  typeFilter.value = ''
  dateRange.value = []
  activeTab.value = 'all'
}

const openDetail = (item) => {
  // 后续可做详情弹窗/抽屉
  if (item.url) {
    openOriginal(item)
  } else {
    ElMessage.info('政策详情功能开发中...')
  }
}
const openOriginal = (item) => {
  if (item.url) {
    window.open(item.url, '_blank')
  } else {
    // 没 URL → 必应搜索原文
    const site = item.category === 'guangdong' ? 'edu.gd.gov.cn' : 'moe.gov.cn'
    const q = `site:${site} ${item.title}`
    window.open(`https://www.bing.com/search?q=${encodeURIComponent(q)}`, '_blank')
  }
}

onMounted(async () => {
  try {
    const res = await fetch('/data/policy.json')
    rawData.value = await res.json()
    updated.value = rawData.value.site?.updated || rawData.value.updated || '—'
  } catch (e) {
    console.error('Failed to load policy data:', e)
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
.edu-page-meta {
  display: flex;
  gap: var(--edu-space-2);
}

.edu-tabs {
  margin-bottom: var(--edu-space-4);
}
.edu-tabs :deep(.el-tabs__item) {
  font-size: var(--edu-font-base);
}
.edu-tabs :deep(.el-tabs__item.is-active) {
  color: var(--edu-primary);
  font-weight: 600;
}
.edu-tab-label {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
.edu-tab-count {
  background: var(--edu-primary-light);
  color: var(--edu-primary);
  padding: 0 8px;
  border-radius: 10px;
  font-size: var(--edu-font-xs);
  margin-left: 4px;
}

.edu-filter-bar {
  display: flex;
  gap: var(--edu-space-3);
  padding: var(--edu-space-4);
  margin-bottom: var(--edu-space-5);
  flex-wrap: wrap;
  align-items: center;
}

.edu-policy-list {
  display: flex;
  flex-direction: column;
  gap: var(--edu-space-3);
}

.edu-policy-item {
  display: flex;
  align-items: stretch;
  gap: var(--edu-space-5);
  padding: var(--edu-space-4) var(--edu-space-5);
  cursor: pointer;
  transition: all 0.2s;
}
.edu-policy-item:hover {
  border-color: var(--edu-primary);
  box-shadow: var(--edu-shadow-md);
}

.edu-policy-item__left {
  flex-shrink: 0;
  width: 72px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.edu-policy-item__date {
  text-align: center;
  padding: var(--edu-space-2);
  background: var(--edu-primary-light);
  border-radius: var(--edu-radius-md);
  min-width: 56px;
}
.edu-policy-item__day {
  font-size: var(--edu-font-2xl);
  font-weight: 700;
  color: var(--edu-primary);
  line-height: 1;
}
.edu-policy-item__date.is-empty {
  background: #F8FAFC;
}
.edu-policy-item__date.is-empty .edu-policy-item__day {
  font-size: var(--edu-font-lg);
  color: #CBD5E1;
  font-weight: 400;
}
.edu-policy-item__month {
  font-size: var(--edu-font-xs);
  color: var(--edu-primary);
  margin-top: 2px;
}

.edu-policy-item__content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
}
.edu-policy-item__title {
  font-size: var(--edu-font-md);
  font-weight: 600;
  color: var(--edu-text-primary);
  margin: 0 0 var(--edu-space-2);
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}
.edu-policy-item__meta {
  display: flex;
  flex-wrap: wrap;
  gap: var(--edu-space-3);
  align-items: center;
  font-size: var(--edu-font-sm);
}
.edu-policy-item__meta span {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
.edu-text-sep {
  color: #CBD5E1;
  margin: 0 2px;
  font-size: 12px;
}
.edu-docno-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  border-radius: 10px;
  background: linear-gradient(135deg, #EFF6FF, #FEF3C7);
  color: var(--edu-primary);
  font-size: 12px;
  font-weight: 500;
  border: 1px solid rgba(37, 99, 235, 0.15);
  max-width: 240px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.edu-policy-item__meta--hint {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  border-radius: 10px;
  background: #F1F5F9;
  color: #94A3B8;
  font-size: 12px;
  font-style: italic;
}
.edu-text-muted--dim {
  opacity: 0.6;
}

.edu-policy-item__action {
  display: flex;
  flex-direction: column;
  gap: var(--edu-space-2);
  justify-content: center;
  flex-shrink: 0;
}

@media (max-width: 768px) {
  .edu-policy-item { flex-direction: column; gap: var(--edu-space-3); }
  .edu-policy-item__action { flex-direction: row; }
  .edu-filter-bar { padding: var(--edu-space-3); }
}
</style>
