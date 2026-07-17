<template>
  <div class="socratic-panel">
    <div class="panel-header">
      <span class="panel-title">苏格拉底问答</span>
      <el-tag v-if="contextReq" size="small" effect="dark" type="info">
        {{ contextReq.title || contextReq.name || ('#' + (contextReq.index || contextReq.id)) }}
      </el-tag>
    </div>

    <div class="panel-body">
      <!-- Loading -->
      <div v-if="loading" class="loading-state">
        <el-icon class="is-loading" :size="24" color="var(--accent-blue)"><Loading /></el-icon>
        <span>加载中...</span>
      </div>

      <!-- Current Question Card -->
      <div v-else-if="question" class="question-card">
        <div class="q-header">
          <el-icon color="var(--accent-blue)"><QuestionFilled /></el-icon>
          <span class="q-label">当前问题</span>
        </div>
        <div class="q-text">{{ question.question || question.content || question.text }}</div>

        <!-- Options (radio) -->
        <div v-if="question.options && question.options.length > 0" class="q-options">
          <el-radio-group v-model="selectedOption" class="option-group">
            <el-radio
              v-for="(opt, i) in question.options"
              :key="i"
              :value="opt.value || opt"
              class="option-item"
            >
              {{ opt.label || opt.text || opt.value || opt }}
            </el-radio>
          </el-radio-group>
        </div>

        <!-- Custom Input -->
        <div class="q-input">
          <el-input
            v-model="customInput"
            type="textarea"
            :rows="3"
            placeholder="输入你的答案..."
            resize="none"
          />
        </div>

        <!-- Actions -->
        <div class="q-actions">
          <el-button
            type="primary"
            :loading="submitting"
            @click="handleSubmit"
            :disabled="!selectedOption && !customInput.trim()"
          >
            <el-icon><Check /></el-icon>
            确认提交
          </el-button>
          <el-button
            text
            :disabled="submitting"
            @click="handleSkip"
          >
            <el-icon><DArrowRight /></el-icon>
            跳过
          </el-button>
        </div>
      </div>

      <!-- No Question -->
      <div v-else class="empty-state">
        <el-icon :size="32" color="var(--text-muted)"><ChatLineSquare /></el-icon>
        <span>等待问题...</span>
      </div>

      <!-- History -->
      <div class="history-section">
        <div class="history-header">
          <el-icon color="var(--text-muted)"><Clock /></el-icon>
          <span>历史记录</span>
        </div>
        <div class="history-list" ref="historyRef">
          <div v-if="history.length === 0" class="history-empty">
            暂无问答记录
          </div>
          <div
            v-for="(item, i) in history"
            :key="i"
            class="history-item"
          >
            <div class="h-question">
              <el-icon color="var(--accent-blue)" :size="14"><QuestionFilled /></el-icon>
              <span>{{ item.question || item.content || item.text }}</span>
            </div>
            <div class="h-answer">
              <el-icon color="var(--accent-green)" :size="14"><Check /></el-icon>
              <span>{{ item.answer || item.response || '(已跳过)' }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'

const props = defineProps({
  question: { type: Object, default: null },
  history: { type: Array, default: () => [] },
  contextReq: { type: Object, default: null },
  loading: { type: Boolean, default: false },
  submitting: { type: Boolean, default: false },
})

const emit = defineEmits(['submit', 'skip'])

const selectedOption = ref(null)
const customInput = ref('')
const historyRef = ref(null)

// Reset inputs when question changes
watch(() => props.question, () => {
  selectedOption.value = null
  customInput.value = ''
})

// Auto-scroll history
watch(() => props.history.length, async () => {
  await nextTick()
  if (historyRef.value) {
    historyRef.value.scrollTop = historyRef.value.scrollHeight
  }
})

function handleSubmit() {
  emit('submit', {
    option: selectedOption.value,
    input: customInput.value.trim(),
  })
}

function handleSkip() {
  emit('skip')
}
</script>

<style scoped>
.socratic-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--bg-primary);
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
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* Loading */
.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 40px;
  color: var(--text-muted);
  font-size: 13px;
}

/* Empty */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 40px;
  color: var(--text-muted);
  font-size: 13px;
}

/* Question Card */
.question-card {
  padding: 16px;
  border-bottom: 1px solid var(--border-color);
  flex-shrink: 0;
}

.q-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 10px;
}

.q-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--accent-blue);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.q-text {
  font-size: 14px;
  line-height: 1.6;
  color: var(--text-primary);
  margin-bottom: 14px;
  padding: 12px;
  background: var(--bg-tertiary);
  border-radius: 8px;
  border: 1px solid var(--border-color);
}

.q-options {
  margin-bottom: 12px;
}

.option-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.option-item {
  padding: 8px 12px;
  background: var(--bg-tertiary);
  border-radius: 6px;
  border: 1px solid var(--border-color);
  transition: border-color 0.2s;
}

.option-item:hover {
  border-color: var(--accent-blue);
}

.q-input {
  margin-bottom: 12px;
}

.q-actions {
  display: flex;
  gap: 8px;
}

/* History */
.history-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.history-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 16px;
  font-size: 12px;
  color: var(--text-muted);
  border-bottom: 1px solid var(--border-color);
  flex-shrink: 0;
}

.history-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px 16px;
}

.history-empty {
  text-align: center;
  color: var(--text-muted);
  font-size: 12px;
  padding: 20px;
}

.history-item {
  margin-bottom: 12px;
  padding: 10px;
  background: var(--bg-tertiary);
  border-radius: 6px;
  border: 1px solid var(--border-color);
}

.h-question {
  display: flex;
  gap: 6px;
  margin-bottom: 6px;
  font-size: 13px;
  color: var(--text-primary);
  line-height: 1.4;
}

.h-answer {
  display: flex;
  gap: 6px;
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.4;
  padding-left: 20px;
}
</style>
