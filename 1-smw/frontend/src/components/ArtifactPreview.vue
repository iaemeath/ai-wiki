<template>
  <div class="artifact-panel" :class="{ collapsed: isCollapsed }">
    <div class="artifact-header" @click="isCollapsed = !isCollapsed">
      <div class="header-left">
        <el-icon color="var(--text-muted)">
          <ArrowRight v-if="isCollapsed" />
          <ArrowDown v-else />
        </el-icon>
        <span class="panel-title">预览</span>
        <el-tag v-if="artifactName && !isCollapsed" size="small" effect="dark" type="info">
          {{ artifactName }}
        </el-tag>
      </div>
      <div class="header-right">
        <el-tag v-if="!isCollapsed" size="small" type="success" effect="dark" class="sandbox-tag">
          <el-icon :size="12"><Lock /></el-icon>
          沙箱
        </el-tag>
      </div>
    </div>

    <div v-show="!isCollapsed" class="artifact-body">
      <!-- Loading -->
      <div v-if="loading" class="loading-state">
        <el-icon class="is-loading" :size="18" color="var(--accent-blue)"><Loading /></el-icon>
        <span>加载预览...</span>
      </div>

      <!-- Empty -->
      <div v-else-if="!htmlContent" class="empty-state">
        <span>暂无预览内容</span>
      </div>

      <!-- Preview iframe -->
      <iframe
        v-else
        ref="frameRef"
        :srcdoc="htmlContent"
        class="preview-frame"
        sandbox="allow-scripts"
        title="Artifact Preview"
      ></iframe>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  htmlContent: { type: String, default: '' },
  artifactName: { type: String, default: '预览文件' },
  loading: { type: Boolean, default: false },
})

const isCollapsed = ref(false)
const frameRef = ref(null)
</script>

<style scoped>
.artifact-panel {
  background: var(--bg-secondary);
  transition: height 0.2s ease;
}

.artifact-panel.collapsed {
  flex-shrink: 0;
}

.artifact-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 16px;
  cursor: pointer;
  user-select: none;
  border-bottom: 1px solid var(--border-color);
  transition: background 0.15s;
}

.artifact-header:hover {
  background: var(--bg-hover);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-right {
  display: flex;
  align-items: center;
}

.panel-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-primary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.sandbox-tag {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  padding: 2px 6px;
}

.artifact-body {
  height: 240px;
  overflow: hidden;
}

.loading-state,
.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  height: 100%;
  color: var(--text-muted);
  font-size: 12px;
}

.preview-frame {
  width: 100%;
  height: 100%;
  border: none;
  background: white;
}
</style>
