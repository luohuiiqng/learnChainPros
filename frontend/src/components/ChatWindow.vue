<script setup lang="ts">
import { nextTick, ref } from "vue";

import MessageInput from "./MessageInput.vue";
import MessageList from "./MessageList.vue";
import { sendChatMessage } from "../services/chatApi";
import type { ChatMessage } from "../types/chat";

function createMessageId() {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }

  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

// Keep a local in-memory message list for Stage 1 (no persistence yet).
const messages = ref<ChatMessage[]>([
  {
    id: createMessageId(),
    role: "assistant",
    content: "你好，我是你的助手。请告诉我你想做什么。",
    timestamp: new Date().toISOString(),
  },
]);

const loading = ref(false);
const errorText = ref("");
const sessionId = ref<string | undefined>(undefined);
const listWrapper = ref<HTMLElement | null>(null);

// Centralized append function keeps message structure consistent.
function appendMessage(role: ChatMessage["role"], content: string, timestamp = new Date().toISOString()) {
  messages.value.push({
    id: createMessageId(),
    role,
    content,
    timestamp,
  });
}

// Ensure newest message stays visible after each send/receive cycle.
async function scrollToBottom() {
  await nextTick();
  if (listWrapper.value) {
    listWrapper.value.scrollTop = listWrapper.value.scrollHeight;
  }
}

// Main send flow: validate -> optimistic user message -> request -> render assistant message.
async function handleSend(text: string) {
  if (!text.trim()) {
    errorText.value = "请输入消息后再发送";
    return;
  }

  if (text.length > 2000) {
    errorText.value = "消息长度不能超过 2000 个字符";
    return;
  }

  errorText.value = "";
  appendMessage("user", text);
  await scrollToBottom();

  loading.value = true;
  try {
    const result = await sendChatMessage({ message: text, session_id: sessionId.value });
    sessionId.value = result.session_id;
    appendMessage("assistant", result.reply, result.timestamp);
  } catch (error) {
    const message = error instanceof Error ? error.message : "网络连接失败，请稍后重试";
    errorText.value = message;
  } finally {
    loading.value = false;
    await scrollToBottom();
  }
}
</script>

<template>
  <main class="chat-shell">
    <section class="chat-panel">
      <header class="chat-header">
        <h1>LearnChain Chat</h1>
        <p>阶段1：文本对话 MVP</p>
      </header>

      <div ref="listWrapper" class="chat-history">
        <MessageList :messages="messages" />
      </div>

      <p v-if="errorText" class="error-banner">{{ errorText }}</p>

      <MessageInput :loading="loading" @submit="handleSend" />
    </section>
  </main>
</template>

<style scoped>
.chat-shell {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 24px;
  background: radial-gradient(circle at top left, #fef3c7, #e0f2fe 60%, #f8fafc);
}

.chat-panel {
  width: min(900px, 100%);
  display: grid;
  grid-template-rows: auto 1fr auto auto;
  gap: 14px;
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(8px);
  border-radius: 20px;
  padding: 16px;
  border: 1px solid rgba(255, 255, 255, 0.9);
  box-shadow: 0 15px 40px rgba(15, 23, 42, 0.15);
  min-height: 78vh;
}

.chat-header h1 {
  margin: 0;
  font-size: 26px;
  color: #0f172a;
}

.chat-header p {
  margin: 6px 0 0;
  color: #475569;
}

.chat-history {
  overflow: auto;
  padding-right: 4px;
}

.error-banner {
  margin: 0;
  color: #b91c1c;
  background: #fee2e2;
  border: 1px solid #fecaca;
  border-radius: 10px;
  padding: 8px 10px;
  font-size: 14px;
}

@media (max-width: 768px) {
  .chat-shell {
    padding: 10px;
  }

  .chat-panel {
    min-height: 90vh;
    border-radius: 14px;
    padding: 12px;
  }

  .chat-header h1 {
    font-size: 22px;
  }
}
</style>

