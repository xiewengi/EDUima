<template>
  <div class="edu-exhibition edu-page">
    <div class="edu-container">
      <!-- 页面标题 -->
      <div class="edu-page-header">
        <div>
          <h1 class="edu-page-title">
            <el-icon><Flag /></el-icon> 重磅展会
          </h1>
          <p class="edu-page-subtitle">教育行业重点展会信息，展会动态与亮点速览。</p>
        </div>
        <div class="edu-page-meta">
          <el-tag type="info">建设中</el-tag>
        </div>
      </div>

      <!-- 占位空态：数据口径确定后接入 -->
      <div class="edu-card edu-exhibition__placeholder">
        <el-empty description="重磅展会内容建设中，敬请期待" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { Flag } from '@element-plus/icons-vue'
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
.edu-exhibition__placeholder {
  padding: var(--edu-space-6) var(--edu-space-4);
}
</style>
