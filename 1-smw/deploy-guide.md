# 1-SMW 确定性系统工作台 — 内网部署指南

## 适用环境

| 项目 | 值 |
|---|---|
| 部署目标 | Windows 11 (192.168.4.215) |
| 操作系统 | Windows 11 Pro |
| 网络 | 无互联网（纯内网）|
| AI 网关 | 192.168.6.100:19090 |
| SSH 隧道 | localhost:19090 → 192.168.6.100:19090 |
| 统一入口 | 端口 3201（Nginx）|

## 端口对照表

| 端口 | 用途 | 说明 |
|---|---|---|
| 3201 | Nginx 统一入口 | 浏览器访问此端口 |
| 8000 | FastAPI 后端 | 直接 API 访问 |
| 5173 | Vite 开发服务器 | 前端热重载用 |
| 19090 | AI 网关（经 SSH 隧道） | Windows 上无需关注，WSL 维护 |

## 前置条件

- [ ] **Python 3.11+** — `python --version`
- [ ] **Node.js 18+** — `node --version`

## 搭建步骤

### Step 1: 安装 Python 依赖

```powershell
cd C:\Users\Administrator\1-smw
python -m venv .venv
.venv\Scripts\pip.exe install --no-index --find-links offline-deps\python -r backend\requirements.txt
```

### Step 2: 启动后端

```powershell
# 方式一：直接运行
.venv\Scripts\uvicorn.exe app.main:app --host 0.0.0.0 --port 8000

# 方式二：用部署脚本（自动设环境变量）
.\deploy\start-backend.ps1
```

验证：浏览器打开 `http://localhost:8000/health` 应返回 `{"status":"ok"}`

API 文档：`http://localhost:8000/docs`（Swagger UI）

### Step 3: 启动前端（开发模式）

```powershell
cd frontend
npm run dev
```

浏览器打开 `http://localhost:5173`

### Step 4: Nginx 统一入口（可选）

从 `https://nginx.org/en/download.html` 下载 Windows 版 Nginx，解压到 `C:\1-smw\nginx\`，复制 `deploy\nginx.conf` 覆盖配置，双击 `nginx.exe`。

`http://localhost:3201` 统一访问。

## AI 网关隧道

在 **WSL 环境**（不是 Windows）中建立 SSH 隧道：

```bash
# 确保 VPN (iNode) 已连接
~/tunnel-start
```

如果手动建立：

```bash
autossh -M 0 -o "ServerAliveInterval=30" \
  -L 19090:192.168.6.100:19090 \
  Administrator@192.168.4.215 -N -f
```

隧道建立后验证：

```bash
curl http://localhost:19090/api/anthropic/v1/messages -X POST \
  -H "Content-Type: application/json" \
  -H "x-api-key: caf4bb9dfcec493fa61e7efb2ac37bb3" \
  -d '{"model":"glm-5.2","max_tokens":10,"messages":[{"role":"user","content":"hi"}]}'
```

> **注意**：Windows 上无需关心隧道，隧道由 WSL 侧的 autossh 自动维护。
> `config.py` 默认值已设为 `http://localhost:19090/...`，Windows 后端直接连 localhost 即可。

## 使用流程

```
1. 浏览器打开 → http://localhost:3201 或 http://localhost:5173
2. 点击上传区域，选择 .xlsx 需求文件
3. 后端自动创建会话 + 分析需求
4. 等待片刻 → 苏格拉底问题弹出
5. 逐条回答选择题或输入自定义答案
6. 全部回答完毕 → 查看 Mermaid 逻辑图和骨架网页
```

### Excel 格式要求

| A 列 | B 列 |
|---|---|
| 需求编号 | 需求描述 |
| REQ-001 | 合同台账支持按合同编号、名称、签订日期筛选 |
| REQ-002 | 到期前 7 天自动发送提醒给经办人 |

## API 端点一览

| 方法 | 路径 | 用途 |
|---|---|---|
| POST | `/api/session/create` | 创建会话，返回 session_id |
| POST | `/api/session/{id}/upload-excel` | 上传 Excel（异步分析）|
| GET | `/api/session/{id}/status` | 查询会话状态 |
| GET | `/api/session/{id}/current-question` | 获取当前问题 |
| POST | `/api/session/{id}/answer` | 提交答案 |
| GET | `/api/session/{id}/outputs` | 获取产出 |
| GET | `/api/session/{id}/diagram/{i}` | 获取 Mermaid 图 |
| GET | `/api/session/{id}/skeleton/{i}` | 获取骨架文件 |

## 故障排除

### 后端 404

上传后页面报 404 → 确认前端 `api/index.js` 路径与后端一致。新版已统一为 `/api/session/...`。

### 上传超时

上传后长时间无响应 → 后端 `upload-excel` 已改为异步，立即返回。等待 5-10 秒后刷新页面，或查看后端命令行日志。

### AI 网关连接失败

```
connect ECONNREFUSED localhost:19090
```

→ 确认 WSL 中 VPN 已连接 + SSH 隧道已建立。
→ `netstat -ano | findstr :19090` 检查本地端口是否在监听。

### Mermaid 不渲染

→ 检查 `offline-deps/mermaid.min.js` 存在（3.4MB）。
→ 查看浏览器控制台有无 JS 错误。

## 文件结构

```
C:\Users\Administrator\1-smw\
├── backend\              # FastAPI + LangGraph 后端
│   └── app\              # 8 个 Python 模块
├── frontend\             # Vue 3 前端
│   ├── dist\             # 构建产物（开箱即用）
│   ├── src\              # 源代码（可修改后 npm run build）
│   └── node_modules\     # 离线依赖（含在内）
├── deploy\               # 部署脚本
├── offline-deps\         # 离线包
│   ├── python\           # 43 个 Windows wheels
│   └── mermaid.min.js    # v11
├── deploy-guide.md       # 本文件
└── README.md
```
