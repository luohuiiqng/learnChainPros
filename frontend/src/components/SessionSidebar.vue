<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";

import { fetchSessions } from "../services/chatApi";
import type { SessionResponse } from "../types/chat";

const props = defineProps<{
  activeSessionId?: string;
  refreshKey: number;
}>();

const emit = defineEmits<{
  openSessionDetail: [sessionId: string];
}>();

const sessions = ref<SessionResponse[]>([]);
const sessionsLoading = ref(false);
const sessionsError = ref("");
const sessionSearch = ref("");

const filteredSessions = computed(() => {
  const searchValue = sessionSearch.value.trim().toLowerCase();
  if (!searchValue) {
    return sessions.value;
  }

  return sessions.value.filter((session) => {
    const haystack = [
      session.session_id,
      session.created_at,
      session.updated_at,
      JSON.stringify(session.metadata ?? {}),
    ]
      .join(" ")
      .toLowerCase();
    return haystack.includes(searchValue);
  });
});

const sessionStats = computed(() => [
  { label: "会话总数", value: String(sessions.value.length) },
  { label: "可见会话", value: String(filteredSessions.value.length) },
  { label: "当前会话", value: props.activeSessionId ? props.activeSessionId.slice(0, 8) : "-" },
]);

onMounted(async () => {
  await loadSessions();
});

watch(
  () => props.refreshKey,
  async () => {
    await loadSessions();
  },
);

async function loadSessions() {
  sessionsLoading.value = true;
  sessionsError.value = "";

  try {
    sessions.value = await fetchSessions();
  } catch (error) {
    sessionsError.value = error instanceof Error ? error.message : "会话列表加载失败";
  } finally {
    sessionsLoading.value = false;
  }
}

function resetSearch() {
  sessionSearch.value = "";
}

function formatTime(value: string) {
  return new Date(value).toLocaleString();
}
</script>

<template>
  <aside class="sidebar-shell">
    <section class="sidebar-panel">
      <header class="panel-header">
        <div>
          <p class="panel-eyebrow">Runtime Console</p>
          <h2>会话记录</h2>
        </div>
        <div class="panel-actions">
          <span class="panel-count">{{ sessions.length }} 条</span>
          <button type="button" class="refresh-button" @click="loadSessions">
            刷新
          </button>
        </div>
      </header>

      <section class="stats-grid">
        <article
          v-for="stat in sessionStats"
          :key="stat.label"
          class="stat-card"
        >
          <span>{{ stat.label }}</span>
          <strong>{{ stat.value }}</strong>
        </article>
      </section>

      <section class="session-filters">
        <label class="filter-field">
          <span>搜索会话</span>
          <input
            v-model="sessionSearch"
            type="text"
            class="filter-input"
            placeholder="搜索 session_id 或 metadata"
          />
        </label>
        <div class="session-filter-meta">
          <span class="session-sort-hint">按最近更新时间倒序</span>
          <button type="button" class="ghost-button" @click="resetSearch">
            清空搜索
          </button>
        </div>
      </section>

      <p v-if="sessionsError" class="panel-error">{{ sessionsError }}</p>
      <p v-else-if="sessionsLoading" class="panel-hint">正在同步会话列表...</p>
      <p v-else-if="sessions.length === 0" class="panel-hint">还没有会话记录，先发一条消息试试。</p>
      <p v-else-if="filteredSessions.length === 0" class="panel-hint">当前搜索条件下没有匹配到会话。</p>

      <div v-else class="session-list">
        <button
          v-for="session in filteredSessions"
          :key="session.session_id"
          type="button"
          class="session-card"
          :class="{ 'is-active': session.session_id === props.activeSessionId }"
          @click="emit('openSessionDetail', session.session_id)"
        >
          <div class="session-card-top">
            <span class="session-chip">Session</span>
            <span v-if="session.session_id === props.activeSessionId" class="active-chip">当前</span>
          </div>
          <strong>{{ session.session_id.slice(0, 8) }}</strong>
          <span class="session-time">更新于 {{ formatTime(session.updated_at) }}</span>
          <span class="session-meta">创建于 {{ formatTime(session.created_at) }}</span>
          <span class="detail-link">查看完整调试详情</span>
        </button>
      </div>
    </section>
  </aside>
</template>

