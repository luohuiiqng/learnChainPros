<script setup lang="ts">
import type { ChatMessage } from "../types/chat";

defineProps<{
  messages: ChatMessage[];
}>();

const isDev = import.meta.env.DEV;
</script>

<template>
  <div class="message-list" aria-live="polite">
    <div
      v-for="message in messages"
      :key="message.id"
      class="message-row"
      :class="message.role === 'user' ? 'is-user' : 'is-assistant'"
    >
      <article class="message-bubble">
        <header class="message-meta">
          <span>{{ message.role === "user" ? "你" : "助手" }}</span>
          <time>{{ new Date(message.timestamp).toLocaleTimeString() }}</time>
        </header>
        <p class="message-content">{{ message.content }}</p>
        <div
          v-if="message.error_code && message.role === 'assistant'"
          class="message-error-hint"
          :class="{ 'message-error-hint--prod': !isDev }"
          role="status"
        >
          <template v-if="isDev">
            <span class="message-error-code">{{ message.error_code }}</span>
            <span class="message-error-dev-hint">（开发环境显示稳定码）</span>
          </template>
          <template v-else>
            <span class="message-error-msg">暂时无法完成该请求，请稍后重试或换种说法。</span>
          </template>
        </div>
      </article>
    </div>
  </div>
</template>

<style scoped>
.message-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.message-row {
  display: flex;
}

.message-row.is-user {
  justify-content: flex-end;
}

.message-row.is-assistant {
  justify-content: flex-start;
}

.message-bubble {
  max-width: min(75ch, 80%);
  border-radius: 16px;
  padding: 10px 14px;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.08);
}

.message-row.is-user .message-bubble {
  background: linear-gradient(135deg, #ff8a5c, #ff6b6b);
  color: #fff;
}

.message-row.is-assistant .message-bubble {
  background: #ffffff;
  color: #1f2937;
  border: 1px solid #e5e7eb;
}

.message-row.is-assistant .message-bubble:has(.message-error-hint--prod) {
  border-color: #f59e0b;
  box-shadow: 0 4px 12px rgba(245, 158, 11, 0.2);
}

.message-meta {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  font-size: 12px;
  opacity: 0.8;
  margin-bottom: 6px;
}

.message-content {
  margin: 0;
  line-height: 1.6;
  word-break: break-word;
  white-space: pre-wrap;
}

.message-error-hint {
  margin: 10px 0 0;
  padding-top: 8px;
  border-top: 1px dashed #e5e7eb;
  font-size: 12px;
  line-height: 1.45;
}

.message-error-hint--prod {
  padding: 8px 10px;
  border-radius: 8px;
  background: #fffbeb;
  border: 1px solid #fcd34d;
}

.message-error-code {
  font-family: ui-monospace, monospace;
  font-size: 11px;
  color: #b45309;
}

.message-error-dev-hint {
  margin-left: 6px;
  font-size: 11px;
  color: #6b7280;
}

.message-error-msg {
  color: #92400e;
}
</style>
