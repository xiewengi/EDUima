<template>
  <div class="edu-thinktank edu-page">
    <div class="edu-container">
      <!-- 页面标题 -->
      <div class="edu-page-header">
        <div>
          <h1 class="edu-page-title">
            <el-icon><View /></el-icon> 智库观察
          </h1>
          <p class="edu-page-subtitle">教育行业智库报告与观察视角，洞察行业趋势。</p>
        </div>
        <div class="edu-page-meta">
          <el-tag type="info">建设中</el-tag>
        </div>
      </div>

      <!-- 占位空态：数据口径确定后接入 -->
      <div class="edu-card edu-thinktank__placeholder">
        <el-empty description="智库观察内容建设中，敬请期待" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { View } from '@element-plus/icons-vue'
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
.edu-thinktank__placeholder {
  padding: var(--edu-space-6) var(--edu-space-4);
}
</style>
