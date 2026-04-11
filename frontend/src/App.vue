<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";

import ChatWindow from "./components/ChatWindow.vue";
import SessionDetailPage from "./components/SessionDetailPage.vue";

type RouteState =
  | { name: "home" }
  | { name: "session-detail"; sessionId: string };

const currentHash = ref(window.location.hash);

const route = computed<RouteState>(() => {
  const normalizedHash = currentHash.value || "#/";
  const sessionMatch = normalizedHash.match(/^#\/sessions\/(.+)$/);
  if (sessionMatch) {
    return {
      name: "session-detail",
      sessionId: decodeURIComponent(sessionMatch[1]),
    };
  }

  return { name: "home" };
});

function syncHash() {
  currentHash.value = window.location.hash;
}

function openSessionDetail(sessionId: string) {
  window.location.hash = `#/sessions/${encodeURIComponent(sessionId)}`;
}

function goHome() {
  window.location.hash = "#/";
}

onMounted(() => {
  if (!window.location.hash) {
    window.location.hash = "#/";
  }
  window.addEventListener("hashchange", syncHash);
});

onUnmounted(() => {
  window.removeEventListener("hashchange", syncHash);
});
</script>

<template>
  <SessionDetailPage
    v-if="route.name === 'session-detail'"
    :session-id="route.sessionId"
    @back="goHome"
  />
  <ChatWindow
    v-else
    @open-session-detail="openSessionDetail"
  />
</template>
