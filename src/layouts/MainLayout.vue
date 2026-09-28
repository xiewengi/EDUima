<template>
  <div class="edu-layout">
    <!-- 顶部导航栏 -->
    <header class="edu-header">
      <div class="edu-header__inner edu-container">
        <!-- Logo -->
        <div class="edu-logo" @click="go('/home')">
          <el-icon class="edu-logo__icon"><Reading /></el-icon>
          <span class="edu-logo__text">教育行业知识服务平台</span>
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
            <el-icon><component :is="item.icon" /></el-icon>
            <span>{{ item.name }}</span>
          </router-link>
        </nav>

        <!-- 右侧操作区 -->
        <div class="edu-header__actions edu-header__actions--desktop">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索..."
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
        <div class="edu-footer__col">
          <div class="edu-footer__title">关于平台</div>
          <p class="edu-footer__desc">教育行业知识服务平台，汇聚广东省教育政策、招投标信息、行业解决方案与生态图谱。</p>
        </div>
        <div class="edu-footer__col">
          <div class="edu-footer__title">数据来源</div>
          <ul class="edu-footer__links">
            <li><a href="https://edu.gd.gov.cn/gkmlpt/policy/" target="_blank">广东省教育厅</a></li>
            <li><a href="http://www.moe.gov.cn/jyb_xxgk/zywj_btlj/index.html" target="_blank">中华人民共和国教育部</a></li>
          </ul>
        </div>
        <div class="edu-footer__col">
          <div class="edu-footer__title">联系方式</div>
          <ul class="edu-footer__links">
            <li><el-icon><Message /></el-icon> ima@example.com</li>
          </ul>
        </div>
      </div>
      <div class="edu-footer__bottom edu-container">
        <span>© {{ currentYear }} 教育行业知识服务平台</span>
        <span class="edu-footer__divider">·</span>
        <span v-if="dataStatus.loading">数据加载中...</span>
        <span v-else-if="dataStatus.error" class="edu-footer__warn">数据异常</span>
        <span v-else class="edu-footer__data">
          <span class="edu-footer__dot" :class="{ 'is-fresh': isFresh }"></span>
          IMA 同步：{{ dataStatus.updated }}
          <span class="edu-footer__stats">采购{{ dataStatus.procurementTotal }} / 中标{{ dataStatus.winningTotal }} / 匹配{{ dataStatus.matchedCount }}</span>
        </span>
        <span class="edu-footer__sync-hint" @click="manualSync">🔄 手动同步</span>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { useRoute, useRouter } from 'vue-router'
import { Reading, Search, Message, HomeFilled, Document, Files, Lightning, Share, Menu, Close } from '@element-plus/icons-vue'
import { computed, ref, watch } from 'vue'

const route = useRoute()
const router = useRouter()
const searchKeyword = ref('')
const menuOpen = ref(false)
const currentYear = new Date().getFullYear()

// 路由变化时关闭移动端菜单
watch(() => route.path, () => { menuOpen.value = false })

const menuItems = [
  { path: '/home', name: '首页', icon: HomeFilled },
  { path: '/bidding', name: '招投标信息', icon: Files },
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
  const now = new Date()
  const diff = (now - d) / (1000 * 60 * 60 * 24) // 天数差
  return diff <= 2
})

async function fetchDataStatus() {
  try {
    const res = await fetch(`/data/bidding.json?v=${Date.now()}`)
    if (!res.ok) throw new Error('fetch failed')
    const data = await res.json()
    dataStatus.value = {
      loading: false,
      error: false,
      updated: data.updated || '-',
      procurementTotal: data.procurement?.length || 0,
      winningTotal: data.winning?.length || 0,
      matchedCount: data.matchStats?.matchedCount || 0,
    }
  } catch (e) {
    dataStatus.value = { loading: false, error: true, updated: '', procurementTotal: 0, winningTotal: 0, matchedCount: 0 }
  }
}

function manualSync() {
  // 清除浏览器缓存 + 重新拉
  dataStatus.value.loading = true
  fetchDataStatus()
  ElMessage.success('已刷新最新数据')
}

import { onMounted } from 'vue'
import { ElMessage } from 'element-plus'
onMounted(fetchDataStatus)
</script>

