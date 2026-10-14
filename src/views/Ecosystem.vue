<template>
  <div class="edu-ecosystem edu-page">
    <div class="edu-container">
      <!-- 页面标题 -->
      <div class="edu-page-header">
        <div>
          <h1 class="edu-page-title">
            <el-icon><Share /></el-icon> 生态图谱
          </h1>
          <p class="edu-page-subtitle">教育信息化 / 智能化<b>供应商名录</b>，涵盖主流厂商的简介与联系方式，点击卡片查看详情。</p>
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

      <!-- 供应商卡片：三列网格，每页 12 家 -->
      <div v-if="pagedItems.length > 0" class="edu-eco-grid">
        <div
          v-for="v in pagedItems"
          :key="v.id"
          class="edu-eco-card edu-card"
          role="button"
          tabindex="0"
          @click="openDetail(v)"
          @keydown.enter="openDetail(v)"
        >
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
              @click.stop
            >
              <el-icon><Link /></el-icon> 官网
            </a>
          </div>
        </div>
      </div>
      <el-empty v-else-if="loaded" description="没有匹配的供应商，换个关键词试试" />

      <!-- 分页：每页 12 家 -->
      <div v-if="filtered.length > PAGE_SIZE" class="edu-eco-pager">
        <el-pagination
          :current-page="currentPage"
          :page-size="PAGE_SIZE"
          :total="filtered.length"
          layout="prev, pager, next, total"
          background
          @current-change="onPageChange"
        />
      </div>

      <!-- 供应商详情弹窗 -->
      <el-dialog
        v-model="detailVisible"
        width="600px"
        :show-close="true"
        class="edu-eco-dialog"
        @closed="detail = null"
      >
        <template v-if="detail" #header>
          <div class="edu-eco-detail__head" :style="{ '--cat-color': catColor(detail.category) }">
            <span class="edu-eco-detail__stripe"></span>
            <div class="edu-eco-detail__head-main">
              <h3 class="edu-eco-detail__name">{{ detail.name }}</h3>
              <p v-if="detail.fullName" class="edu-eco-detail__full">{{ detail.fullName }}</p>
              <div class="edu-eco-detail__tags">
                <span class="edu-eco-detail__cat" :style="{ background: catColor(detail.category) }">
                  {{ detail.category }}
                </span>
                <span v-if="detail.city" class="edu-eco-detail__city">📍 {{ detail.city }}</span>
              </div>
            </div>
          </div>
        </template>

        <template v-if="detail">
          <div class="edu-eco-detail__section">
            <h4 class="edu-eco-detail__label">供应商简介</h4>
            <p class="edu-eco-detail__summary">{{ detail.summary }}</p>
          </div>

          <div class="edu-eco-detail__section">
            <h4 class="edu-eco-detail__label">联系与访问</h4>
            <div class="edu-eco-detail__rows">
              <div class="edu-eco-detail__row">
                <span class="edu-eco-detail__row-label">
                  <el-icon><Phone /></el-icon> 客服电话
                </span>
                <a v-if="detail.phone" class="edu-eco-detail__row-value edu-eco-detail__phone" :href="'tel:' + detail.phone.replace(/[^0-9+]/g, '')">
                  {{ detail.phone }}
                </a>
                <span v-else class="edu-eco-detail__row-value edu-eco-detail__row-value--none">待补充</span>
              </div>
              <div class="edu-eco-detail__row">
                <span class="edu-eco-detail__row-label">
                  <el-icon><Link /></el-icon> 官方网站
                </span>
                <a class="edu-eco-detail__row-value edu-eco-detail__site" :href="detail.website" target="_blank" rel="noopener">
                  {{ siteHost(detail.website) }}
                  <el-icon><TopRight /></el-icon>
                </a>
              </div>
            </div>
          </div>
        </template>

        <template v-if="detail" #footer>
          <el-button @click="detailVisible = false">关闭</el-button>
          <el-button
            v-if="detail.phone"
            @click="copyPhone"
          >
            <el-icon style="margin-right: 4px"><CopyDocument /></el-icon> 复制电话
          </el-button>
          <el-button type="primary" @click="openSite(detail)">
            <el-icon style="margin-right: 4px"><TopRight /></el-icon> 前往官网
          </el-button>
        </template>
      </el-dialog>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { Share, Link, Phone, Search, TopRight, CopyDocument } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const PAGE_SIZE = 12
const items = ref([])
const updated = ref('—')
const loaded = ref(false)
const activeCat = ref('all')
const keyword = ref('')
const currentPage = ref(1)

// ── 详情弹窗 ──
const detail = ref(null)
const detailVisible = ref(false)
const openDetail = (v) => {
  detail.value = v
  detailVisible.value = true
}
const openSite = (v) => { if (v?.website) window.open(v.website, '_blank', 'noopener') }
const copyPhone = async () => {
  try {
    await navigator.clipboard.writeText(detail.value.phone)
    ElMessage.success('电话已复制')
  } catch { ElMessage.error('复制失败，请手动选择复制') }
}
// 官网链接只显示域名，完整 URL 悬停可见
const siteHost = (url) => {
  try { return new URL(url).host.replace(/^www\./, '') } catch { return url }
}

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

