<template>
  <div class="edu-ecosystem edu-page">
    <div class="edu-container">
      <!-- 页面标题 -->
      <div class="edu-page-header">
        <div>
          <h1 class="edu-page-title">
            <el-icon><Share /></el-icon> 生态图谱
          </h1>
          <p class="edu-page-subtitle">教育信息化 / 智能化<b>供应商名录</b>，涵盖主流厂商的简介与联系方式，点击卡片直达官网。</p>
        </div>
        <div class="edu-page-meta">
          <el-tag type="info">更新：{{ updated }}</el-tag>
          <el-tag type="success">{{ filtered.length }} 家</el-tag>
        </div>
      </div>

      <!-- 分类筛选 + 搜索 -->
      <div class="edu-eco-toolbar edu-card">
        <div class="edu-eco-cats">
          <button
            v-for="c in catOptions"
            :key="c.key"
            class="edu-eco-cat"
            :class="{ 'is-active': activeCat === c.key }"
            @click="activeCat = c.key"
          >
            {{ c.label }}<span v-if="c.count" class="edu-eco-cat__num">{{ c.count }}</span>
          </button>
        </div>
        <el-input
          v-model="keyword"
          class="edu-eco-search"
          placeholder="搜索厂商名称 / 简介，如：希沃、录播、一卡通"
          clearable
          :prefix-icon="Search"
        />
      </div>

      <!-- 供应商卡片：三列网格 -->
      <div v-if="filtered.length > 0" class="edu-eco-grid">
        <div v-for="v in filtered" :key="v.id" class="edu-eco-card edu-card">
          <span class="edu-eco-card__stripe" :style="{ background: catColor(v.category) }"></span>
          <div class="edu-eco-card__head">
            <h4 class="edu-eco-card__name" :title="v.fullName || v.name">{{ v.name }}</h4>
            <span class="edu-eco-card__cat" :style="{ color: catColor(v.category) }">{{ v.category }}</span>
          </div>
          <div class="edu-eco-card__meta">
            <span v-if="v.city" class="edu-eco-card__city">📍 {{ v.city }}</span>
            <span v-if="v.fullName" class="edu-eco-card__full" :title="v.fullName">{{ v.fullName }}</span>
          </div>
          <p class="edu-eco-card__desc">{{ v.summary }}</p>
          <div class="edu-eco-card__foot">
            <span v-if="v.phone" class="edu-eco-card__phone">
              <el-icon><Phone /></el-icon> {{ v.phone }}
            </span>
            <span v-else class="edu-eco-card__phone edu-eco-card__phone--none">电话待补充</span>
            <a
              class="edu-eco-card__link"
              :href="v.website"
              target="_blank"
              rel="noopener"
              title="前往供应商官网"
            >
              <el-icon><Link /></el-icon> 官网
            </a>
          </div>
        </div>
      </div>
      <el-empty v-else-if="loaded" description="没有匹配的供应商，换个关键词试试" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Share, Link, Phone, Search } from '@element-plus/icons-vue'

const items = ref([])
const updated = ref('—')
const loaded = ref(false)
const activeCat = ref('all')
const keyword = ref('')

const CAT_COLORS = {
  '智慧教学硬件': '#1E5AA8',
  '软件平台与资源': '#8B5CF6',
  'AI与教育大模型': '#D97706',
  '网络与云服务': '#0E7490',
  '网络安全': '#DC2626',
  '职业教育实训': '#059669',
  '考试信息化': '#7C3AED',
  '校园安防与后勤': '#64748B',
}
const catColor = (c) => CAT_COLORS[c] || '#1E5AA8'

const catOptions = computed(() => {
  const opts = [{ key: 'all', label: '全部', count: items.value.length }]
  const seen = []
  items.value.forEach((v) => { if (!seen.includes(v.category)) seen.push(v.category) })
  seen.forEach((c) => opts.push({
    key: c, label: c, count: items.value.filter((v) => v.category === c).length,
  }))
  return opts
})

