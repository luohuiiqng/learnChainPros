export type MessageRole = "user" | "assistant";

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: string;
  /** 逻辑失败时后端返回的稳定码（HTTP 仍可能为 200） */
  error_code?: string | null;
}

export interface ChatRequest {
  message: string;
  session_id?: string;
}

export interface ChatResponse {
  reply: string;
  session_id: string;
  timestamp: string;
  /** 与响应头 X-Request-ID 一致，便于排障 */
  request_id?: string | null;
  /**
   * 逻辑失败时的稳定码（与后端 ErrorCode 一致），HTTP 仍可能为 200；
   * 成功时为 null/undefined
   */
  error_code?: string | null;
}

export interface SessionResponse {
  session_id: string;
  created_at: string;
  updated_at: string;
  metadata: Record<string, unknown>;
}

export interface RuntimeSessionSnapshot {
  session_id: string;
  user_input: string;
  planner_result: Record<string, unknown> | null;
  workflow_result: Record<string, unknown> | null;
  tool_calls: Array<Record<string, unknown>>;
  model_calls: Array<Record<string, unknown>>;
  workflow_trace: Array<Record<string, unknown>>;
  final_output: string | null;
  errors: string[];
}

export interface TranscriptEntryResponse {
  type: string;
  user_input: string;
  final_output: string | null;
  success: boolean;
  timestamp: string;
  runtime_session: RuntimeSessionSnapshot;
}

export interface ErrorResponse {
  error: {
    code: string;
    message: string;
  };
}
