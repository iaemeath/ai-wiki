<template>
  <div class="dashboard">
    <!-- 标题栏 -->
    <header class="title-bar">
      <div class="title-left">
        <el-icon :size="22" color="var(--accent-blue)"><Monitor /></el-icon>
        <h1>1-SMW 确定性系统工作台</h1>
      </div>
      <div class="title-right">
        <el-tag v-if="sessionId" type="info" size="small" effect="dark">
          Session: {{ sessionId.substring(0, 8) }}...
        </el-tag>
        <el-tag v-if="sessionStep" :type="stepTagType" size="small" effect="dark">
          {{ stepLabel }}
        </el-tag>
        <el-button v-if="sessionId" size="small" text @click="resetSession">
          <el-icon><Close /></el-icon>
          结束会话
        </el-button>
      </div>
    </header>

    <!-- 上传着陆页 -->
    <div v-if="!sessionId" class="upload-landing">
      <div class="upload-card">
        <el-icon :size="48" color="var(--accent-blue)"><Upload /></el-icon>
        <h2>上传 Excel 需求文档</h2>
        <p class="upload-desc">上传 .xlsx 文件启动苏格拉底式需求对齐会话</p>
        <el-upload
          drag
          accept=".xlsx,.xls"
          :auto-upload="false"
          :show-file-list="false"
          :on-change="handleFileSelect"
          class="upload-area"
        >
          <el-icon :size="36" class="upload-icon"><Plus /></el-icon>
          <div class="upload-text">
            将 Excel 文件拖拽到此处，或 <em>点击选择</em>
          </div>
          <template #tip>
            <div class="upload-tip">仅支持 .xlsx 格式</div>
          </template>
        </el-upload>
      </div>
    </div>

    <!-- 工作区 -->
    <div v-else class="workspace">
      <div class="main-panel">
        <div class="panel-left">
          <RequirementList
            :requirements="requirements"
            :current-id="currentRequirementId"
            :loading="loading.requirements"
            @upload="handleFileSelect"
          />
        </div>
        <div class="panel-center">
          <SocraticPanel
            :question="currentQuestion"
            :history="qaHistory"
            :context-req="currentRequirement"
            :loading="loading.question"
            :submitting="loading.submitting"
            @submit="handleAnswerSubmit"
          />
        </div>
        <div class="panel-right">
          <MermaidRenderer
            :diagram="diagramDef"
            :diagram-name="diagramName"
            :loading="loading.diagram"
          />
        </div>
      </div>
      <div class="bottom-panel">
        <ArtifactPreview
          :html-content="artifactHtml"
          :artifact-name="artifactName"
          :loading="loading.artifact"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onUnmounted } from 'vue'
import {
  createSession,
  uploadExcel,
  getSessionStatus,
  getCurrentQuestion,
  submitAnswer,
  getOutputs,
  getDiagram,
  getSkeleton,
} from '../api/index.js'
import RequirementList from '../components/RequirementList.vue'
import SocraticPanel from '../components/SocraticPanel.vue'
import MermaidRenderer from '../components/MermaidRenderer.vue'
import ArtifactPreview from '../components/ArtifactPreview.vue'

const sessionId = ref(null)
const sessionStep = ref(null)
const requirements = ref([])
const currentRequirementId = ref(null)
const currentQuestion = ref(null)
const currentRequirement = ref(null)
const qaHistory = ref([])
const diagramDef = ref('')
const diagramName = ref('逻辑图纸')
const artifactHtml = ref('')
const artifactName = ref('预览文件')

const loading = ref({
  requirements: false,
  question: false,
  submitting: false,
  diagram: false,
  artifact: false,
})

let pollTimer = null

const stepLabelMap = {
  init: '初始化',
  analyzing: '需求分析中...',
  questioning: '等待回答',
  answering: '处理中',
  evaluating: '评估中...',
  generating: '生成产出...',
  completed: '已完成',
}
const stepTagTypeMap = {
  init: 'info',
  analyzing: 'warning',
  questioning: 'primary',
  answering: 'warning',
  evaluating: 'warning',
  generating: 'warning',
  completed: 'success',
}
const stepLabel = ref('')
const stepTagType = ref('info')

// --- 上传流程：先创建会话，再上传 Excel ---
async function handleFileSelect(uploadFile) {
  try {
    loading.value.requirements = true

    // Step 1: 创建会话
    const sessionRes = await createSession()
    const sid = sessionRes.session_id
    sessionId.value = sid

    // Step 2: 上传 Excel
    const uploadRes = await uploadExcel(sid, uploadFile.raw || uploadFile)
    requirements.value = uploadRes.requirements || []
    sessionStep.value = uploadRes.next_step
    updateStepDisplay()

    // Step 3: 启动轮询
    startPolling()
  } catch (err) {
    console.error('上传失败:', err)
  } finally {
    loading.value.requirements = false
  }
}

