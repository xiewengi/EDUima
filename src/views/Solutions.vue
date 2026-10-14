<template>
  <div class="edu-solutions edu-page">
    <div class="edu-container">
      <!-- 页面标题 -->
      <div class="edu-page-header">
        <div>
          <h1 class="edu-page-title">
            <el-icon><Lightning /></el-icon> 解决方案
          </h1>
          <p class="edu-page-subtitle">主流教育信息化厂商<b>智慧教育 / 数字化解决方案</b>精选，点击卡片直达厂商官网方案页。</p>
        </div>
        <div class="edu-page-meta">
          <el-tag type="info">更新：{{ updated }}</el-tag>
          <el-tag type="success">{{ items.length }} 个方案</el-tag>
        </div>
      </div>

      <!-- 三列卡片：配图 + 摘要 + 跳转官网方案页（口径 2026-10-14：不做彩页下载，只跳官网） -->
      <div v-if="items.length > 0" class="edu-solutions-grid">
        <div v-for="item in items" :key="item.id" class="edu-solution-card edu-card">
          <div class="edu-solution-card__cover">
            <img
              v-if="!item._imgFail"
              :src="imgUrl(item.image)"
              :alt="item.name"
              loading="lazy"
              referrerpolicy="no-referrer"
              @error="item._imgFail = true"
            />
            <div v-else class="edu-solution-card__cover-fallback"><span>🏫</span></div>
            <span class="edu-solution-card__category">{{ item.category }}</span>
          </div>
          <div class="edu-solution-card__body">
            <h4 class="edu-solution-card__name" :title="item.name">{{ item.name }}</h4>
            <div class="edu-solution-card__vendor">{{ item.vendor }}</div>
            <p class="edu-solution-card__desc">{{ item.summary }}</p>
            <div class="edu-solution-card__tags">
              <el-tag v-for="tag in item.tags" :key="tag" size="small" type="info">{{ tag }}</el-tag>
            </div>
            <div class="edu-solution-card__foot">
              <a
                class="edu-solution-card__link"
                :href="item.pageUrl"
                target="_blank"
                rel="noopener"
                title="前往厂商官网查看该方案详情"
              >
                <el-icon><Link /></el-icon> 官网方案
              </a>
            </div>
          </div>
        </div>
      </div>
      <el-empty v-else-if="loaded" description="暂无解决方案数据" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Lightning, Link } from '@element-plus/icons-vue'

const items = ref([])
const updated = ref('—')
const loaded = ref(false)

const imgUrl = (p) => import.meta.env.BASE_URL + p

onMounted(async () => {
  try {
    const res = await fetch(import.meta.env.BASE_URL + 'data/solutions.json?v=' + Date.now())
    const data = await res.json()
    items.value = data.items || []
    updated.value = (data.updatedAt || '').slice(0, 10) || '—'
  } catch (e) {
    console.error('Failed to load solutions data:', e)
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

/* 三列网格（口径同展会页三列布局） */
.edu-solutions-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--edu-space-4);
}
.edu-solution-card {
  padding: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.edu-solution-card__cover {
  position: relative;
  height: 170px;
  background: var(--edu-primary-bg, #eef3f9);
}
.edu-solution-card__cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
.edu-solution-card__cover-fallback {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 48px;
  background: linear-gradient(135deg, #1e5aa8 0%, #3f7fd4 100%);
}
.edu-solution-card__category {
  position: absolute;
  left: 10px;
  bottom: 10px;
  padding: 2px 10px;
  border-radius: var(--edu-radius-md, 6px);
  background: rgba(30, 90, 168, 0.88);
  color: #fff;
  font-size: var(--edu-font-xs, 12px);
  letter-spacing: 1px;
}
.edu-solution-card__body {
  padding: var(--edu-space-4);
  display: flex;
  flex-direction: column;
  flex: 1;
}
.edu-solution-card__name {
  font-size: var(--edu-font-md);
  font-weight: 600;
  line-height: 1.4;
  margin-bottom: 2px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.edu-solution-card__vendor {
  font-size: var(--edu-font-xs, 12px);
  color: var(--edu-primary);
  font-weight: 600;
  margin-bottom: var(--edu-space-2);
}
.edu-solution-card__desc {
  font-size: var(--edu-font-sm);
  color: var(--edu-text-secondary);
  line-height: 1.6;
  margin-bottom: var(--edu-space-3);
  flex: 1;
  display: -webkit-box;
  -webkit-line-clamp: 4;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.edu-solution-card__tags {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
  margin-bottom: var(--edu-space-3);
}
.edu-solution-card__foot {
  display: flex;
  gap: var(--edu-space-3);
  border-top: 1px solid var(--edu-border-color, #ebeef5);
  padding-top: var(--edu-space-3);
}
.edu-solution-card__link {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: var(--edu-font-sm);
  color: var(--edu-primary);
  text-decoration: none;
  font-weight: 500;
}
.edu-solution-card__link:hover {
  text-decoration: underline;
}

@media (max-width: 1080px) {
  .edu-solutions-grid { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 680px) {
  .edu-solutions-grid { grid-template-columns: 1fr; }
}
</style>
