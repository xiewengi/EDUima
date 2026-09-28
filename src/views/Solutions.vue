<template>
  <div class="edu-solutions edu-page">
    <div class="edu-container">
      <div class="edu-placeholder edu-card">
        <div class="edu-placeholder__icon">
          <el-icon :size="64"><Lightning /></el-icon>
        </div>
        <h1 class="edu-placeholder__title">💡 解决方案中心</h1>
        <p class="edu-placeholder__desc">教育行业数字化解决方案集合，持续更新中...</p>

        <div class="edu-solutions-grid">
          <div v-for="item in demoSolutions" :key="item.name" class="edu-solution-card edu-card">
            <div class="edu-solution-card__icon" :style="{ background: item.color }">
              <el-icon :size="28"><component :is="item.icon" /></el-icon>
            </div>
            <div class="edu-solution-card__name">{{ item.name }}</div>
            <div class="edu-solution-card__desc">{{ item.desc }}</div>
            <div class="edu-solution-card__tags">
              <el-tag v-for="tag in item.tags" :key="tag" size="small" type="info">{{ tag }}</el-tag>
            </div>
          </div>
        </div>

        <el-alert
          type="info"
          :closable="false"
          show-icon
          title="本板块为示例占位"
          description="后续将接入真实的教育行业解决方案内容，包括智慧校园、教育数据中台、实训装备等。"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { Lightning, Monitor, DataAnalysis, Cpu, Connection } from '@element-plus/icons-vue'

const demoSolutions = [
  {
    name: '智慧校园平台',
    desc: '一站式校园数字化管理解决方案',
    icon: Monitor,
    color: '#1E5AA8',
    tags: ['K12', '高教', '一卡通']
  },
  {
    name: '教育数据中台',
    desc: '数据治理 + AI 智能分析决策支持',
    icon: DataAnalysis,
    color: '#8B5CF6',
    tags: ['数据', 'AI', '大屏']
  },
  {
    name: '实训装备方案',
    desc: '职业教育实训中心整体建设方案',
    icon: Cpu,
    color: '#10B981',
    tags: ['职业教育', '实训室', '硬件']
  },
  {
    name: '家校互联系统',
    desc: '家校沟通、安全管理、家长课堂',
    icon: Connection,
    color: '#F4A261',
    tags: ['家校', '安全', '小程序']
  }
]
</script>

<style scoped>
.edu-placeholder {
  padding: var(--edu-space-8) var(--edu-space-6);
  text-align: center;
  border-radius: var(--edu-radius-xl);
}
.edu-placeholder__icon {
  color: var(--edu-primary);
  margin-bottom: var(--edu-space-4);
}
.edu-placeholder__title {
  font-size: var(--edu-font-2xl);
  margin-bottom: var(--edu-space-2);
}
.edu-placeholder__desc {
  color: var(--edu-text-secondary);
  font-size: var(--edu-font-md);
  margin-bottom: var(--edu-space-6);
}
.edu-solutions-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--edu-space-4);
  margin-bottom: var(--edu-space-6);
}
.edu-solution-card {
  padding: var(--edu-space-5);
  text-align: left;
  cursor: default;
}
.edu-solution-card__icon {
  width: 56px;
  height: 56px;
  border-radius: var(--edu-radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  margin-bottom: var(--edu-space-3);
}
.edu-solution-card__name {
  font-size: var(--edu-font-md);
  font-weight: 600;
  margin-bottom: var(--edu-space-1);
}
.edu-solution-card__desc {
  font-size: var(--edu-font-sm);
  color: var(--edu-text-secondary);
  margin-bottom: var(--edu-space-3);
  line-height: 1.5;
}
.edu-solution-card__tags {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

@media (max-width: 960px) {
  .edu-solutions-grid { grid-template-columns: repeat(2, 1fr); }
}
</style>