// 每页 12 家；筛选/搜索变化时回到第 1 页
const pagedItems = computed(() => {
  const start = (currentPage.value - 1) * PAGE_SIZE
  return filtered.value.slice(start, start + PAGE_SIZE)
})
watch([activeCat, keyword], () => { currentPage.value = 1 })

const onPageChange = (page) => {
  currentPage.value = page
  // 换页后滚回列表顶部，避免停在长列表尾部
  document.querySelector('.edu-eco-grid')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

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
  cursor: pointer;
  transition: box-shadow 0.2s, transform 0.2s;
}
.edu-eco-card:hover,
.edu-eco-card:focus-visible {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
  transform: translateY(-2px);
  outline: none;
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

/* 分页 */
.edu-eco-pager {
  display: flex;
  justify-content: center;
  margin-top: var(--edu-space-5);
}

/* ── 供应商详情弹窗 ── */
/* 弹窗若被 teleport 到 body，scoped 样式够不到弹窗壳，用 :global 兜底 */
:global(.edu-eco-dialog) {
  --el-dialog-padding-primary: 0;
  border-radius: var(--edu-radius-md, 12px);
  overflow: hidden;
}
:global(.edu-eco-dialog .el-dialog__header) { padding: 0; margin-right: 0; }
:global(.edu-eco-dialog .el-dialog__body) { padding: var(--edu-space-4) var(--edu-space-5); }
:global(.edu-eco-dialog .el-dialog__footer) {
  padding: var(--edu-space-3) var(--edu-space-5);
  border-top: 1px solid #ebeef5;
}
/* 底部按钮留足呼吸感（间距 + 统一最小宽度） */
:global(.edu-eco-dialog .el-dialog__footer .el-button + .el-button) { margin-left: 14px; }
:global(.edu-eco-dialog .el-dialog__footer .el-button) { min-width: 88px; }

.edu-eco-detail__head {
  position: relative;
  padding: var(--edu-space-4) var(--edu-space-5);
  background: linear-gradient(135deg, color-mix(in srgb, var(--cat-color) 12%, #fff) 0%, #fff 70%);
  border-bottom: 1px solid #ebeef5;
  overflow: hidden;
  padding-right: 48px; /* 给关闭按钮让位 */
}
.edu-eco-detail__stripe {
  position: absolute;
  left: 0; top: 0; bottom: 0;
  width: 5px;
  background: var(--cat-color);
}
.edu-eco-detail__name {
  margin: 0 0 2px;
  font-size: 20px;
  font-weight: 700;
  color: var(--edu-text-primary, #1f2937);
}
.edu-eco-detail__full {
  margin: 0 0 var(--edu-space-2);
  font-size: var(--edu-font-sm);
  color: var(--edu-text-secondary, #6b7280);
}
.edu-eco-detail__tags {
  display: flex;
  align-items: center;
  gap: var(--edu-space-2);
}
.edu-eco-detail__cat {
  display: inline-block;
  padding: 2px 10px;
  border-radius: var(--edu-radius-pill, 20px);
  color: #fff;
  font-size: var(--edu-font-xs, 12px);
  line-height: 1.6;
}
.edu-eco-detail__city {
  font-size: var(--edu-font-xs, 12px);
  color: var(--edu-text-secondary, #6b7280);
}
.edu-eco-detail__section { margin-bottom: var(--edu-space-4); }
.edu-eco-detail__section:last-child { margin-bottom: 0; }
.edu-eco-detail__label {
  margin: 0 0 var(--edu-space-2);
  font-size: var(--edu-font-xs, 12px);
  font-weight: 600;
  color: var(--edu-text-placeholder, #9ca3af);
  letter-spacing: 0.05em;
}
.edu-eco-detail__summary {
  margin: 0;
  font-size: var(--edu-font-sm);
  line-height: 1.8;
  color: var(--edu-text-primary, #374151);
}
.edu-eco-detail__rows {
  display: flex;
  flex-direction: column;
  gap: 2px;
  border: 1px solid #ebeef5;
  border-radius: var(--edu-radius-md, 12px);
  overflow: hidden;
}
.edu-eco-detail__row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--edu-space-3);
  padding: 10px var(--edu-space-3);
}
.edu-eco-detail__row + .edu-eco-detail__row { border-top: 1px solid #f3f4f6; }
.edu-eco-detail__row-label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: var(--edu-font-sm);
  color: var(--edu-text-secondary, #6b7280);
  flex-shrink: 0;
}
.edu-eco-detail__row-value {
  font-size: var(--edu-font-sm);
  color: var(--edu-text-primary, #374151);
  min-width: 0;
}
.edu-eco-detail__row-value--none { color: var(--edu-text-placeholder, #9ca3af); font-style: italic; }
.edu-eco-detail__phone {
  font-family: ui-monospace, Menlo, monospace;
  text-decoration: none;
}
.edu-eco-detail__site {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: var(--edu-primary);
  text-decoration: none;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.edu-eco-detail__site:hover { text-decoration: underline; }

@media (max-width: 680px) {
  :global(.edu-eco-dialog) { width: 92% !important; }
}

@media (max-width: 1080px) {
  .edu-eco-grid { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 680px) {
  .edu-eco-grid { grid-template-columns: 1fr; }
}
</style>
