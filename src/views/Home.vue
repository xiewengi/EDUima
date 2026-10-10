<template>
  <div class="edu-home">
    <!-- Hero 区（全屏背景图 + 毛玻璃文字卡） -->
    <section class="home-hero">
      <!-- 背景图层 -->
      <div class="home-hero__bg">
        <img :src="heroImg" alt="" />
        <div class="home-hero__overlay home-hero__overlay--dark"></div>
        <div class="home-hero__overlay home-hero__overlay--gradient"></div>
        <div class="home-hero__grid"></div>
      </div>
      <!-- 内容层 -->
      <div class="home-hero__inner">
        <div class="home-hero__card">
          <h1 class="home-hero__title">教育智服 · 知识领航</h1>
          <p class="home-hero__subtitle">教育知识服务平台</p>
          <p class="home-hero__desc">
            汇聚广东省教育政策、招投标信息、行业解决方案与生态图谱，<br />
            助力教育数字化转型升级。
          </p>
          <div class="home-hero__tags">
            <router-link v-for="t in heroTags" :key="t.path" :to="t.path" class="home-tag">
              <el-icon><component :is="t.icon" /></el-icon>
              <span>{{ t.name }}</span>
            </router-link>
          </div>
          <div class="home-hero__cta">
            <button class="home-btn home-btn--primary" @click="router.push('/policy')">
              浏览政策文件 →
            </button>
          </div>
        </div>
      </div>
    </section>

    <!-- 数据指标条 -->
    <section class="edu-container">
      <div class="home-stats">
        <div v-for="s in statItems" :key="s.label" class="home-stat">
          <div class="home-stat__icon">
            <el-icon :size="22"><component :is="s.icon" /></el-icon>
          </div>
          <div class="home-stat__info">
            <div class="home-stat__value">{{ s.value }}</div>
            <div class="home-stat__label">{{ s.label }}</div>
          </div>
        </div>
      </div>
    </section>

    <!-- 最新动态（双栏） -->
    <section class="edu-container home-section">
      <div class="home-columns">
        <!-- 最新政策 -->
        <div class="home-columns__col">
          <div class="home-panel">
            <div class="home-panel__header">
              <div class="home-panel__title">
                <span class="home-panel__dot home-panel__dot--blue"></span>
                最新政策动态
              </div>
              <el-link type="primary" @click="router.push('/policy')" :underline="false">查看全部 →</el-link>
            </div>
            <ul class="home-list">
              <li v-for="item in latestPolicies" :key="item.title" class="home-list__item">
                <span class="home-list__title" @click="openLink(item.url)">{{ item.title }}</span>
                <span class="home-list__date">{{ item.date }}</span>
              </li>
              <li v-if="latestPolicies.length === 0" class="home-list__empty">暂无数据</li>
            </ul>
          </div>
        </div>

        <!-- 最新中标 -->
        <div class="home-columns__col">
          <div class="home-panel">
            <div class="home-panel__header">
              <div class="home-panel__title">
                <span class="home-panel__dot home-panel__dot--orange"></span>
                最新中标公告
              </div>
              <el-link type="primary" @click="router.push('/bidding')" :underline="false">查看全部 →</el-link>
            </div>
            <ul class="home-list">
              <li v-for="item in latestWinnings" :key="item.id" class="home-list__item">
                <span class="home-list__title">{{ item.title }}</span>
                <span class="home-list__date">{{ item.publishDate }}</span>
              </li>
              <li v-if="latestWinnings.length === 0" class="home-list__empty">暂无数据</li>
            </ul>
          </div>
        </div>
      </div>
    </section>

    <!-- 快捷入口 -->
    <section class="edu-container home-section">
      <h2 class="home-section-title">快捷入口</h2>
      <div class="home-quick">
        <router-link to="/bidding" class="home-quick__item">
          <div class="home-quick__icon home-quick__icon--blue"><el-icon :size="28"><Files /></el-icon></div>
          <div class="home-quick__name">招投标信息</div>
        </router-link>
        <router-link to="/policy" class="home-quick__item">
          <div class="home-quick__icon home-quick__icon--orange"><el-icon :size="28"><Document /></el-icon></div>
          <div class="home-quick__name">政策动态</div>
        </router-link>
        <router-link to="/solutions" class="home-quick__item">
          <div class="home-quick__icon home-quick__icon--green"><el-icon :size="28"><Lightning /></el-icon></div>
          <div class="home-quick__name">解决方案</div>
        </router-link>
        <router-link to="/ecosystem" class="home-quick__item">
          <div class="home-quick__icon home-quick__icon--purple"><el-icon :size="28"><Share /></el-icon></div>
          <div class="home-quick__name">生态图谱</div>
        </router-link>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  Document, Trophy, ShoppingCart, Files, Lightning, Share,
  HomeFilled, DataAnalysis, CircleCheck, Calendar, Link
} from '@element-plus/icons-vue'

