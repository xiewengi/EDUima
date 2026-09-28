<template>
  <div class="edu-ecosystem edu-page">
    <div class="edu-container">
      <div class="edu-placeholder edu-card">
        <div class="edu-placeholder__icon">
          <el-icon :size="64"><Share /></el-icon>
        </div>
        <h1 class="edu-placeholder__title">🌐 教育产业生态图谱</h1>
        <p class="edu-placeholder__desc">政府部门 · 学校院校 · 教育科技企业 · 投资方 · 行业协会 关系网络可视化</p>

        <!-- 模拟图谱 -->
        <div class="edu-graph">
          <div class="edu-graph__node edu-graph__node--center">
            <span class="edu-graph__label">🏫 广东省教育厅</span>
            <div class="edu-graph__dot"></div>
          </div>
          <div class="edu-graph__node edu-graph__node--1">
            <span class="edu-graph__label">🎓 清华附中湾区学校</span>
          </div>
          <div class="edu-graph__node edu-graph__node--2">
            <span class="edu-graph__label">🎓 东莞汽车技术学校</span>
          </div>
          <div class="edu-graph__node edu-graph__node--3">
            <span class="edu-graph__label">🎓 广州幼儿师范高等专科学校</span>
          </div>
          <div class="edu-graph__node edu-graph__node--4">
            <span class="edu-graph__label">🛠️ XX教育科技公司</span>
          </div>
          <div class="edu-graph__node edu-graph__node--5">
            <span class="edu-graph__label">🛠️ YY智慧校园</span>
          </div>
          <div class="edu-graph__node edu-graph__node--6">
            <span class="edu-graph__label">💰 ZZ投资集团</span>
          </div>
          <svg class="edu-graph__lines" viewBox="0 0 800 400" preserveAspectRatio="none">
            <line x1="400" y1="200" x2="200" y2="100" class="edu-graph__line" />
            <line x1="400" y1="200" x2="600" y2="100" class="edu-graph__line" />
            <line x1="400" y1="200" x2="200" y2="300" class="edu-graph__line" />
            <line x1="400" y1="200" x2="600" y2="300" class="edu-graph__line" />
            <line x1="200" y1="100" x2="600" y2="300" class="edu-graph__line edu-graph__line--success" />
            <line x1="600" y1="100" x2="200" y2="300" class="edu-graph__line edu-graph__line--success" />
            <line x1="400" y1="200" x2="700" y2="200" class="edu-graph__line" />
            <line x1="400" y1="200" x2="100" y2="200" class="edu-graph__line" />
          </svg>
        </div>

        <!-- 图例 -->
        <div class="edu-graph-legend">
          <span><span class="edu-graph-legend__dot edu-graph-legend__dot--center"></span> 政府部门</span>
          <span><span class="edu-graph-legend__dot edu-graph-legend__dot--school"></span> 学校院校</span>
          <span><span class="edu-graph-legend__dot edu-graph-legend__dot--company"></span> 教育科技企业</span>
          <span><span class="edu-graph-legend__dot edu-graph-legend__dot--investor"></span> 投资方</span>
          <span><el-icon class="edu-graph-legend__link edu-graph-legend__link--normal"><Connection /></el-icon> 监管/合作</span>
          <span><el-icon class="edu-graph-legend__link edu-graph-legend__link--success"><Connection /></el-icon> 中标/采购</span>
        </div>

        <el-alert
          type="info"
          :closable="false"
          show-icon
          title="本板块为示例占位"
          description="后续将基于 ECharts 力导向图，接入真实的教育产业机构关系数据。点击节点可查看机构详情、相关中标记录与政策依据。"
          style="margin-top: var(--edu-space-6)"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { Share, Connection } from '@element-plus/icons-vue'
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

.edu-graph {
  position: relative;
  width: 100%;
  height: 400px;
  background: linear-gradient(135deg, var(--edu-primary-lighter) 0%, #F0F4FF 100%);
  border-radius: var(--edu-radius-lg);
  overflow: hidden;
  margin-bottom: var(--edu-space-5);
}
.edu-graph__lines {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 1;
}
.edu-graph__line {
  stroke: var(--edu-primary);
  stroke-width: 2;
  stroke-dasharray: 6 4;
  opacity: 0.4;
}
.edu-graph__line--success {
  stroke: var(--edu-success);
  stroke-dasharray: none;
  opacity: 0.6;
}

.edu-graph__node {
  position: absolute;
  z-index: 2;
  transform: translate(-50%, -50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--edu-space-1);
  animation: pulse 3s ease-in-out infinite;
}
.edu-graph__node--center {
  left: 50%;
  top: 50%;
}
.edu-graph__node--1 { left: 25%; top: 25%; animation-delay: 0.3s; }
.edu-graph__node--2 { left: 75%; top: 25%; animation-delay: 0.6s; }
.edu-graph__node--3 { left: 25%; top: 75%; animation-delay: 0.9s; }
.edu-graph__node--4 { left: 75%; top: 75%; animation-delay: 1.2s; }
.edu-graph__node--5 { left: 87.5%; top: 50%; animation-delay: 1.5s; }
.edu-graph__node--6 { left: 12.5%; top: 50%; animation-delay: 1.8s; }

.edu-graph__label {
  font-size: var(--edu-font-sm);
  background: #fff;
  padding: 4px 12px;
  border-radius: var(--edu-radius-pill, 20px);
  box-shadow: var(--edu-shadow-sm);
  white-space: nowrap;
}
.edu-graph__dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: var(--edu-primary);
  box-shadow: 0 0 0 4px rgba(30, 90, 168, 0.2);
}

@keyframes pulse {
  0%, 100% { transform: translate(-50%, -50%) scale(1); }
  50% { transform: translate(-50%, -50%) scale(1.05); }
}

.edu-graph-legend {
  display: flex;
  justify-content: center;
  gap: var(--edu-space-5);
  flex-wrap: wrap;
  font-size: var(--edu-font-sm);
  color: var(--edu-text-secondary);
}
.edu-graph-legend span {
  display: flex;
  align-items: center;
  gap: 6px;
}
.edu-graph-legend__dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  display: inline-block;
}
.edu-graph-legend__dot--center { background: var(--edu-primary); }
.edu-graph-legend__dot--school { background: var(--edu-success); }
.edu-graph-legend__dot--company { background: var(--edu-accent); }
.edu-graph-legend__dot--investor { background: #8B5CF6; }
.edu-graph-legend__link--normal { color: var(--edu-primary); }
.edu-graph-legend__link--success { color: var(--edu-success); }
</style>
