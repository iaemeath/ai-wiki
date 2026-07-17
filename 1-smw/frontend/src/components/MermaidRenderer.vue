<template>
  <div class="mermaid-panel">
    <div class="panel-header">
      <span class="panel-title">{{ diagramName }}</span>
      <el-tooltip content="刷新图纸" placement="top">
        <el-button text size="small" @click="refreshDiagram">
          <el-icon color="var(--text-muted)"><Refresh /></el-icon>
        </el-button>
      </el-tooltip>
    </div>

    <div class="panel-body">
      <!-- Loading -->
      <div v-if="loading" class="loading-state">
        <el-icon class="is-loading" :size="20" color="var(--accent-blue)"><Loading /></el-icon>
        <span>加载图纸...</span>
      </div>

      <!-- Diagram -->
      <div v-else-if="diagram" class="diagram-container">
        <div v-if="renderError" class="error-fallback">
          <el-alert
            title="图纸渲染失败"
            type="warning"
            :closable="false"
            show-icon
            :description="renderError"
          />
          <pre class="raw-text">{{ diagram }}</pre>
        </div>
        <div
          v-show="!renderError"
          ref="mermaidRef"
          class="mermaid-content"
        ></div>
      </div>

      <!-- Empty -->
      <div v-else class="empty-state">
        <el-icon :size="28" color="var(--text-muted)"><Share /></el-icon>
        <span>暂无图纸</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  diagram: { type: String, default: '' },
  diagramName: { type: String, default: '逻辑图纸' },
  loading: { type: Boolean, default: false },
})

const mermaidRef = ref(null)
const renderError = ref(null)
let mermaidInstance = null

// Render diagram
async function renderDiagram() {
  if (!props.diagram || !mermaidRef.value) return

  renderError.value = null

  try {
    const mermaid = await import('mermaid')

    mermaid.initialize({
      startOnLoad: false,
      theme: 'dark',
      themeVariables: {
        background: '#1e1e2e',
        primaryColor: '#2d2d44',
        primaryBorderColor: '#3d3d5c',
        primaryTextColor: '#e0e0f0',
        lineColor: '#6c8cff',
        secondaryColor: '#252536',
        tertiaryColor: '#363650',
        fontFamily: '"Cascadia Code","JetBrains Mono",monospace',
      },
      securityLevel: 'loose',
    })

    const { svg } = await mermaid.render('mermaid-svg-' + Date.now(), props.diagram)
    mermaidRef.value.innerHTML = svg
  } catch (err) {
    console.error('Mermaid render error:', err)
    renderError.value = err.message || '无法解析图纸定义'
  }
}

// Refresh
function refreshDiagram() {
  renderDiagram()
}

// Watch for changes
watch(() => props.diagram, () => {
  if (props.diagram) {
    nextTick(() => renderDiagram())
  }
})

onMounted(() => {
  if (props.diagram) {
    nextTick(() => renderDiagram())
  }
})
</script>

<style scoped>
.mermaid-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--bg-secondary);
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-color);
  flex-shrink: 0;
}

.panel-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.panel-body {
  flex: 1;
  overflow: auto;
  padding: 12px;
}

.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 30px;
  color: var(--text-muted);
  font-size: 12px;
}

.diagram-container {
  min-height: 100%;
}

.mermaid-content {
  display: flex;
  justify-content: center;
  padding: 8px;
}

.mermaid-content :deep(svg) {
  max-width: 100%;
  height: auto;
}

.error-fallback {
  padding: 8px;
}

.raw-text {
  margin-top: 12px;
  padding: 12px;
  background: var(--bg-tertiary);
  border-radius: 6px;
  font-size: 11px;
  line-height: 1.5;
  color: var(--text-secondary);
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 300px;
  overflow: auto;
}
</style>
