import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 120000,
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.response.use(
  r => r.data,
  e => {
    const m = e.response?.data?.detail || e.response?.data?.message || e.message || 'Request failed'
    console.error('[API]', m)
    return Promise.reject(new Error(m))
  }
)

// --- 会话管理 ---

/** 创建新会话 → { session_id } */
export function createSession() {
  return api.post('/session/create')
}

/** 上传 Excel 到已有会话 → { requirements_count, requirements, next_step } */
export function uploadExcel(sessionId, file) {
  const fd = new FormData()
  fd.append('file', file)
  return api.post(`/session/${sessionId}/upload-excel`, fd, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 300000,  // 上传+分析可能较长
  })
}

/** 获取会话状态 → { step, requirements_count, questions_count, questions_answered } */
export function getSessionStatus(sid) {
  return api.get(`/session/${sid}/status`)
}

/** 获取当前问题 → { question, total_questions, current_index, step } */
export function getCurrentQuestion(sid) {
  return api.get(`/session/${sid}/current-question`)
}

/** 提交答案 → { next_step, message, remaining_questions } */
export function submitAnswer(sid, data) {
  return api.post(`/session/${sid}/answer`, data)
}

/** 获取最终产出 → { outputs: { adr, mermaid_diagrams, skeleton_files } } */
export function getOutputs(sid) {
  return api.get(`/session/${sid}/outputs`)
}

/** 获取指定 Mermaid 图 → { mermaid, index, total } */
export function getDiagram(sid, index = 0) {
  return api.get(`/session/${sid}/diagram/${index}`)
}

/** 获取指定骨架文件 → { file: { path, content }, index, total } */
export function getSkeleton(sid, index = 0) {
  return api.get(`/session/${sid}/skeleton/${index}`)
}

/** 健康检查 */
export function healthCheck() { return api.get('/health') }

export default api
