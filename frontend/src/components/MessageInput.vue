<script setup lang="ts">
import { ref } from "vue";

const props = defineProps<{
  loading: boolean;
}>();

const emit = defineEmits<{
  submit: [value: string];
}>();

const input = ref("");

function submitMessage() {
  const value = input.value.trim();
  if (!value || props.loading) {
    return;
  }

  emit("submit", value);
  input.value = "";
}

function onEnter(event: KeyboardEvent) {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    submitMessage();
  }
}
</script>

<template>
  <section class="input-card">
    <textarea
      v-model="input"
      class="message-input"
      rows="3"
      placeholder="输入你的问题，按 Enter 发送..."
      :disabled="loading"
      @keydown="onEnter"
    />
    <div class="actions">
      <button class="send-button" type="button" :disabled="loading" @click="submitMessage">
        {{ loading ? "发送中..." : "发送" }}
      </button>
    </div>
  </section>
</template>

<style scoped>
.input-card {
  border: 1px solid #e5e7eb;
  border-radius: 16px;
  background: #ffffff;
  box-shadow: 0 8px 20px rgba(15, 23, 42, 0.06);
  padding: 12px;
}

.message-input {
  width: 100%;
  border: none;
  resize: vertical;
  min-height: 70px;
  font-size: 15px;
  color: #1f2937;
  outline: none;
}

.actions {
  display: flex;
  justify-content: flex-end;
}

.send-button {
  border: none;
  border-radius: 999px;
  background: #0f766e;
  color: #ffffff;
  padding: 8px 18px;
  font-size: 14px;
  cursor: pointer;
}

.send-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}
</style>