const router = useRouter()
const heroImg = import.meta.env.BASE_URL + 'assets/hero-edu.jpg'

const heroTags = [
  { name: '政策动态', path: '/policy', icon: Document },
  { name: '招投标', path: '/bidding', icon: Files },
  { name: '解决方案', path: '/solutions', icon: Lightning },
  { name: '生态图谱', path: '/ecosystem', icon: Share },
]

const policyData = ref({ categories: [] })
const biddingData = ref({ procurement: [], winning: [] })

const metrics = computed(() => ({
  totalPolicies: policyData.value.categories.reduce((sum, c) => sum + (c.items?.length || 0), 0),
  totalProcurement: biddingData.value.procurement?.length || 0,
  totalWinning: biddingData.value.winning?.length || 0,
  matchedCount: biddingData.value.matchStats?.matchedCount || 0,
  updatedAt: biddingData.value.updated || '—'
}))

const statItems = computed(() => [
  { label: '政策条目', value: metrics.value.totalPolicies + ' 项', icon: Document },
  { label: '中标公告', value: metrics.value.totalWinning + ' 条', icon: Trophy },
  { label: '采购公告', value: metrics.value.totalProcurement + ' 条', icon: ShoppingCart },
  { label: '匹配对数', value: metrics.value.matchedCount + ' 对', icon: CircleCheck },
  { label: '最近更新', value: metrics.value.updatedAt, icon: Calendar },
  { label: '数据来源', value: '省教育厅', icon: Link },
])

const latestPolicies = computed(() => {
  const list = []
  policyData.value.categories.forEach(cat => {
    (cat.items || []).forEach(item => list.push(item))
  })
  return list.sort((a, b) => (b.date || '').localeCompare(a.date || '')).slice(0, 6)
})

const latestWinnings = computed(() => {
  return [...(biddingData.value.winning || [])]
    .sort((a, b) => (b.publishDate || '').localeCompare(a.publishDate || ''))
    .slice(0, 6)
})

function openLink(url) {
  if (url) window.open(url, '_blank')
}

onMounted(async () => {
  try {
    const ts = Date.now()
    const [pRes, bRes] = await Promise.all([
      fetch(import.meta.env.BASE_URL + 'data/policy.json?v=' + ts).then(r => r.json()),
      fetch(import.meta.env.BASE_URL + 'data/bidding.json?v=' + ts).then(r => r.json())
    ])
    policyData.value = pRes
    biddingData.value = bRes
  } catch (e) {
    console.error('Failed to load data:', e)
  }
})
</script>

<style scoped>
/* ========== Hero ========== */
.home-hero {
  position: relative;
  min-height: 560px;
  overflow: hidden;
}

/* 背景图层 */
.home-hero__bg {
  position: absolute;
  inset: 0;
  z-index: 0;
}
.home-hero__bg img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
  object-position: center 45%;
}
/* 左侧局部渐变遮罩：只压暗文字区域，右边图片原封不动 */
.home-hero__overlay {
  position: absolute;
  inset: 0;
  pointer-events: none;
}
.home-hero__overlay--dark {
  background: linear-gradient(90deg,
    rgba(8, 12, 24, 0.85) 0%,
    rgba(8, 12, 24, 0.70) 25%,
    rgba(8, 12, 24, 0.35) 50%,
    rgba(8, 12, 24, 0.10) 70%,
    rgba(8, 12, 24, 0) 100%);
}
.home-hero__overlay--gradient {
  background: linear-gradient(180deg,
    rgba(8, 12, 24, 0.3) 0%,
    rgba(8, 12, 24, 0) 30%,
    rgba(8, 12, 24, 0) 60%,
    rgba(8, 12, 24, 0.2) 100%);
}
.home-hero__grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(255,255,255,0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,0.05) 1px, transparent 1px);
  background-size: 56px 56px;
  pointer-events: none;
  mix-blend-mode: screen;
  opacity: 0.5;
}