<style scoped>
.edu-layout {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

/* Header */
.edu-header {
  position: sticky;
  top: 0;
  z-index: 100;
  background: #fff;
  border-bottom: 1px solid var(--edu-border-light);
  box-shadow: var(--edu-shadow-sm);
}
.edu-header__inner {
  display: flex;
  align-items: center;
  height: 64px;
  gap: var(--edu-space-5);
}
.edu-logo {
  display: flex;
  align-items: center;
  gap: var(--edu-space-2);
  cursor: pointer;
  flex-shrink: 0;
}
.edu-logo__icon {
  font-size: 24px;
  color: var(--edu-primary);
}
.edu-logo__text {
  font-size: var(--edu-font-lg);
  font-weight: 700;
  color: var(--edu-text-primary);
  white-space: nowrap;
}

/* 桌面导航 */
.edu-nav--desktop {
  display: flex;
  gap: var(--edu-space-1);
  flex: 1;
  justify-content: center;
}
.edu-nav__item {
  display: flex;
  align-items: center;
  gap: var(--edu-space-1);
  padding: var(--edu-space-2) var(--edu-space-3);
  border-radius: var(--edu-radius-md);
  color: var(--edu-text-regular);
  font-size: var(--edu-font-base);
  font-weight: 500;
  transition: all 0.2s;
  white-space: nowrap;
}
.edu-nav__item:hover {
  background: var(--edu-primary-light);
  color: var(--edu-primary);
}
.edu-nav__item.is-active {
  background: var(--edu-primary);
  color: #fff;
}
.edu-nav__item.is-active:hover {
  background: var(--edu-primary-hover);
  color: #fff;
}

/* 右侧操作区 */
.edu-header__actions--desktop {
  display: flex;
  align-items: center;
  gap: var(--edu-space-3);
  flex-shrink: 0;
}
.edu-search { width: 220px; }

/* 汉堡按钮（默认隐藏） */
.edu-header__burger {
  display: none;
  flex-shrink: 0;
}

/* 移动端菜单 */
.edu-mobile-menu {
  padding: var(--edu-space-3);
  border-top: 1px solid var(--edu-border-light);
  background: #fff;
}
.edu-mobile-menu__nav {
  display: flex;
  flex-direction: column;
  gap: var(--edu-space-1);
  margin-bottom: var(--edu-space-2);
}
.edu-mobile-menu__item {
  display: flex;
  align-items: center;
  gap: var(--edu-space-3);
  padding: var(--edu-space-3) var(--edu-space-4);
  border-radius: var(--edu-radius-md);
  color: var(--edu-text-regular);
  font-size: var(--edu-font-base);
  font-weight: 500;
  transition: all 0.2s;
}
.edu-mobile-menu__item:hover {
  background: var(--edu-primary-light);
  color: var(--edu-primary);
}
.edu-mobile-menu__item.is-active {
  background: var(--edu-primary);
  color: #fff;
}
.edu-mobile-menu__search { padding: var(--edu-space-2) 0; }

/* 移动端下拉动画 */
.slide-down-enter-active,
.slide-down-leave-active { transition: all 0.25s ease; }
.slide-down-enter-from,
.slide-down-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

/* Main */
.edu-main { flex: 1; }

/* Footer */
.edu-footer {
  background: var(--edu-text-primary);
  color: #CBD5E1;
  margin-top: var(--edu-space-8);
}
.edu-footer__inner {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr;
  gap: var(--edu-space-6);
  padding: var(--edu-space-6) var(--edu-space-5);
}
.edu-footer__title {
  font-size: var(--edu-font-md);
  font-weight: 600;
  color: #fff;
  margin-bottom: var(--edu-space-3);
}
.edu-footer__desc {
  font-size: var(--edu-font-sm);
  line-height: 1.8;
  color: #94A3B8;
}
.edu-footer__links {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: var(--edu-space-2);
  font-size: var(--edu-font-sm);
}
.edu-footer__links a,
.edu-footer__links li {
  color: #94A3B8;
  display: flex;
  align-items: center;
  gap: 6px;
}
.edu-footer__links a:hover { color: #fff; }
.edu-footer__bottom {
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  padding: var(--edu-space-4) var(--edu-space-5);
  font-size: var(--edu-font-xs);
  text-align: center;
  color: #64748B;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}
.edu-footer__divider { color: #334155; }
.edu-footer__data {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: #94A3B8;
}
.edu-footer__dot {
  width: 8px; height: 8px; border-radius: 50%;
  background: #64748B;
  transition: background 0.3s;
}
.edu-footer__dot.is-fresh {
  background: #22C55E;
  box-shadow: 0 0 8px rgba(34, 197, 94, 0.6);
}
.edu-footer__stats {
  margin-left: 6px;
  padding-left: 6px;
  border-left: 1px solid rgba(255,255,255,0.1);
  color: #64748B;
  font-size: 11px;
}
.edu-footer__sync-hint {
  margin-left: 4px;
  padding: 2px 8px;
  border-radius: 10px;
  background: rgba(255,255,255,0.08);
  cursor: pointer;
  transition: background 0.2s;
}
.edu-footer__sync-hint:hover { background: rgba(255,255,255,0.15); color: #fff; }
.edu-footer__warn { color: #F97316; }

/* Page transition */
.fade-enter-active,
.fade-leave-active { transition: opacity 0.2s ease; }
.fade-enter-from,
.fade-leave-to { opacity: 0; }

/* ========== 响应式 ========== */

/* 1200px 以下：缩小间距 */
@media (max-width: 1200px) {
  .edu-header__inner { gap: var(--edu-space-3); }
  .edu-nav--desktop { gap: 0; }
  .edu-nav__item { padding: 6px 10px; font-size: var(--edu-font-sm); }
  .edu-logo__text { font-size: var(--edu-font-base); }
  .edu-search { width: 180px; }
}

/* 960px 以下：进一步缩小 */
@media (max-width: 960px) {
  .edu-header__inner { height: 56px; }
  .edu-logo__icon { font-size: 20px; }
  .edu-logo__text { font-size: var(--edu-font-sm); }
  .edu-nav__item { padding: 4px 8px; font-size: 13px; gap: 2px; }
  .edu-nav__item .el-icon { font-size: 14px; }
  .edu-search { width: 150px; }
}

/* 768px 以下：显示汉堡菜单，隐藏桌面导航 */
@media (max-width: 768px) {
  .edu-nav--desktop { display: none; }
  .edu-header__actions--desktop { display: none; }
  .edu-header__burger { display: inline-flex; }
  .edu-logo__text { max-width: 140px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .edu-footer__inner {
    grid-template-columns: 1fr;
    gap: var(--edu-space-4);
    padding: var(--edu-space-5) var(--edu-space-4);
  }
  .edu-header__inner { height: 56px; gap: var(--edu-space-2); }
}
</style>
