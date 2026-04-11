import type {
  ChatRequest,
  ChatResponse,
  ErrorResponse,
  SessionResponse,
  TranscriptEntryResponse,
} from "../types/chat";

const API_BASE_URL = "";

export async function sendChatMessage(payload: ChatRequest): Promise<ChatResponse> {
  return requestJson<ChatResponse>("/agent_api/chat", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
}

export async function fetchSessions(): Promise<SessionResponse[]> {
  return requestJson<SessionResponse[]>("/agent_api/sessions");
}

export async function fetchTranscript(sessionId: string): Promise<TranscriptEntryResponse[]> {
  return requestJson<TranscriptEntryResponse[]>(`/agent_api/sessions/${sessionId}/transcript`);
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, init);

  if (!response.ok) {
    const errorBody = (await response.json().catch(() => null)) as ErrorResponse | null;
    const message = errorBody?.error?.message ?? "请求失败，请稍后重试";
    throw new Error(message);
  }

  return (await response.json()) as T;
}