/* 内容层：无卡片，文字直接叠背景 */
.home-hero__inner {
  position: relative;
  z-index: 1;
  max-width: 1360px;
  margin: 0 auto;
  padding: 110px 48px 100px;
  min-height: 560px;
  display: flex;
  align-items: center;
}

/* 文字块：无框无边框无圆角，就纯文字 */
.home-hero__card {
  max-width: 640px;
  /* 不要任何视觉容器 */
}

.home-hero__title {
  font-size: 56px;
  font-weight: 800;
  color: #FFFFFF;
  line-height: 1.15;
  margin: 0 0 14px;
  letter-spacing: -1.5px;
  font-family: -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif;
  text-shadow: 0 2px 16px rgba(0, 0, 0, 0.5), 0 0 40px rgba(0, 0, 0, 0.2);
}
.home-hero__subtitle {
  font-size: 22px;
  font-weight: 500;
  color: #BFDBFE;
  margin: 0 0 22px;
  letter-spacing: 1px;
  text-shadow: 0 1px 8px rgba(0, 0, 0, 0.4);
}
.home-hero__desc {
  font-size: 16px;
  color: rgba(255, 255, 255, 0.85);
  line-height: 1.9;
  margin: 0 0 40px;
  text-shadow: 0 1px 6px rgba(0, 0, 0, 0.35);
}
.home-hero__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 44px;
}
.home-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 10px 22px;
  background: rgba(255, 255, 255, 0.12);
  border: 1px solid rgba(255, 255, 255, 0.25);
  border-radius: 100px;
  color: #FFFFFF;
  font-size: 14px;
  font-weight: 500;
  text-decoration: none;
  transition: all 0.2s;
}
.home-tag:hover {
  background: rgba(255, 255, 255, 0.22);
  border-color: rgba(255, 255, 255, 0.45);
  transform: translateY(-1px);
}
.home-hero__cta {
  display: flex;
  gap: 16px;
}
.home-btn {
  padding: 14px 36px;
  border-radius: 100px;
  font-size: 15px;
  font-weight: 600;
  border: none;
  cursor: pointer;
  transition: all 0.2s;
}
.home-btn--primary {
  background: linear-gradient(135deg, #3B82F6 0%, #1D4ED8 100%);
  color: #fff;
  box-shadow: 0 4px 24px rgba(59, 130, 246, 0.55);
}
.home-btn--primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 32px rgba(59, 130, 246, 0.65);
}

