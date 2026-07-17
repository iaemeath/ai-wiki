# 1-SMW 确定性系统工作台

## 概述

1-SMW（Specification-Mindset-Workflow）是一套需求工程辅助工具。
通过苏格拉底式追问，将模糊需求收敛为三类工程交付物：

- **ADR**（架构决策记录，Markdown）
- **Mermaid 逻辑图**（架构图 / 数据流图）
- **Vue 骨架网页**（隔离单文件组件）

## 工作流

```
Excel 需求表 → AI 分析 → 苏格拉底追问 → 评估 → 三件套产出
                           (human-in-the-loop)
```

## 技术栈

| 层 | 技术 |
|---|---|
| 后端 | FastAPI 0.115 + LangGraph 0.2 + httpx |
| 前端 | Vue 3 + Element Plus + Mermaid.js v11 |
| AI | GLM-5.2（内网网关 192.168.6.100:19090）|
| 部署 | Windows + Nginx（离线就绪）|

## 快速开始

详见 [deploy-guide.md](deploy-guide.md)

### 后端

```bash
pip install -r backend/requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 前端

```bash
cd frontend
npm install
npm run dev     # 开发 → localhost:5173
npm run build   # 生产 → dist/
```

## API

| 方法 | 路径 | 用途 |
|---|---|---|
| POST | `/api/session/create` | 创建会话 |
| POST | `/api/session/{id}/upload-excel` | 上传 Excel |
| GET | `/api/session/{id}/status` | 会话状态 |
| GET | `/api/session/{id}/current-question` | 当前问题 |
| POST | `/api/session/{id}/answer` | 提交答案 |
| GET | `/api/session/{id}/outputs` | 获取产出 |
| GET | `/api/session/{id}/diagram/{i}` | Mermaid 图 |
| GET | `/api/session/{id}/skeleton/{i}` | 骨架文件 |

## 项目结构

```
1-smw/
├── backend/app/          # FastAPI + LangGraph（8 模块）
├── frontend/src/         # Vue 3（9 文件）
├── deploy/               # 部署脚本
├── offline-deps/         # 离线依赖包
└── deploy-guide.md       # 部署指南
```
