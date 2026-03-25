<script setup lang="ts">
import type { ChatMessage } from "../types/chat";

defineProps<{
  messages: ChatMessage[];
}>();
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
</style>