/* ========== 数据指标条 ========== */
.home-stats {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 0;
  margin-top: -24px;
  background: #fff;
  border: 1px solid #E2E8F0;
  border-radius: 14px;
  box-shadow: 0 4px 20px rgba(15, 23, 42, 0.06);
  overflow: hidden;
  position: relative;
  z-index: 10;
}
.home-stat {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 20px 24px;
  border-right: 1px solid #E2E8F0;
  transition: background 0.2s;
}
.home-stat:last-child { border-right: none; }
.home-stat:hover { background: #F8FAFC; }
.home-stat__icon {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  background: #EFF6FF;
  color: #2563EB;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.home-stat:nth-child(2) .home-stat__icon { background: #FEF3E2; color: #EA580C; }
.home-stat:nth-child(3) .home-stat__icon { background: #DCFCE7; color: #16A34A; }
.home-stat:nth-child(4) .home-stat__icon { background: #EDE9FE; color: #7C3AED; }
.home-stat:nth-child(5) .home-stat__icon { background: #FDF2F8; color: #DB2777; }
.home-stat:nth-child(6) .home-stat__icon { background: #F1F5F9; color: #475569; }
.home-stat__value {
  font-size: 18px;
  font-weight: 700;
  color: #0F172A;
  font-variant-numeric: tabular-nums;
  line-height: 1.2;
}
.home-stat__label {
  font-size: 12px;
  color: #64748B;
  margin-top: 2px;
}

/* ========== 最新动态 ========== */
.home-section {
  margin-top: 48px;
}
.home-section-title {
  font-size: 20px;
  font-weight: 700;
  color: #0F172A;
  margin: 0 0 20px;
}
.home-columns {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}
.home-panel {
  background: #fff;
  border: 1px solid #E2E8F0;
  border-radius: 14px;
  overflow: hidden;
}
.home-panel__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #E2E8F0;
}
.home-panel__title {
  font-size: 15px;
  font-weight: 600;
  color: #0F172A;
  display: flex;
  align-items: center;
  gap: 10px;
}
.home-panel__dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}
.home-panel__dot--blue { background: #2563EB; }
.home-panel__dot--orange { background: #EA580C; }
.home-list {
  list-style: none;
  padding: 0;
  margin: 0;
}
.home-list__item {
  display: flex;
  align-items: center;
  padding: 14px 20px;
  border-bottom: 1px solid #F1F5F9;
  transition: background 0.15s;
}
.home-list__item:last-child { border-bottom: none; }
.home-list__item:hover { background: #F8FAFC; }
.home-list__title {
  flex: 1;
  font-size: 14px;
  color: #1E293B;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  cursor: pointer;
}
.home-list__title:hover { color: #2563EB; }
.home-list__date {
  font-size: 12px;
  color: #94A3B8;
  margin-left: 16px;
  white-space: nowrap;
}
.home-list__empty {
  padding: 32px 20px;
  text-align: center;
  color: #94A3B8;
  font-size: 13px;
}

/* ========== 快捷入口 ========== */
.home-quick {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}
.home-quick__item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 28px 16px;
  background: #fff;
  border: 1px solid #E2E8F0;
  border-radius: 14px;
  text-decoration: none;
  transition: all 0.2s;
}
.home-quick__item:hover {
  border-color: rgba(37, 99, 235, 0.3);
  transform: translateY(-3px);
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
}
.home-quick__icon {
  width: 52px;
  height: 52px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}
.home-quick__icon--blue { background: linear-gradient(135deg, #3B82F6, #2563EB); }
.home-quick__icon--orange { background: linear-gradient(135deg, #F97316, #EA580C); }
.home-quick__icon--green { background: linear-gradient(135deg, #22C55E, #16A34A); }
.home-quick__icon--purple { background: linear-gradient(135deg, #8B5CF6, #7C3AED); }
.home-quick__name {
  font-size: 14px;
  font-weight: 600;
  color: #1E293B;
}

/* ========== 响应式 ========== */
@media (max-width: 1200px) {
  .home-hero__inner { padding: 80px 32px 72px; }
  .home-hero__card { padding: 40px 44px; }
  .home-stats { grid-template-columns: repeat(3, 1fr); }
  .home-stat { border-right: 1px solid #E2E8F0; border-bottom: 1px solid #E2E8F0; }
  .home-stat:nth-child(3n) { border-right: none; }
  .home-stat:nth-last-child(-n+3) { border-bottom: none; }
}
@media (max-width: 960px) {
  .home-hero__title { font-size: 40px; }
  .home-hero__inner { padding: 56px 24px 64px; }
  .home-hero__card { padding: 36px 32px; max-width: 100%; text-align: left; }
  .home-columns { grid-template-columns: 1fr; }
  .home-quick { grid-template-columns: repeat(2, 1fr); }
  .home-stats { grid-template-columns: repeat(2, 1fr); }
  .home-stat { border-right: none; }
  .home-hero { min-height: auto; }
}
@media (max-width: 640px) {
  .home-hero__title { font-size: 30px; letter-spacing: -1px; }
  .home-hero__subtitle { font-size: 16px; }
  .home-hero__desc { font-size: 14px; line-height: 1.7; }
  .home-hero__card { padding: 28px 24px; border-radius: 18px; }
  .home-quick { grid-template-columns: 1fr 1fr; gap: 12px; }
}
</style>
