<template>
  <div class="edu-layout">
    <!-- 顶部导航栏 -->
    <header class="edu-header">
      <div class="edu-header__inner edu-container">
        <!-- Logo -->
        <div class="edu-logo" @click="go('/home')">
          <div class="edu-logo__mark">
            <el-icon :size="20"><Reading /></el-icon>
          </div>
          <span class="edu-logo__text">教育智服</span>
          <span class="edu-logo__sub">Knowledge Platform</span>
        </div>

        <!-- 桌面端导航 -->
        <nav class="edu-nav edu-nav--desktop">
          <router-link
            v-for="item in menuItems"
            :key="item.path"
            :to="item.path"
            class="edu-nav__item"
            :class="{ 'is-active': isActive(item.path) }"
          >
            <span>{{ item.name }}</span>
          </router-link>
        </nav>

        <!-- 右侧操作区 -->
        <div class="edu-header__actions edu-header__actions--desktop">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索政策、招投标..."
            :prefix-icon="Search"
            class="edu-search"
            clearable
            size="default"
          />
        </div>

        <!-- 移动端汉堡按钮 -->
        <el-button
          class="edu-header__burger"
          :icon="menuOpen ? Close : Menu"
          circle
          @click="menuOpen = !menuOpen"
        />
      </div>

      <!-- 移动端下拉菜单 -->
      <transition name="slide-down">
        <div v-if="menuOpen" class="edu-mobile-menu edu-container">
          <nav class="edu-mobile-menu__nav">
            <router-link
              v-for="item in menuItems"
              :key="item.path"
              :to="item.path"
              class="edu-mobile-menu__item"
              :class="{ 'is-active': isActive(item.path) }"
              @click="menuOpen = false"
            >
              <el-icon><component :is="item.icon" /></el-icon>
              <span>{{ item.name }}</span>
            </router-link>
          </nav>
          <div class="edu-mobile-menu__search">
            <el-input
              v-model="searchKeyword"
              placeholder="搜索政策、招投标..."
              :prefix-icon="Search"
              clearable
            />
          </div>
        </div>
      </transition>
    </header>

    <!-- 主内容区 -->
    <main class="edu-main">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>

    <!-- 页脚 -->
    <footer class="edu-footer">
      <div class="edu-footer__inner edu-container">
        <div class="edu-footer__col edu-footer__col--brand">
          <div class="edu-footer__logo">
            <div class="edu-logo__mark edu-logo__mark--white">
              <el-icon :size="18"><Reading /></el-icon>
            </div>
            <span>教育智服</span>
          </div>
          <p class="edu-footer__desc">
            汇聚广东省教育政策、招投标信息、行业解决方案与生态图谱，助力教育数字化转型升级。
          </p>
        </div>
        <div class="edu-footer__col">
          <div class="edu-footer__title">数据来源</div>
          <ul class="edu-footer__links">
            <li><a href="https://edu.gd.gov.cn/gkmlpt/policy/" target="_blank">广东省教育厅</a></li>
            <li><a href="http://www.moe.gov.cn/jyb_xxgk/zywj_btlj/index.html" target="_blank">中华人民共和国教育部</a></li>
            <li><a href="https://www.gdgpo.gov.cn/" target="_blank">广东省政府采购网</a></li>
          </ul>
        </div>
        <div class="edu-footer__col">
          <div class="edu-footer__title">导航</div>
          <ul class="edu-footer__links">
            <li><router-link to="/policy">政策动态</router-link></li>
            <li><router-link to="/bidding">招投标信息</router-link></li>
            <li><router-link to="/solutions">解决方案</router-link></li>
            <li><router-link to="/ecosystem">生态图谱</router-link></li>
          </ul>
        </div>
      </div>
      <div class="edu-footer__bottom edu-container">
        <span>© {{ currentYear }} 教育智服 · 教育知识服务平台</span>
        <span class="edu-footer__dot-sep">·</span>
        <span class="edu-footer__data">
          <span class="edu-footer__dot" :class="{ 'is-fresh': isFresh }"></span>
          IMA 同步：{{ dataStatus.updated }}
          <span class="edu-footer__stats">采购 {{ dataStatus.procurementTotal }} / 中标 {{ dataStatus.winningTotal }} / 匹配 {{ dataStatus.matchedCount }}</span>
        </span>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { useRoute, useRouter } from 'vue-router'
import { Reading, Search, Menu, Close, HomeFilled, Document, Files, Lightning, Share } from '@element-plus/icons-vue'
import { computed, ref, watch, onMounted } from 'vue'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const searchKeyword = ref('')
const menuOpen = ref(false)
const currentYear = new Date().getFullYear()

watch(() => route.path, () => { menuOpen.value = false })

const menuItems = [
  { path: '/home', name: '首页', icon: HomeFilled },
  { path: '/bidding', name: '招投标', icon: Files },
  { path: '/policy', name: '政策动态', icon: Document },
  { path: '/solutions', name: '解决方案', icon: Lightning },
  { path: '/ecosystem', name: '生态图谱', icon: Share }
]

const isActive = (path) => {
  if (path === '/home') return route.path === '/home' || route.path === '/'
  return route.path.startsWith(path)
}

const go = (path) => { menuOpen.value = false; router.push(path) }

// ========== 数据更新状态 ==========
const dataStatus = ref({ loading: true, error: false, updated: '', procurementTotal: 0, winningTotal: 0, matchedCount: 0 })
const isFresh = computed(() => {
  if (!dataStatus.value.updated) return false
  const d = new Date(dataStatus.value.updated)
  return (Date.now() - d.getTime()) / (1000 * 60 * 60 * 24) <= 2
})