const filtered = computed(() => {
  const kw = keyword.value.trim().toLowerCase()
  return items.value.filter((v) => {
    if (activeCat.value !== 'all' && v.category !== activeCat.value) return false
    if (!kw) return true
    return [v.name, v.fullName, v.summary, v.city].some((s) => (s || '').toLowerCase().includes(kw))
  })
})

onMounted(async () => {
  try {
    const res = await fetch(import.meta.env.BASE_URL + 'data/ecosystem.json?v=' + Date.now())
    const data = await res.json()
    items.value = data.items || []
    updated.value = (data.updatedAt || '').slice(0, 10) || '—'
  } catch (e) {
    console.error('Failed to load ecosystem data:', e)
  } finally {
    loaded.value = true
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
}
.edu-page-subtitle {
  color: var(--edu-text-secondary);
  font-size: var(--edu-font-sm);
  margin-top: var(--edu-space-1);
}
.edu-page-meta {
  display: flex;
  gap: var(--edu-space-2);
}

/* 工具条 */
.edu-eco-toolbar {
  padding: var(--edu-space-3) var(--edu-space-4);
  margin-bottom: var(--edu-space-4);
  display: flex;
  flex-direction: column;
  gap: var(--edu-space-3);
}
.edu-eco-cats {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.edu-eco-cat {
  border: 1px solid var(--edu-border-color, #ebeef5);
  background: #fff;
  border-radius: var(--edu-radius-pill, 20px);
  padding: 5px 14px;
  font-size: var(--edu-font-sm);
  color: var(--edu-text-secondary);
  cursor: pointer;
  transition: all 0.2s;
  display: inline-flex;
  align-items: center;
  gap: 5px;
}
.edu-eco-cat:hover { border-color: var(--edu-primary); color: var(--edu-primary); }
.edu-eco-cat.is-active {
  background: var(--edu-primary);
  border-color: var(--edu-primary);
  color: #fff;
}
.edu-eco-cat__num {
  font-size: var(--edu-font-xs, 12px);
  opacity: 0.75;
}
.edu-eco-search { max-width: 360px; }

/* 三列卡片 */
.edu-eco-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--edu-space-4);
}
.edu-eco-card {
  position: relative;
  padding: var(--edu-space-4) var(--edu-space-4) var(--edu-space-3);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.edu-eco-card__stripe {
  position: absolute;
  left: 0; top: 0; bottom: 0;
  width: 4px;
}
.edu-eco-card__head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--edu-space-2);
  margin-bottom: 2px;
}
.edu-eco-card__name {
  font-size: var(--edu-font-md);
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.edu-eco-card__cat {
  font-size: var(--edu-font-xs, 12px);
  flex-shrink: 0;
  font-weight: 500;
}
.edu-eco-card__meta {
  display: flex;
  gap: var(--edu-space-2);
  align-items: center;
  margin-bottom: var(--edu-space-2);
  font-size: var(--edu-font-xs, 12px);
  color: var(--edu-text-secondary);
}
.edu-eco-card__city { flex-shrink: 0; }
.edu-eco-card__full {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.edu-eco-card__desc {
  font-size: var(--edu-font-sm);
  color: var(--edu-text-secondary);
  line-height: 1.6;
  margin-bottom: var(--edu-space-3);
  flex: 1;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.edu-eco-card__foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--edu-space-2);
  border-top: 1px solid var(--edu-border-color, #ebeef5);
  padding-top: var(--edu-space-2);
}
.edu-eco-card__phone {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: var(--edu-font-xs, 12px);
  color: var(--edu-text-secondary);
  font-family: ui-monospace, Menlo, monospace;
}
.edu-eco-card__phone--none { opacity: 0.5; font-style: italic; }
.edu-eco-card__link {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: var(--edu-font-sm);
  color: var(--edu-primary);
  text-decoration: none;
  font-weight: 500;
  flex-shrink: 0;
}
.edu-eco-card__link:hover { text-decoration: underline; }

@media (max-width: 1080px) {
  .edu-eco-grid { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 680px) {
  .edu-eco-grid { grid-template-columns: 1fr; }
}
</style>
