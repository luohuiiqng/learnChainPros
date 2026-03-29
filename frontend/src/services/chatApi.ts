import type { ChatRequest, ChatResponse, ErrorResponse } from "../types/chat";

const API_BASE_URL = "";

export async function sendChatMessage(payload: ChatRequest): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE_URL}/agent_api/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    // Backend returns unified { error: { code, message } } contract.
    const errorBody = (await response.json().catch(() => null)) as ErrorResponse | null;
    const message = errorBody?.error?.message ?? "请求失败，请稍后重试";
    throw new Error(message);
  }

  return (await response.json()) as ChatResponse;
}


