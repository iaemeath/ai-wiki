<template>
  <div class="req-list">
    <div class="panel-header">
      <span class="panel-title">需求条目</span>
      <el-tag size="small" effect="dark" type="info">
        {{ completedCount }}/{{ requirements.length }}
      </el-tag>
    </div>

    <!-- Progress Bar -->
    <div class="progress-section">
      <el-progress
        :percentage="progressPercent"
        :stroke-width="6"
        :show-text="false"
      />
      <span class="progress-label">{{ progressPercent }}%</span>
    </div>

    <!-- Upload Area (when no requirements) -->
    <div v-if="requirements.length === 0" class="empty-upload">
      <el-upload
        drag
        accept=".xlsx,.xls"
        :auto-upload="false"
        :show-file-list="false"
        :on-change="handleUpload"
        class="upload-inline"
      >
        <el-icon :size="28" color="var(--accent-blue)"><Plus /></el-icon>
        <div class="upload-text-sm">上传 .xlsx 文件</div>
      </el-upload>
    </div>

    <!-- Requirement Items -->
    <div v-else class="req-items" ref="listRef">
      <div
        v-for="req in requirements"
        :key="req.id || req.index"
        class="req-item"
        :class="{
          active: (req.id === currentId || req.index === currentId),
          completed: req.status === 'aligned' || req.status === 'completed',
          ambiguous: req.status === 'ambiguous' || req.status === 'questioned',
        }"
      >
        <div class="req-icon">
          <el-icon v-if="req.status === 'aligned' || req.status === 'completed'" color="var(--accent-green)"><SuccessFilled /></el-icon>
          <el-icon v-else-if="req.status === 'ambiguous' || req.status === 'questioned'" color="var(--accent-yellow)"><WarningFilled /></el-icon>
          <el-icon v-else color="var(--text-muted)"><Clock /></el-icon>
        </div>
        <div class="req-content">
          <div class="req-title">{{ req.title || req.name || req.content || ('条目 ' + (req.index || req.id)) }}</div>
          <div class="req-meta">
            <el-tag
              :type="statusTagType(req.status)"
              size="small"
              effect="dark"
            >
              {{ statusLabel(req.status) }}
            </el-tag>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  requirements: { type: Array, default: () => [] },
  currentId: { type: [String, Number], default: null },
  loading: { type: Boolean, default: false },
})

const emit = defineEmits(['upload'])

const completedCount = computed(() =>
  props.requirements.filter(r => r.status === 'aligned' || r.status === 'completed').length
)

const progressPercent = computed(() =>
  props.requirements.length > 0
    ? Math.round((completedCount.value / props.requirements.length) * 100)
    : 0
)

function handleUpload(file) {
  emit('upload', file)
}

function statusTagType(status) {
  if (status === 'aligned' || status === 'completed') return 'success'
  if (status === 'ambiguous' || status === 'questioned') return 'warning'
  return 'info'
}

function statusLabel(status) {
  const map = {
    pending: '待处理',
    processing: '处理中',
    aligned: '已对齐',
    completed: '已完成',
    ambiguous: '有疑问',
    questioned: '有疑问',
  }
  return map[status] || status || '待处理'
}
</script>

<style scoped>
.req-list {
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

.progress-section {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  flex-shrink: 0;
}

.progress-section .el-progress {
  flex: 1;
}

.progress-label {
  font-size: 12px;
  color: var(--text-muted);
  min-width: 36px;
  text-align: right;
}

/* Empty upload */
.empty-upload {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.upload-inline {
  width: 100%;
}

.upload-text-sm {
  margin-top: 6px;
  color: var(--text-muted);
  font-size: 12px;
}

/* Requirement Items */
.req-items {
  flex: 1;
  overflow-y: auto;
  padding: 4px 0;
}

.req-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 16px;
  cursor: pointer;
  transition: background 0.15s;
  border-left: 3px solid transparent;
}

.req-item:hover {
  background: var(--bg-hover);
}

.req-item.active {
  background: rgba(108, 140, 255, 0.08);
  border-left-color: var(--accent-blue);
}

.req-item.completed {
  opacity: 0.7;
}

.req-item.ambiguous {
  border-left-color: var(--accent-yellow);
}

.req-icon {
  flex-shrink: 0;
  margin-top: 2px;
}

.req-content {
  flex: 1;
  min-width: 0;
}

.req-title {
  font-size: 13px;
  color: var(--text-primary);
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.req-meta {
  margin-top: 4px;
}
</style>