// --- 轮询状态 ---
function startPolling() {
  if (pollTimer) clearInterval(pollTimer)
  pollTimer = setInterval(pollSession, 3000)
  // 立即拉一次
  pollSession()
}

async function pollSession() {
  if (!sessionId.value) return

  try {
    // 拉状态
    const status = await getSessionStatus(sessionId.value)
    sessionStep.value = status.step
    updateStepDisplay()

    // 根据状态加载不同数据
    if (status.step === 'questioning' || status.step === 'evaluating') {
      const qRes = await getCurrentQuestion(sessionId.value)
      currentQuestion.value = qRes.question
      if (qRes.question?.context) {
        currentRequirementId.value = qRes.question.context
        currentRequirement.value = requirements.value.find(r => r.id === qRes.question.context) || null
      }
    }

    if (status.step === 'questioning') {
      // 只在 questioning 阶段加载历史
      await loadHistory()
    }

    if (status.step === 'completed') {
      // 完成后一次拉所有产出
      clearInterval(pollTimer)
      pollTimer = null
      await loadOutputs()
    }
  } catch (err) {
    console.error('轮询失败:', err)
  }
}

async function loadHistory() {
  if (!sessionId.value) return
  // 从 question 的 context 可以推断历史; 或用 outputs 的 ADR 推理
  // 简化: 前端本地维护已回答的问题列表
}

async function loadOutputs() {
  if (!sessionId.value) return
  try {
    const outRes = await getOutputs(sessionId.value)
    const outputs = outRes.outputs

    // Mermaid 图
    if (outputs.mermaid_diagrams?.length > 0) {
      diagramDef.value = outputs.mermaid_diagrams[0]
      diagramName.value = `架构图 (${outputs.mermaid_diagrams.length}张)`
    }

    // 骨架文件
    if (outputs.skeleton_files?.length > 0) {
      const skel = outputs.skeleton_files[0]
      artifactHtml.value = skel.content || ''
      artifactName.value = skel.path || '预览文件'
    }
  } catch (err) {
    console.error('加载产出失败:', err)
  }
}

function updateStepDisplay() {
  stepLabel.value = stepLabelMap[sessionStep.value] || sessionStep.value
  stepTagType.value = stepTagTypeMap[sessionStep.value] || 'info'
}

// --- 提交答案 ---
async function handleAnswerSubmit(answerData) {
  if (!sessionId.value) return
  loading.value.submitting = true
  try {
    await submitAnswer(sessionId.value, answerData)
    // 添加到本地历史
    qaHistory.value.push({
      role: 'user',
      content: answerData.answer,
      question_id: answerData.question_id,
    })
    // 清空当前问题，等待轮询更新
    sessionStep.value = 'evaluating'
    updateStepDisplay()
  } catch (err) {
    console.error('提交失败:', err)
  } finally {
    loading.value.submitting = false
  }
}

// --- 重置 ---
function resetSession() {
  if (pollTimer) { clearInterval(pollTimer); pollTimer = null }
  sessionId.value = null
  sessionStep.value = null
  requirements.value = []
  currentQuestion.value = null
  qaHistory.value = []
  diagramDef.value = ''
  artifactHtml.value = ''
}

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})
</script>

<style scoped>
.dashboard {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--bg-primary);
  overflow: hidden;
}
.title-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-color);
  flex-shrink: 0;
}
.title-left {
  display: flex;
  align-items: center;
  gap: 10px;
}
.title-left h1 {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  letter-spacing: 0.5px;
}
.title-right {
  display: flex;
  align-items: center;
  gap: 12px;
}
.upload-landing {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}
.upload-card {
  text-align: center;
  padding: 48px;
}
.upload-card h2 { margin-top: 16px; font-size: 20px; color: var(--text-primary); }
.upload-desc { margin-top: 8px; color: var(--text-muted); font-size: 13px; }
.upload-area { margin-top: 24px; }
.upload-icon { margin-bottom: 8px; }
.upload-text { color: var(--text-secondary); font-size: 13px; }
.upload-text em { color: var(--accent-blue); font-style: normal; }
.upload-tip { color: var(--text-muted); font-size: 12px; margin-top: 8px; }
.workspace { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
.main-panel { flex: 1; display: flex; overflow: hidden; gap: 0; }
.panel-left { width: 35%; min-width: 280px; border-right: 1px solid var(--border-color); overflow: hidden; }
.panel-center { flex: 1; min-width: 300px; border-right: 1px solid var(--border-color); overflow: hidden; }
.panel-right { width: 25%; min-width: 240px; overflow: hidden; }
.bottom-panel { flex-shrink: 0; border-top: 1px solid var(--border-color); }
</style>