async function fetchDataStatus() {
  try {
    const res = await fetch(import.meta.env.BASE_URL + `data/bidding.json?v=${Date.now()}`)
    if (!res.ok) throw new Error('fetch failed')
    const data = await res.json()
    dataStatus.value = {
      loading: false, error: false,
      updated: data.updated || '-',
      procurementTotal: data.procurement?.length || 0,
      winningTotal: data.winning?.length || 0,
      matchedCount: data.matchStats?.matchedCount || 0,
    }
  } catch (e) {
    dataStatus.value = { loading: false, error: true, updated: '', procurementTotal: 0, winningTotal: 0, matchedCount: 0 }
  }
}

onMounted(fetchDataStatus)
</script>

<style scoped>
.edu-layout {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

/* ========== Header ========== */
.edu-header {
  position: sticky;
  top: 0;
  z-index: 100;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: saturate(180%) blur(12px);
  -webkit-backdrop-filter: saturate(180%) blur(12px);
  border-bottom: 1px solid #E2E8F0;
}
.edu-header__inner {
  display: flex;
  align-items: center;
  height: 60px;
  gap: 32px;
}
.edu-logo {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  flex-shrink: 0;
}
.edu-logo__mark {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.25);
}
.edu-logo__mark--white {
  background: linear-gradient(135deg, #3B82F6 0%, #1D4ED8 100%);
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3);
}
.edu-logo__text {
  font-size: 17px;
  font-weight: 700;
  color: #0F172A;
  letter-spacing: -0.5px;
}
.edu-logo__sub {
  font-size: 10px;
  font-weight: 400;
  color: #94A3B8;
  margin-left: 2px;
  letter-spacing: 0.5px;
  text-transform: uppercase;
}

/* 桌面导航 */
.edu-nav--desktop {
  display: flex;
  gap: 4px;
  flex: 1;
  justify-content: flex-start;
  margin-left: 12px;
}
.edu-nav__item {
  display: flex;
  align-items: center;
  padding: 6px 18px;
  border-radius: 8px;
  color: #475569;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.15s;
  text-decoration: none;
  white-space: nowrap;
}
.edu-nav__item:hover {
  background: #F1F5F9;
  color: #0F172A;
}
.edu-nav__item.is-active {
  background: #EFF6FF;
  color: #2563EB;
  font-weight: 600;
}

/* 搜索 */
.edu-header__actions--desktop {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-shrink: 0;
}
.edu-search { width: 240px; }

/* 汉堡 */
.edu-header__burger { display: none; flex-shrink: 0; }

/* 移动端菜单 */
.edu-mobile-menu {
  padding: 12px 20px 20px;
  border-top: 1px solid #E2E8F0;
  background: #fff;
}
.edu-mobile-menu__nav {
  display: flex;
  flex-direction: column;
  gap: 2px;
  margin-bottom: 12px;
}
.edu-mobile-menu__item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border-radius: 8px;
  color: #475569;
  font-size: 15px;
  font-weight: 500;
  text-decoration: none;
}
.edu-mobile-menu__item.is-active { background: #EFF6FF; color: #2563EB; }

/* 动画 */
.slide-down-enter-active,
.slide-down-leave-active { transition: all 0.2s ease; }
.slide-down-enter-from,
.slide-down-leave-to { opacity: 0; transform: translateY(-8px); }

.edu-main { flex: 1; }

/* ========== Footer ========== */
.edu-footer {
  background: #0F172A;
  color: #94A3B8;
  margin-top: 0;
}
.edu-footer__inner {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr;
  gap: 48px;
  padding: 56px 24px 32px;
}
.edu-footer__logo {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 17px;
  font-weight: 700;
  color: #fff;
  margin-bottom: 16px;
}
.edu-footer__desc {
  font-size: 13px;
  line-height: 1.8;
  color: #64748B;
  max-width: 380px;
  margin: 0;
}
.edu-footer__title {
  font-size: 13px;
  font-weight: 600;
  color: #E2E8F0;
  margin-bottom: 16px;
  letter-spacing: 0.5px;
}
.edu-footer__links {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.edu-footer__links a {
  color: #64748B;
  font-size: 13px;
  text-decoration: none;
  transition: color 0.15s;
}
.edu-footer__links a:hover { color: #60A5FA; }

.edu-footer__bottom {
  border-top: 1px solid rgba(148, 163, 184, 0.15);
  padding: 20px 24px;
  font-size: 12px;
  text-align: center;
  color: #475569;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.edu-footer__dot {
  width: 7px; height: 7px; border-radius: 50%;
  background: #334155;
}
.edu-footer__dot.is-fresh {
  background: #22C55E;
  box-shadow: 0 0 6px rgba(34, 197, 94, 0.5);
}
.edu-footer__stats {
  margin-left: 8px;
  padding-left: 8px;
  border-left: 1px solid rgba(148, 163, 184, 0.2);
  font-size: 11px;
  color: #475569;
}

/* Page transition */
.fade-enter-active,
.fade-leave-active { transition: opacity 0.2s ease; }
.fade-enter-from,
.fade-leave-to { opacity: 0; }

/* ========== 响应式 ========== */
@media (max-width: 1200px) {
  .edu-header__inner { gap: 20px; }
  .edu-search { width: 200px; }
}
@media (max-width: 960px) {
  .edu-header__inner { height: 56px; gap: 12px; }
  .edu-logo__text { font-size: 15px; }
  .edu-logo__sub { display: none; }
  .edu-footer__inner { grid-template-columns: 1fr; gap: 28px; padding: 40px 20px 24px; }
}
@media (max-width: 768px) {
  .edu-nav--desktop { display: none; }
  .edu-header__actions--desktop { display: none; }
  .edu-header__burger { display: inline-flex; }
}
</style>
