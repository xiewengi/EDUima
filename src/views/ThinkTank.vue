<template>
  <div class="edu-thinktank edu-page">
    <div class="edu-container">
      <!-- 页面标题 -->
      <div class="edu-page-header">
        <div>
          <h1 class="edu-page-title">
            <el-icon><View /></el-icon> 智库观察
          </h1>
          <p class="edu-page-subtitle">权威教育媒体的<b>智库报告 / 观察视角 / 行业趋势</b>洞察精选，点击卡片直达原文。</p>
        </div>
        <div class="edu-page-meta">
          <el-tag type="info">更新：{{ updated }}</el-tag>
          <el-tag type="success">{{ items.length }} 条</el-tag>
        </div>
      </div>

      <!-- 三列卡片：图 + 摘要 + 跳原文（口径同招投标/重磅展会页三列网格） -->
      <div class="edu-paired-view">
        <div class="edu-paired-view__col edu-paired-view__col--full">
          <div class="edu-paired-list edu-paired-list--full">
            <template v-if="items.length > 0">
              <div
                v-for="(item, idx) in items"
                :key="item.id"
                class="edu-thinktank-card"
              >
                <!-- 头图：无图用本地主题图轮换，再失败降级渐变 -->
                <a class="edu-thinktank-card__cover" :href="item.url" target="_blank" rel="noopener">
                  <img
                    v-if="!item._fbFail"
                    :src="item.image || fallbackImg(item)"
                    :alt="item.title"
                    referrerpolicy="no-referrer"
                    loading="lazy"
                    @error="onImgError(item)"
                  />
                  <div v-else class="edu-thinktank-card__fallback"><span>🔍</span></div>
                  <span class="edu-thinktank-card__source">{{ item.source }}</span>
                </a>
                <div class="edu-thinktank-card__body">
                  <h4 class="edu-thinktank-card__title" :title="item.title">{{ item.title }}</h4>
                  <p v-if="item.summary" class="edu-thinktank-card__summary">{{ item.summary }}</p>
                  <div class="edu-thinktank-card__foot">
                    <span class="edu-thinktank-card__date">{{ item.date || '—' }}</span>
                    <a
                      class="edu-paired-item__source"
                      :href="item.url"
                      target="_blank"
                      rel="noopener"
                      title="跳转到原网站查看全文"
                    >
                      <el-icon><Link /></el-icon> 跳转原文
                    </a>
                  </div>
                </div>
              </div>
            </template>
            <el-empty v-else description="暂无智库观察内容" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { View, Link } from '@element-plus/icons-vue'

const items = ref([])
const updated = ref('—')

// 无图条目的本地主题占位图（中国教研/数据科技场景，AI 生成已入库 public/images/exhibition/）
// ⚠️ 与 Exhibition.vue 的占位图池完全错开，两页之间不允许出现同一张图（2026-10-14 老大反馈）
const FALLBACKS = [
  'tt-conference.png', 'tt-datacenter.png', 'tt-screen.png',
  'tt-ai.png', 'tt-lecture.png', 'tt-hall.png', 'tt-lab.png', 'tt-seminar.png',
]
// 占位图按「无图卡片的序号」分配（不能用文章位次取模：无图位次稀疏时会撞同一张）
let fbNext = 0
const fallbackImg = (item) =>
  import.meta.env.BASE_URL + 'images/exhibition/' + FALLBACKS[item._fb % FALLBACKS.length]

// 原图挂了 → 降到本地占位图（补发一个新序号）；占位图也挂了 → 渐变 emoji
const onImgError = (item) => {
  if (item.image) {
    item.image = ''
    if (item._fb === undefined) item._fb = fbNext++
  } else item._fbFail = true
}

onMounted(async () => {
  try {
    const res = await fetch(import.meta.env.BASE_URL + 'data/thinktank.json?v=' + Date.now())
    const data = await res.json()
    items.value = data.items || []
    fbNext = 0
    items.value.forEach((it) => { if (!it.image) it._fb = fbNext++ })
    updated.value = (data.updatedAt || '').slice(0, 10) || '—'
  } catch (e) {
    console.error('Failed to load thinktank data:', e)
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

/* 三列网格容器（复用招投标页 .edu-paired-list--full 的网格口径） */
.edu-thinktank.edu-page :deep(.edu-paired-list.edu-paired-list--full) {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--edu-space-3);
  max-height: none;
  overflow-y: visible;
  padding: var(--edu-space-3);
}
@media (max-width: 1200px) {
  .edu-thinktank.edu-page :deep(.edu-paired-list.edu-paired-list--full) { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 720px) {
  .edu-thinktank.edu-page :deep(.edu-paired-list.edu-paired-list--full) { grid-template-columns: 1fr; }
}

/* 卡片 */
.edu-thinktank-card {
  display: flex;
  flex-direction: column;
  border: 1px solid var(--edu-border-light);
  border-radius: var(--edu-radius-md);
  background: #fff;
  overflow: hidden;
  transition: box-shadow 0.2s, transform 0.2s;
}
.edu-thinktank-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
  transform: translateY(-2px);
}

/* 头图 */
.edu-thinktank-card__cover {
  position: relative;
  display: block;
  aspect-ratio: 16 / 9;
  background: var(--edu-bg-hover);
  overflow: hidden;
}
.edu-thinktank-card__cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
.edu-thinktank-card__fallback {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 40px;
  background: linear-gradient(135deg, #F0FDF4 0%, #DCFCE7 100%);
}
.edu-thinktank-card__source {
  position: absolute;
  left: 8px;
  bottom: 8px;
  padding: 2px 8px;
  border-radius: var(--edu-radius-sm);
  background: rgba(15, 23, 42, 0.65);
  color: #fff;
  font-size: var(--edu-font-xs);
  line-height: 1.5;
  backdrop-filter: blur(4px);
}

/* 内容区 */
.edu-thinktank-card__body {
  display: flex;
  flex-direction: column;
  gap: var(--edu-space-2);
  padding: var(--edu-space-3);
  flex: 1;
  min-width: 0;
}
.edu-thinktank-card__title {
  margin: 0;
  font-size: var(--edu-font-base);
  font-weight: 600;
  color: var(--edu-text-primary);
  line-height: 1.5;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}
.edu-thinktank-card__summary {
  margin: 0;
  font-size: var(--edu-font-xs);
  color: var(--edu-text-secondary);
  line-height: 1.6;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
}
.edu-thinktank-card__foot {
  margin-top: auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--edu-space-2);
}
.edu-thinktank-card__date {
  font-size: var(--edu-font-xs);
  color: var(--edu-text-placeholder);
  font-variant-numeric: tabular-nums;
}
</style>
