<template>
  <div id="app">
    <!-- Splash während Prüfung -->
    <div v-if="loading" class="splash">
      <span class="splash-logo">HandOver</span>
    </div>

    <!-- Setup Wizard (nur beim ersten Start) -->
    <SetupWizard v-else-if="!setupDone" @setup-complete="onSetupComplete" />

    <!-- Login -->
    <LoginPage v-else-if="!authStore.isLoggedIn" />

    <!-- Hauptanwendung -->
    <AppShell v-else />

    <!-- Update Checker — läuft immer im Hintergrund -->
    <UpdateChecker v-if="authStore.isLoggedIn" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from './stores/auth'
import SetupWizard   from './pages/SetupWizard.vue'
import LoginPage     from './pages/Login.vue'
import AppShell      from './components/layout/AppShell.vue'
import UpdateChecker from './components/UpdateChecker.vue'
import api           from './api'

const authStore = useAuthStore()
const loading   = ref(true)
const setupDone = ref(false)

onMounted(async () => {
  try {
    const res = await api.get('/settings/is-setup-done')
    setupDone.value = res.data.setup_done
    authStore.restore()
  } catch (e) {
    console.error('Backend nicht erreichbar', e)
  } finally {
    loading.value = false
  }
})

function onSetupComplete() {
  setupDone.value = true
}
</script>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: 'DM Sans', -apple-system, sans-serif; background: #f5f5f7; }
#app { height: 100vh; }

.splash {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #1d1d1f;
}
.splash-logo {
  font-size: 32px;
  font-weight: 300;
  color: white;
  letter-spacing: -1px;
}
</style>