<style scoped>
.sidebar-shell {
  display: grid;
  min-height: 100%;
  height: 100%;
}

.sidebar-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-height: 0;
  border-radius: 24px;
  padding: 18px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(255, 248, 240, 0.92)),
    linear-gradient(135deg, rgba(251, 191, 36, 0.08), rgba(14, 165, 233, 0.08));
  border: 1px solid rgba(148, 163, 184, 0.2);
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.08);
  overflow: hidden;
}

.panel-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.panel-eyebrow {
  margin: 0 0 4px;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: #b45309;
}

.panel-header h2 {
  margin: 0;
  font-size: 20px;
  color: #111827;
}

.panel-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.panel-count {
  align-self: center;
  border-radius: 999px;
  padding: 6px 10px;
  font-size: 12px;
  color: #7c2d12;
  background: rgba(251, 191, 36, 0.16);
}

.refresh-button,
.ghost-button {
  border-radius: 999px;
  padding: 8px 12px;
  font-size: 12px;
  cursor: pointer;
}

.refresh-button {
  border: none;
  color: #fff;
  background: linear-gradient(135deg, #d97706, #0f766e);
}

.ghost-button {
  border: 1px solid rgba(148, 163, 184, 0.22);
  color: #334155;
  background: rgba(255, 255, 255, 0.85);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.stat-card {
  display: grid;
  gap: 8px;
  border-radius: 16px;
  padding: 14px;
  background: linear-gradient(180deg, rgba(255, 247, 237, 0.96), rgba(255, 255, 255, 0.96));
  border: 1px solid rgba(251, 191, 36, 0.18);
}

.stat-card span {
  font-size: 12px;
  color: #92400e;
}

.stat-card strong {
  font-size: 22px;
  color: #111827;
}

.session-filters {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 10px;
  align-items: end;
}

.filter-field {
  display: grid;
  gap: 8px;
}

.filter-field span,
.session-sort-hint {
  font-size: 12px;
  color: #92400e;
}

.filter-input {
  width: 100%;
  border: 1px solid rgba(148, 163, 184, 0.22);
  border-radius: 14px;
  padding: 10px 12px;
  background: rgba(255, 255, 255, 0.95);
  color: #0f172a;
  outline: none;
}

.session-filter-meta {
  display: flex;
  align-items: center;
  gap: 10px;
}

.session-list {
  display: grid;
  gap: 12px;
  min-height: 0;
  overflow: auto;
  padding-right: 4px;
}

.panel-hint,
.panel-error {
  margin: 0;
  padding: 12px 14px;
  border-radius: 14px;
  font-size: 14px;
}

.panel-hint {
  color: #475569;
  background: rgba(241, 245, 249, 0.8);
}

.panel-error {
  color: #b91c1c;
  background: rgba(254, 226, 226, 0.85);
}

.session-card {
  text-align: left;
  display: grid;
  gap: 6px;
  border: 1px solid rgba(148, 163, 184, 0.16);
  border-radius: 18px;
  padding: 14px;
  background: rgba(255, 255, 255, 0.9);
  cursor: pointer;
  transition: transform 180ms ease, box-shadow 180ms ease, border-color 180ms ease;
}

.session-card:hover,
.session-card.is-active {
  transform: translateY(-1px);
  border-color: rgba(217, 119, 6, 0.45);
  box-shadow: 0 12px 24px rgba(217, 119, 6, 0.12);
}

.session-card-top {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  align-items: center;
}

.session-chip,
.active-chip {
  width: fit-content;
  border-radius: 999px;
  padding: 4px 8px;
  font-size: 11px;
}

.session-chip {
  color: #92400e;
  background: rgba(251, 191, 36, 0.18);
}

.active-chip {
  color: #0f766e;
  background: rgba(14, 165, 233, 0.12);
}

.session-card strong {
  font-size: 16px;
  color: #111827;
}

.session-time,
.session-meta {
  font-size: 13px;
  color: #64748b;
}

.detail-link {
  margin-top: 4px;
  font-size: 12px;
  color: #0f766e;
}

@media (max-width: 720px) {
  .stats-grid,
  .session-filters {
    grid-template-columns: 1fr;
  }

  .session-filter-meta {
    justify-content: space-between;
  }

  .panel-actions {
    align-items: flex-end;
    flex-direction: column;
  }
}
</style>
