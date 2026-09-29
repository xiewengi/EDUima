<template>
  <div class="edu-home edu-page">
    <div class="edu-container">
      <!-- Hero 区 -->
      <section class="edu-hero edu-card">
        <div class="edu-hero__left">
          <h1 class="edu-hero__title">教育行业知识服务平台</h1>
          <p class="edu-hero__subtitle">
            汇聚广东省教育政策、招投标信息、行业解决方案与生态图谱，<br />
            助力教育数字化转型升级。
          </p>
          <div class="edu-hero__actions">
            <el-button type="primary" size="large" :icon="Document" @click="router.push('/policy')">
              浏览政策
            </el-button>
            <el-button size="large" :icon="Files" plain @click="router.push('/bidding')">
              查看招投标
            </el-button>
          </div>
        </div>
        <div class="edu-hero__right">
          <div class="edu-hero__illustration">
            <div class="edu-hero__circle edu-hero__circle--1"></div>
            <div class="edu-hero__circle edu-hero__circle--2"></div>
            <div class="edu-hero__book">📚</div>
            <div class="edu-hero__data">📊</div>
            <div class="edu-hero__network">🌐</div>
          </div>
        </div>
      </section>

      <!-- 数据概览 -->
      <section class="edu-section">
        <h2 class="edu-section-title">数据概览</h2>
        <div class="edu-metrics">
          <div class="edu-metric edu-card">
            <div class="edu-metric__icon edu-metric__icon--blue">
              <el-icon :size="28"><Document /></el-icon>
            </div>
            <div class="edu-metric__info">
              <div class="edu-metric__value">{{ metrics.totalPolicies }}</div>
              <div class="edu-metric__label">政策条目</div>
            </div>
          </div>
          <div class="edu-metric edu-card">
            <div class="edu-metric__icon edu-metric__icon--orange">
              <el-icon :size="28"><Trophy /></el-icon>
            </div>
            <div class="edu-metric__info">
              <div class="edu-metric__value">{{ metrics.totalWinning }}</div>
              <div class="edu-metric__label">中标公告</div>
            </div>
          </div>
          <div class="edu-metric edu-card">
            <div class="edu-metric__icon edu-metric__icon--green">
              <el-icon :size="28"><ShoppingCart /></el-icon>
            </div>
            <div class="edu-metric__info">
              <div class="edu-metric__value">{{ metrics.totalProcurement }}</div>
              <div class="edu-metric__label">采购公告</div>
            </div>
          </div>
          <div class="edu-metric edu-card">
            <div class="edu-metric__icon edu-metric__icon--purple">
              <el-icon :size="28"><RefreshRight /></el-icon>
            </div>
            <div class="edu-metric__info">
              <div class="edu-metric__value">{{ metrics.updatedAt }}</div>
              <div class="edu-metric__label">最近更新</div>
            </div>
          </div>
        </div>
      </section>

      <!-- 最新动态（双栏） -->
      <section class="edu-section">
        <div class="edu-columns">
          <!-- 最新政策 -->
          <div class="edu-columns__col">
            <div class="edu-card edu-card--header">
              <div class="edu-card__header">
                <h3 class="edu-card__title">
                  <el-icon><Document /></el-icon> 最新政策动态
                </h3>
                <el-link type="primary" @click="router.push('/policy')">查看全部 →</el-link>
              </div>
              <ul class="edu-list">
                <li v-for="item in latestPolicies" :key="item.title" class="edu-list__item">
                  <span class="edu-tag" v-if="item.category">{{ item.category }}</span>
                  <span class="edu-list__title">{{ item.title }}</span>
                  <span class="edu-list__date">{{ item.date }}</span>
                </li>
                <li v-if="latestPolicies.length === 0" class="edu-list__empty">暂无数据</li>
              </ul>
            </div>
          </div>

          <!-- 最新中标 -->
          <div class="edu-columns__col">
            <div class="edu-card edu-card--header">
              <div class="edu-card__header">
                <h3 class="edu-card__title">
                  <el-icon><Trophy /></el-icon> 最新中标公告
                </h3>
                <el-link type="primary" @click="router.push('/bidding')">查看全部 →</el-link>
              </div>
              <ul class="edu-list">
                <li v-for="item in latestWinnings" :key="item.id" class="edu-list__item">
                  <span class="edu-tag edu-tag--accent">{{ item.region }}</span>
                  <span class="edu-list__title">{{ item.title }}</span>
                  <span class="edu-list__date">{{ item.publishDate }}</span>
                </li>
                <li v-if="latestWinnings.length === 0" class="edu-list__empty">暂无数据</li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      <!-- 快捷入口 -->
      <section class="edu-section">
        <h2 class="edu-section-title">快捷入口</h2>
        <div class="edu-quick">
          <router-link to="/bidding" class="edu-quick__item edu-card edu-card--clickable">
            <div class="edu-quick__icon edu-quick__icon--blue"><el-icon :size="32"><Files /></el-icon></div>
            <div class="edu-quick__text">
              <div class="edu-quick__name">招投标信息</div>
              <div class="edu-quick__desc">采购与中标数据配对查询</div>
            </div>
          </router-link>
          <router-link to="/policy" class="edu-quick__item edu-card edu-card--clickable">
            <div class="edu-quick__icon edu-quick__icon--orange"><el-icon :size="32"><Document /></el-icon></div>
            <div class="edu-quick__text">
              <div class="edu-quick__name">政策动态</div>
              <div class="edu-quick__desc">国家与广东省政策文件库</div>
            </div>
          </router-link>
          <router-link to="/solutions" class="edu-quick__item edu-card edu-card--clickable">
            <div class="edu-quick__icon edu-quick__icon--green"><el-icon :size="32"><Lightning /></el-icon></div>
            <div class="edu-quick__text">
              <div class="edu-quick__name">解决方案</div>
              <div class="edu-quick__desc">教育数字化方案集合</div>
            </div>
          </router-link>
          <router-link to="/ecosystem" class="edu-quick__item edu-card edu-card--clickable">
            <div class="edu-quick__icon edu-quick__icon--purple"><el-icon :size="32"><Share /></el-icon></div>
            <div class="edu-quick__text">
              <div class="edu-quick__name">生态图谱</div>
              <div class="edu-quick__desc">教育产业关系网络可视化</div>
            </div>
          </router-link>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Document, Trophy, ShoppingCart, RefreshRight, Files, Lightning, Share } from '@element-plus/icons-vue'

