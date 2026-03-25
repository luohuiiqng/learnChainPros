# LearnChainPros - 阶段1文本聊天 MVP

本项目实现了阶段1目标：
- Vue3 前端聊天界面（文本输入/展示）
- FastAPI 后端聊天接口（文本响应）
- 前后端通信与统一错误处理

## 目录结构

```text
learnChainPros/
  backend/
  frontend/
  docs/
```

## 1. 启动后端

```bash
cd backend
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

健康检查：`GET http://127.0.0.1:8000/health`

## 2. 启动前端

```bash
cd frontend
npm install
npm run dev
```

访问：`http://127.0.0.1:5173`

## 3. API 说明

### POST `/api/chat`

请求体：

```json
{
  "message": "你好",
  "session_id": "optional-uuid"
}
```

成功响应：

```json
{
  "reply": "你好，我收到了：你好",
  "session_id": "same-or-generated-uuid",
  "timestamp": "2026-03-25T10:00:00Z"
}
```

错误响应：

```json
{
  "error": {
    "code": "BAD_REQUEST",
    "message": "message不能为空"
  }
}
```

## 4. 阶段1已实现内容

- 文本消息发送与回复
- 发送中状态与错误提示
- 输入校验（空文本、长度限制）
- UI 美观与移动端可用（基础响应式）

## 5. 下一步建议（阶段2）

- 接入真实 LLM（LangChain + 模型提供方）
- 增加流式返回（SSE）
- 增加会话记忆和历史持久化
