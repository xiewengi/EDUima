<template>
  <div class="edu-exhibition edu-page">
    <div class="edu-container">
      <!-- 页面标题 -->
      <div class="edu-page-header">
        <div>
          <h1 class="edu-page-title">
            <el-icon><Flag /></el-icon> 重磅展会
          </h1>
          <p class="edu-page-subtitle">国内教育信息化领域<b>重点展会 / 大会</b>精选（装备展览 + 会议论坛），时间地点经人工核验，点击卡片直达官网或权威通知。</p>
        </div>
        <div class="edu-page-meta">
          <el-tag type="info">更新：{{ updated }}</el-tag>
          <el-tag type="success">{{ items.length }} 条</el-tag>
        </div>
      </div>

      <!-- 三列卡片：图 + 摘要 + 跳原文（口径同招投标页三列网格） -->
      <div class="edu-paired-view">
        <div class="edu-paired-view__col edu-paired-view__col--full">
          <div class="edu-paired-list edu-paired-list--full">
            <template v-if="items.length > 0">
              <div
                v-for="(item, idx) in items"
                :key="item.id"
                class="edu-exhibition-card"
              >
                <!-- 头图：无图用本地主题图轮换，再失败降级渐变 -->
                <a class="edu-exhibition-card__cover" :href="item.url" target="_blank" rel="noopener">
                  <img
                    v-if="!item._fbFail"
                    :src="item.image || fallbackImg(item)"
                    :alt="item.title"
                    referrerpolicy="no-referrer"
                    loading="lazy"
                    @error="onImgError(item)"
                  />
                  <div v-else class="edu-exhibition-card__fallback"><span>📣</span></div>
                  <span class="edu-exhibition-card__source">{{ item.source }}</span>
                </a>
                <div class="edu-exhibition-card__body">
                  <h4 class="edu-exhibition-card__title" :title="item.title">{{ item.title }}</h4>
                  <p v-if="item.summary" class="edu-exhibition-card__summary">{{ item.summary }}</p>
                  <div class="edu-exhibition-card__foot">
                    <span class="edu-exhibition-card__date">{{ item.date || '—' }}</span>
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
            <el-empty v-else description="暂无展会资讯" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Flag, Link } from '@element-plus/icons-vue'

const items = ref([])
const updated = ref('—')

// 无图条目的本地主题占位图（中国校园/教育科技场景，AI 生成已入库 public/images/exhibition/）
// ⚠️ 与 ThinkTank.vue 的占位图池完全错开，两页之间不允许出现同一张图（2026-10-14 老大反馈）
const FALLBACKS = [
  'fb-classroom.jpg', 'fb-smartclass.png', 'fb-expo.png', 'fb-robot.png',
  'fb-campus.png', 'fb-coding.png', 'fb-library.png', 'fb-digital.jpg',
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
    const res = await fetch(import.meta.env.BASE_URL + 'data/exhibition.json?v=' + Date.now())
    const data = await res.json()
    items.value = data.items || []
    fbNext = 0
    items.value.forEach((it) => { if (!it.image) it._fb = fbNext++ })
    updated.value = (data.updatedAt || '').slice(0, 10) || '—'
  } catch (e) {
    console.error('Failed to load exhibition data:', e)
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
.edu-exhibition.edu-page :deep(.edu-paired-list.edu-paired-list--full) {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--edu-space-3);
  max-height: none;
  overflow-y: visible;
  padding: var(--edu-space-3);
}
@media (max-width: 1200px) {
  .edu-exhibition.edu-page :deep(.edu-paired-list.edu-paired-list--full) { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 720px) {
  .edu-exhibition.edu-page :deep(.edu-paired-list.edu-paired-list--full) { grid-template-columns: 1fr; }
}

/* 卡片 */
.edu-exhibition-card {
  display: flex;
  flex-direction: column;
  border: 1px solid var(--edu-border-light);
  border-radius: var(--edu-radius-md);
  background: #fff;
  overflow: hidden;
  transition: box-shadow 0.2s, transform 0.2s;
}
.edu-exhibition-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
  transform: translateY(-2px);
}

/* 头图 */
.edu-exhibition-card__cover {
  position: relative;
  display: block;
  aspect-ratio: 16 / 9;
  background: var(--edu-bg-hover);
  overflow: hidden;
}
.edu-exhibition-card__cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
.edu-exhibition-card__fallback {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 40px;
  background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%);
}
.edu-exhibition-card__source {
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
.edu-exhibition-card__body {
  display: flex;
  flex-direction: column;
  gap: var(--edu-space-2);
  padding: var(--edu-space-3);
  flex: 1;
  min-width: 0;
}
.edu-exhibition-card__title {
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
.edu-exhibition-card__summary {
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
.edu-exhibition-card__foot {
  margin-top: auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--edu-space-2);
}
.edu-exhibition-card__date {
  font-size: var(--edu-font-xs);
  color: var(--edu-text-placeholder);
  font-variant-numeric: tabular-nums;
}
</style>