const router = useRouter()

const policyData = ref({ categories: [] })
const biddingData = ref({ procurement: [], winning: [] })

const metrics = computed(() => ({
  totalPolicies: policyData.value.categories.reduce((sum, c) => sum + (c.items?.length || 0), 0),
  totalProcurement: biddingData.value.procurement?.length || 0,
  totalWinning: biddingData.value.winning?.length || 0,
  updatedAt: biddingData.value.updated || '—'
}))

const latestPolicies = computed(() => {
  const list = []
  policyData.value.categories.forEach(cat => {
    (cat.items || []).slice(0, 2).forEach(item => {
      list.push({ ...item, category: cat.name?.replace('（广东省）', '').replace('通用', '') || '' })
    })
  })
  return list.sort((a, b) => (b.date || '').localeCompare(a.date || '')).slice(0, 5)
})

const latestWinnings = computed(() => {
  return [...(biddingData.value.winning || [])]
    .sort((a, b) => (b.publishDate || '').localeCompare(a.publishDate || ''))
    .slice(0, 5)
})

onMounted(async () => {
  try {
    const [pRes, bRes] = await Promise.all([
      fetch(import.meta.env.BASE_URL + 'data/policy.json').then(r => r.json()),
      fetch(import.meta.env.BASE_URL + 'data/bidding.json').then(r => r.json())
    ])
    policyData.value = pRes
    biddingData.value = bRes
  } catch (e) {
    console.error('Failed to load data:', e)
  }
})
</script>

<style scoped>
.edu-hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 60px var(--edu-space-7);
  background: linear-gradient(135deg, var(--edu-primary) 0%, #2D7BD8 100%);
  color: #fff;
  border: none;
  border-radius: var(--edu-radius-xl);
  overflow: hidden;
  position: relative;
}
.edu-hero::before {
  content: '';
  position: absolute;
  top: -100px;
  right: -100px;
  width: 400px;
  height: 400px;
  border-radius: 50%;
  background: rgba(255,255,255,0.08);
}
.edu-hero::after {
  content: '';
  position: absolute;
  bottom: -80px;
  left: 40%;
  width: 300px;
  height: 300px;
  border-radius: 50%;
  background: rgba(255,255,255,0.05);
}
.edu-hero__left {
  position: relative;
  z-index: 1;
  max-width: 560px;
}
.edu-hero__title {
  font-size: 36px;
  font-weight: 700;
  line-height: 1.3;
  margin: 0 0 var(--edu-space-4);
}
.edu-hero__subtitle {
  font-size: var(--edu-font-md);
  line-height: 1.8;
  opacity: 0.92;
  margin-bottom: var(--edu-space-5);
}
.edu-hero__actions {
  display: flex;
  gap: var(--edu-space-3);
}
.edu-hero__actions .el-button + .el-button {
  margin-left: 0;
}
.edu-hero__right {
  position: relative;
  z-index: 1;
  width: 300px;
  height: 240px;
}
.edu-hero__illustration {
  position: relative;
  width: 100%;
  height: 100%;
}
.edu-hero__book, .edu-hero__data, .edu-hero__network {
  position: absolute;
  font-size: 48px;
  filter: drop-shadow(0 4px 8px rgba(0,0,0,0.2));
  animation: float 4s ease-in-out infinite;
}
.edu-hero__book { top: 20px; left: 30px; animation-delay: 0s; }
.edu-hero__data { top: 60px; right: 20px; animation-delay: 1s; font-size: 40px; }
.edu-hero__network { bottom: 10px; left: 80px; animation-delay: 2s; font-size: 44px; }

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

