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
        <div v-for="s in statItems" :key="s.label"
             class="home-stat"
             :class="{ 'home-stat--link': s.path }"
             @click="s.path && router.push(s.path)">
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

    <!-- 六大内容板块（2026-10-14 照抄医疗平台知识库首页版式：每板块大标题 + 3 张最新内容卡；
         卡片展示口径与各明细页一致，生态图谱为供应商轮播） -->
    <section class="edu-container home-sections">

      <!-- ① 解决方案 -->
      <div class="home-block">
        <div class="home-block__head">
          <h3 class="home-block__title">解决方案</h3>
          <router-link to="/solutions" class="home-block__more">查看全部 →</router-link>
        </div>
        <div class="home-grid">
          <article v-for="item in topSolutions" :key="item.id" class="hcard hcard--media">
            <div class="hcard__cover">
              <img
                v-if="!item._imgFail"
                :src="imgUrl(item.image)"
                :alt="item.name"
                loading="lazy"
                referrerpolicy="no-referrer"
                @error="item._imgFail = true"
              />
              <div v-else class="hcard__cover-fallback hcard__cover-fallback--sol"><span>🏫</span></div>
              <span class="hcard__badge">{{ item.category }}</span>
            </div>
            <div class="hcard__body">
              <h4 class="hcard__title" :title="item.name">{{ item.name }}</h4>
              <div class="hcard__vendor">{{ item.vendor }}</div>
              <p class="hcard__summary">{{ item.summary }}</p>
              <div class="hcard__foot">
                <span class="hcard__date"></span>
                <a class="hcard__link" :href="item.pageUrl" target="_blank" rel="noopener" title="前往厂商官网查看该方案详情">
                  官网方案 →
                </a>
              </div>
            </div>
          </article>
          <div v-if="topSolutions.length === 0" class="home-empty">正在载入解决方案…</div>
        </div>
      </div>

      <!-- ② 政策动态 -->
      <div class="home-block">
        <div class="home-block__head">
          <h3 class="home-block__title">政策动态</h3>
          <router-link to="/policy" class="home-block__more">查看全部 →</router-link>
        </div>
        <div class="home-grid">
          <article v-for="(item, idx) in topPolicies" :key="item.mediaId" class="hcard hcard--media">
            <div class="hcard__cover">
              <img
                v-if="!item._imgFail"
                :src="policyImg(idx)"
                :alt="item.title"
                loading="lazy"
                referrerpolicy="no-referrer"
                @error="item._imgFail = true"
              />
              <div v-else class="hcard__cover-fallback"><span>📚</span></div>
              <span v-if="item.source" class="hcard__badge hcard__badge--dark">{{ item.source }}</span>
            </div>
            <div class="hcard__body">
              <h4 class="hcard__title" :title="item.title">{{ item.title }}</h4>
              <div class="hcard__meta">
                <span v-if="item.doc_no" class="hcard__docno">{{ item.doc_no }}</span>
              </div>
              <div class="hcard__foot">
                <span class="hcard__date">{{ item.date }}</span>
                <a v-if="item.url" class="hcard__link" :href="item.url" target="_blank" rel="noopener" title="跳转到发布机构原文页面">
                  阅读原文 →
                </a>
              </div>
            </div>
          </article>
          <div v-if="topPolicies.length === 0" class="home-empty">正在载入政策数据…</div>
        </div>
      </div>

      <!-- ③ 重磅展会 -->
      <div class="home-block">
        <div class="home-block__head">
          <h3 class="home-block__title">重磅展会</h3>
          <router-link to="/exhibition" class="home-block__more">查看全部 →</router-link>
        </div>
        <div class="home-grid">
          <article v-for="item in topExhibitions" :key="item.id" class="hcard hcard--media">
            <div class="hcard__cover">
              <img
                v-if="!item._fbFail && item._img"
                :src="item._img"
                :alt="item.title"
                loading="lazy"
                referrerpolicy="no-referrer"
                @error="onCardImgError(item)"
              />
              <div v-else class="hcard__cover-fallback"><span>📣</span></div>
              <span v-if="item.source" class="hcard__badge hcard__badge--dark">{{ item.source }}</span>
            </div>
            <div class="hcard__body">
              <h4 class="hcard__title" :title="item.title">{{ item.title }}</h4>
              <p class="hcard__summary">{{ item.summary }}</p>
              <div class="hcard__foot">
                <span class="hcard__date">{{ item.date || '—' }}</span>
                <a class="hcard__link" :href="item.url" target="_blank" rel="noopener" title="跳转到原网站查看全文">
                  跳转原文 →
                </a>
              </div>
            </div>
          </article>
          <div v-if="topExhibitions.length === 0" class="home-empty">正在载入展会资讯…</div>
        </div>
      </div>

      <!-- ④ 智库观察 -->
      <div class="home-block">
        <div class="home-block__head">
          <h3 class="home-block__title">智库观察</h3>
          <router-link to="/thinktank" class="home-block__more">查看全部 →</router-link>
        </div>
        <div class="home-grid">
          <article v-for="item in topThinktank" :key="item.id" class="hcard hcard--media">
            <div class="hcard__cover">
              <img
                v-if="!item._fbFail && item._img"
                :src="item._img"
                :alt="item.title"
                loading="lazy"
                referrerpolicy="no-referrer"
                @error="onCardImgError(item)"
              />
              <div v-else class="hcard__cover-fallback"><span>🔍</span></div>
              <span v-if="item.source" class="hcard__badge hcard__badge--dark">{{ item.source }}</span>
            </div>
            <div class="hcard__body">
              <h4 class="hcard__title" :title="item.title">{{ item.title }}</h4>
              <p class="hcard__summary">{{ item.summary }}</p>
              <div class="hcard__foot">
                <span class="hcard__date">{{ item.date || '—' }}</span>
                <a class="hcard__link" :href="item.url" target="_blank" rel="noopener" title="跳转到原网站查看全文">
                  跳转原文 →
                </a>
              </div>
            </div>
          </article>
          <div v-if="topThinktank.length === 0" class="home-empty">正在载入智库文章…</div>
        </div>
      </div>

      <!-- ⑤ 招投标信息（口径同招投标页：只展示中标/成交结果公告） -->
      <div class="home-block">
        <div class="home-block__head">
          <h3 class="home-block__title">招投标信息</h3>
          <router-link to="/bidding" class="home-block__more">查看全部 →</router-link>
        </div>
        <div class="home-grid">
          <article v-for="item in topBids" :key="item.id" class="hcard">
            <div class="hcard__body">
              <h4 class="hcard__title" :title="item.title">{{ item.projectName || item.title }}</h4>
              <div class="hcard__meta">
                <span v-if="item.projectCode" class="hcard__docno">{{ item.projectCode }}</span>
                <span v-if="item.winningBidder" class="hcard__source">中标方：{{ item.winningBidder }}</span>
              </div>
              <p class="hcard__summary">{{ item.summary }}</p>
              <div class="hcard__foot">
                <span class="hcard__date">{{ (item.publishDate || (item.createdAt || '').slice(0, 10)) || '—' }}</span>
                <a v-if="item.sourceUrl" class="hcard__link" :href="item.sourceUrl" target="_blank" rel="noopener" title="跳转到广东省政府采购网的对应公告页面">
                  中标公告 →
                </a>
              </div>
            </div>
          </article>
          <div v-if="topBids.length === 0" class="home-empty">正在载入中标公告…</div>
        </div>
      </div>

      <!-- ⑥ 生态图谱（供应商轮播，照抄医疗首页：每页 3 家 / 5 秒自动播放 / 悬停暂停） -->
      <div class="home-block">
        <div class="home-block__head">
          <h3 class="home-block__title">生态图谱</h3>
          <router-link to="/ecosystem" class="home-block__more">查看全部 →</router-link>
        </div>
        <div class="eco-carousel" ref="ecoBox">
          <div class="eco-viewport" ref="ecoViewport">
            <div class="eco-track" :style="{ transform: 'translateX(-' + ecoPage * 100 + '%)' }">
              <div v-for="s in ecosystemItems" :key="s.id" class="eco-cell">
                <article class="hcard">
                  <div class="hcard__body">
                    <span class="hcard__cat">{{ s.category }}</span>
                    <h4 class="hcard__title" :title="s.name">{{ s.name }}</h4>
                    <p class="hcard__summary">{{ s.summary }}</p>
                    <div class="hcard__foot">
                      <span class="hcard__date"></span>
                      <a v-if="s.website" class="hcard__link" :href="s.website" target="_blank" rel="noopener" title="前往供应商官网">
                        官网 →
                      </a>
                    </div>
                  </div>
                </article>
              </div>
            </div>
          </div>
          <div class="eco-ctrl">
            <button class="eco-btn" type="button" aria-label="上一页" @click="ecoGo(-1)">
              <el-icon><ArrowLeft /></el-icon>
            </button>
            <span class="eco-count">{{ ecoPages() ? ecoPage + 1 : 0 }} / {{ ecoPages() }}</span>
            <button class="eco-btn" type="button" aria-label="下一页" @click="ecoGo(1)">
              <el-icon><ArrowRight /></el-icon>
            </button>
          </div>
        </div>
      </div>

    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import {
  Document, Trophy, Files, Lightning, Share,
  ArrowLeft, ArrowRight, Flag, View,
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
const biddingData = ref({ items: [] })
const solutionItems = ref([])
const exhibitionItems = ref([])
const thinktankItems = ref([])
const ecosystemItems = ref([])

const metrics = computed(() => ({
  totalPolicies: policyData.value.categories.reduce((sum, c) => sum + (c.items?.length || 0), 0),
}))

const statItems = computed(() => [
  { label: '政策条目', value: metrics.value.totalPolicies + ' 项', icon: Document, path: '/policy' },
  { label: '招投标', value: topBidsAll.value.length + ' 条', icon: Trophy, path: '/bidding' },
  { label: '解决方案', value: solutionItems.value.length + ' 项', icon: Lightning, path: '/solutions' },
  { label: '生态图谱', value: ecosystemItems.value.length + ' 家', icon: Share, path: '/ecosystem' },
  { label: '重磅展会', value: exhibitionItems.value.length + ' 条', icon: Flag, path: '/exhibition' },
  { label: '智库观察', value: thinktankItems.value.length + ' 条', icon: View, path: '/thinktank' },
])

// 政策卡封面：本地主题图池轮换（Unsplash 免费图库自托管，2026-10-14 老大要求政策卡配图）
const POL_IMG_POOL = [
  'images/policy/pol-1.jpg',
  'images/policy/pol-2.jpg',
  'images/policy/pol-3.jpg',
]
const policyImg = (idx) => imgUrl(POL_IMG_POOL[idx % POL_IMG_POOL.length])

// ── 招投标：只保留中标（成交）结果，口径同招投标页 isAward ──
const isAward = (b) => {
  const hay = (b.group || '') + ' ' + (b.title || '')
  return hay.includes('中标') || hay.includes('结果') || hay.includes('成交')
}
const topBidsAll = computed(() =>
  [...(biddingData.value.items || [])].filter(isAward)
    .sort((a, b) => (b.publishDate || b.createdAt || '').localeCompare(a.publishDate || a.createdAt || ''))
)
const topBids = computed(() => topBidsAll.value.slice(0, 3))

const topSolutions = computed(() => solutionItems.value.slice(0, 3))

const topPolicies = computed(() => {
  const list = []
  policyData.value.categories.forEach(cat => (cat.items || []).forEach(item => list.push(item)))
  return list.sort((a, b) => (b.date || '').localeCompare(a.date || '')).slice(0, 3)
})

const topExhibitions = computed(() =>
  [...exhibitionItems.value]
    .sort((a, b) => (b.date || '').localeCompare(a.date || ''))
    .slice(0, 3)
)
const topThinktank = computed(() =>
  [...thinktankItems.value]
    .sort((a, b) => (b.date || '').localeCompare(a.date || ''))
    .slice(0, 3)
)

// ── 展会/智库卡片图片：与明细页同口径 —— 条目原图，无图降级本地主题图，再失败降级渐变 emoji ──
const imgUrl = (p) => import.meta.env.BASE_URL + p
const EXH_FB = [
  'fb-classroom.jpg', 'fb-smartclass.png', 'fb-expo.png', 'fb-robot.png',
  'fb-campus.png', 'fb-coding.png', 'fb-library.png', 'fb-digital.jpg',
]
const TT_FB = [
  'tt-conference.png', 'tt-datacenter.png', 'tt-screen.png',
  'tt-ai.png', 'tt-lecture.png', 'tt-hall.png', 'tt-lab.png', 'tt-seminar.png',
]
function assignFallback(list, pool) {
  let n = 0
  list.forEach(it => {
    if (it.image) {
      it._img = it.image
    } else {
      it._fbUrl = imgUrl('images/exhibition/' + pool[n % pool.length])
      it._img = it._fbUrl
      n++
    }
  })
}
// 原图挂了 → 降到该条目的本地占位图；占位图也挂了 → 渐变 emoji（口径同明细页）
const onCardImgError = (item) => {
  if (item.image && item._img === item.image) {
    item.image = ''
    item._img = item._fbUrl || ''
    if (!item._img) item._fbFail = true
  } else {
    item._fbFail = true
  }
}

// ── 生态图谱轮播（照抄医疗首页：桌面每页 3 家、窄屏 1 家；按钮翻页 + 5 秒自动播放，悬停暂停） ──
const ecoViewport = ref(null)
const ecoPage = ref(0)
let ecoTimer = null

const ecoPerView = () => (ecoViewport.value && ecoViewport.value.clientWidth < 640 ? 1 : 3)
const ecoPages = () => Math.max(1, Math.ceil(ecosystemItems.value.length / ecoPerView()))
const ecoGo = (d) => {
  ecoPage.value = (ecoPage.value + d + ecoPages()) % ecoPages()
}
const ecoPlay = () => { ecoStop(); ecoTimer = setInterval(() => ecoGo(1), 5000) }
const ecoStop = () => { if (ecoTimer) { clearInterval(ecoTimer); ecoTimer = null } }

onMounted(async () => {
  const ts = Date.now()
  const B = import.meta.env.BASE_URL
  const get = (f) => fetch(B + 'data/' + f + '?v=' + ts).then(r => r.json()).catch(() => null)
  const [pRes, bRes, sRes, eRes, tRes, ecoRes] = await Promise.all([
    get('policy.json'), get('bidding.json'), get('solutions.json'),
    get('exhibition.json'), get('thinktank.json'), get('ecosystem.json'),
  ])
  if (pRes) policyData.value = pRes
  if (bRes) biddingData.value = bRes
  solutionItems.value = (sRes && sRes.items) || []
  exhibitionItems.value = (eRes && eRes.items) || []
  thinktankItems.value = (tRes && tRes.items) || []
  ecosystemItems.value = (ecoRes && ecoRes.items) || []

  // 展会/智库卡片的无图条目分配本地占位图（口径同明细页）
  assignFallback(topExhibitions.value, EXH_FB)
  assignFallback(topThinktank.value, TT_FB)

  const v = ecoViewport.value
  if (v) {
    v.parentElement.addEventListener('mouseenter', ecoStop)
    v.parentElement.addEventListener('mouseleave', ecoPlay)
    window.addEventListener('resize', onEcoResize)
  }
  ecoPlay()
})
const onEcoResize = () => { ecoPage.value = 0 }
onBeforeUnmount(() => {
  ecoStop()
  window.removeEventListener('resize', onEcoResize)
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
.home-stat--link { cursor: pointer; }
.home-stat--link:hover { background: #EFF6FF; }
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

/* ========== 六大内容板块 ========== */
.home-sections {
  margin-top: 56px;
  display: flex;
  flex-direction: column;
  gap: 56px;
}
.home-block__head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.home-block__title {
  font-size: 20px;
  font-weight: 700;
  color: #0F172A;
  margin: 0;
  padding-left: 12px;
  border-left: 4px solid var(--edu-primary, #1E5AA8);
  line-height: 1.3;
}
.home-block__more {
  font-size: 13px;
  color: var(--edu-primary, #1E5AA8);
  font-weight: 500;
  text-decoration: none;
}
.home-block__more:hover { color: var(--edu-primary-hover, #174A8E); }
.home-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}
.home-empty {
  grid-column: 1 / -1;
  padding: 40px 0;
  text-align: center;
  color: #94A3B8;
  font-size: 13px;
}

/* 通用内容卡（版式口径对齐各明细页卡片） */
.hcard {
  display: flex;
  flex-direction: column;
  background: #fff;
  border: 1px solid var(--edu-border-light, #EDF2F7);
  border-radius: var(--edu-radius-md, 8px);
  overflow: hidden;
  transition: box-shadow 0.2s, transform 0.2s;
}
.hcard:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
  transform: translateY(-2px);
}
.hcard__cover {
  position: relative;
  aspect-ratio: 16 / 9;
  background: var(--edu-bg-hover, #F0F4F9);
  overflow: hidden;
  flex-shrink: 0;
}
.hcard__cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
.hcard__cover-fallback {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 40px;
  background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%);
}
.hcard__cover-fallback--sol {
  background: linear-gradient(135deg, #1E5AA8 0%, #3F7FD4 100%);
}
.hcard__badge {
  position: absolute;
  left: 8px;
  bottom: 8px;
  padding: 2px 10px;
  border-radius: var(--edu-radius-sm, 4px);
  background: rgba(30, 90, 168, 0.88);
  color: #fff;
  font-size: 12px;
  letter-spacing: 1px;
}
.hcard__badge--dark {
  background: rgba(15, 23, 42, 0.65);
  backdrop-filter: blur(4px);
  letter-spacing: 0;
}
.hcard__body {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 14px 16px;
  flex: 1;
  min-width: 0;
}
.hcard__title {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--edu-text-primary, #2B3A4A);
  line-height: 1.5;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}
.hcard__vendor {
  font-size: 12px;
  color: var(--edu-primary, #1E5AA8);
  font-weight: 600;
  margin-top: -4px;
}
.hcard__cat {
  align-self: flex-start;
  padding: 1px 8px;
  border-radius: var(--edu-radius-sm, 4px);
  background: var(--edu-primary-light, #EAF1F8);
  color: var(--edu-primary, #1E5AA8);
  font-size: 12px;
}
.hcard__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 12px;
  font-size: 12px;
  color: var(--edu-text-secondary, #6B7C8E);
  margin-top: -2px;
}
.hcard__source { font-weight: 500; }
.hcard__docno {
  color: var(--edu-text-placeholder, #9AA7B4);
}
.hcard__summary {
  margin: 0;
  font-size: 12px;
  color: var(--edu-text-secondary, #6B7C8E);
  line-height: 1.6;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
}
.hcard__foot {
  margin-top: auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding-top: 6px;
  border-top: 1px solid var(--edu-border-light, #EDF2F7);
}
.hcard__date {
  font-size: 12px;
  color: var(--edu-text-placeholder, #9AA7B4);
  font-variant-numeric: tabular-nums;
}
.hcard__link {
  font-size: 12px;
  color: var(--edu-primary, #1E5AA8);
  font-weight: 500;
  text-decoration: none;
  white-space: nowrap;
}
.hcard__link:hover {
  color: var(--edu-primary-hover, #174A8E);
  text-decoration: underline;
}

/* ========== 生态图谱轮播（照抄医疗首页交互） ========== */
.eco-viewport {
  overflow: hidden;
}
.eco-track {
  display: flex;
  transition: transform 0.5s ease;
}
.eco-cell {
  flex: 0 0 33.3333%;
  box-sizing: border-box;
  padding: 0 8px;
  display: flex;
}
.eco-cell .hcard {
  flex: 1;
}
.eco-ctrl {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 14px;
  margin-top: 16px;
}
.eco-btn {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: 1px solid var(--edu-border, #E2E8F0);
  background: #fff;
  color: var(--edu-primary, #1E5AA8);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
}
.eco-btn:hover {
  background: var(--edu-primary-light, #EAF1F8);
  border-color: var(--edu-primary, #1E5AA8);
}
.eco-count {
  font-size: 13px;
  color: var(--edu-text-secondary, #6B7C8E);
  font-variant-numeric: tabular-nums;
}

/* ========== 响应式 ========== */
@media (max-width: 1200px) {
  .home-hero__inner { padding: 80px 32px 72px; }
  .home-stats { grid-template-columns: repeat(3, 1fr); }
  .home-stat { border-right: 1px solid #E2E8F0; border-bottom: 1px solid #E2E8F0; }
  .home-stat:nth-child(3n) { border-right: none; }
  .home-stat:nth-last-child(-n+3) { border-bottom: none; }
  .home-grid { grid-template-columns: repeat(2, 1fr); }
  .eco-cell { flex-basis: 50%; }
}
@media (max-width: 960px) {
  .home-hero__title { font-size: 40px; }
  .home-hero__inner { padding: 56px 24px 64px; }
  .home-hero__card { max-width: 100%; text-align: left; }
  .home-stats { grid-template-columns: repeat(2, 1fr); }
  .home-stat { border-right: none; }
  .home-hero { min-height: auto; }
  .home-sections { gap: 44px; margin-top: 44px; }
}
@media (max-width: 640px) {
  .home-hero__title { font-size: 30px; letter-spacing: -1px; }
  .home-hero__subtitle { font-size: 16px; }
  .home-hero__desc { font-size: 14px; line-height: 1.7; }
  .home-grid { grid-template-columns: 1fr; }
  .eco-cell { flex-basis: 100%; padding: 0 4px; }
}
</style>