.edu-section {
  margin-top: var(--edu-space-7);
}

.edu-metrics {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--edu-space-4);
}
.edu-metric {
  display: flex;
  align-items: center;
  gap: var(--edu-space-4);
  padding: var(--edu-space-5);
}
.edu-metric__icon {
  width: 56px;
  height: 56px;
  border-radius: var(--edu-radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.edu-metric__icon--blue { background: var(--edu-primary-light); color: var(--edu-primary); }
.edu-metric__icon--orange { background: #FEF3E2; color: var(--edu-accent-hover); }
.edu-metric__icon--green { background: var(--edu-success-light); color: var(--edu-success); }
.edu-metric__icon--purple { background: #EDE9FE; color: #7C3AED; }
.edu-metric__value {
  font-size: var(--edu-font-2xl);
  font-weight: 700;
  color: var(--edu-text-primary);
  font-variant-numeric: tabular-nums;
}
.edu-metric__label {
  font-size: var(--edu-font-sm);
  color: var(--edu-text-secondary);
}

.edu-columns {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--edu-space-4);
}
.edu-card--header .edu-card__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--edu-space-4) var(--edu-space-5);
  border-bottom: 1px solid var(--edu-border-light);
}
.edu-card__title {
  font-size: var(--edu-font-md);
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: var(--edu-space-2);
  color: var(--edu-text-primary);
  margin: 0;
}
.edu-list {
  list-style: none;
  padding: 0;
  margin: 0;
}
.edu-list__item {
  display: flex;
  align-items: center;
  gap: var(--edu-space-2);
  padding: var(--edu-space-3) var(--edu-space-5);
  border-bottom: 1px solid var(--edu-border-light);
  transition: background 0.2s;
}
.edu-list__item:last-child {
  border-bottom: none;
}
.edu-list__item:hover {
  background: var(--edu-bg-hover);
}
.edu-list__title {
  flex: 1;
  font-size: var(--edu-font-base);
  color: var(--edu-text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  cursor: pointer;
}
.edu-list__title:hover {
  color: var(--edu-primary);
}
.edu-list__date {
  font-size: var(--edu-font-xs);
  color: var(--edu-text-placeholder);
  white-space: nowrap;
}
.edu-list__empty {
  padding: var(--edu-space-5);
  text-align: center;
  color: var(--edu-text-placeholder);
  font-size: var(--edu-font-sm);
}

.edu-quick {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--edu-space-4);
}
.edu-quick__item {
  display: flex;
  align-items: center;
  gap: var(--edu-space-4);
  padding: var(--edu-space-5);
  text-decoration: none;
  color: inherit;
}
.edu-quick__item:hover {
  transform: translateY(-2px);
}
.edu-quick__icon {
  width: 56px;
  height: 56px;
  border-radius: var(--edu-radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: #fff;
}
.edu-quick__icon--blue { background: var(--edu-primary); }
.edu-quick__icon--orange { background: var(--edu-accent); }
.edu-quick__icon--green { background: var(--edu-success); }
.edu-quick__icon--purple { background: #7C3AED; }
.edu-quick__name {
  font-size: var(--edu-font-md);
  font-weight: 600;
  margin-bottom: 4px;
}
.edu-quick__desc {
  font-size: var(--edu-font-sm);
  color: var(--edu-text-secondary);
}

@media (max-width: 960px) {
  .edu-hero { flex-direction: column; padding: 40px var(--edu-space-5); text-align: center; }
  .edu-hero__title { font-size: 28px; }
  .edu-hero__actions { justify-content: center; }
  .edu-hero__right { display: none; }
  .edu-metrics { grid-template-columns: repeat(2, 1fr); }
  .edu-columns { grid-template-columns: 1fr; }
  .edu-quick { grid-template-columns: repeat(2, 1fr); }
}
</style>
