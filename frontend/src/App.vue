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

    <!-- Inaktivitäts-Warnung (Auto-Logout) -->
    <div class="idle-overlay" v-if="idleWarning && authStore.isLoggedIn">
      <div class="idle-card">
        <div class="idle-icon">🔒</div>
        <h3>Sitzung läuft bald ab</h3>
        <p>Wegen Inaktivität wirst du in <strong>{{ remainingSeconds }}s</strong> automatisch abgemeldet.</p>
        <button class="btn-stay" @click="stayLoggedIn">Angemeldet bleiben</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useAuthStore } from './stores/auth'
import { useAutoLogout } from './composables/useAutoLogout'
import SetupWizard   from './pages/SetupWizard.vue'
import LoginPage     from './pages/Login.vue'
import AppShell      from './components/layout/AppShell.vue'
import UpdateChecker from './components/UpdateChecker.vue'
import api           from './api'

const authStore = useAuthStore()
const loading   = ref(true)
const setupDone = ref(false)

// Auto-Logout — 30 Min Inaktivitaet, 60s Warnung davor
const { warning: idleWarning, msRemaining, reset: resetIdle } = useAutoLogout(
  () => {
    if (authStore.isLoggedIn) {
      authStore.logout()
    }
  },
  { timeoutMs: 30 * 60 * 1000, warnBeforeMs: 60 * 1000 }
)

const remainingSeconds = computed(() => Math.ceil(msRemaining.value / 1000))

function stayLoggedIn() {
  resetIdle()
}

// Bei Login/Logout Timer neu starten
watch(() => authStore.isLoggedIn, (loggedIn) => {
  if (loggedIn) resetIdle()
})

onMounted(async () => {
  try {
    const res = await api.get('/settings/is-setup-done')
    setupDone.value = res.data.setup_done
    await authStore.restore()
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

/* Inaktivitaets-Warnung */
.idle-overlay {
  position: fixed; inset: 0;
  background: rgba(0, 0, 0, 0.55);
  backdrop-filter: blur(6px);
  z-index: 9998;
  display: flex; align-items: center; justify-content: center;
  animation: fadeIn 0.2s ease both;
}
.idle-card {
  background: white;
  border-radius: 20px;
  padding: 40px 44px;
  text-align: center;
  max-width: 380px;
  width: calc(100% - 48px);
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  font-family: 'DM Sans', sans-serif;
}
.idle-icon { font-size: 42px; margin-bottom: 14px; }
.idle-card h3 {
  font-family: 'Instrument Serif', serif;
  font-size: 24px; font-weight: 400; color: #1d1d1f;
  letter-spacing: -0.5px; margin-bottom: 8px;
}
.idle-card p {
  font-size: 14px; color: #6e6e73;
  margin-bottom: 24px; line-height: 1.5;
}
.idle-card strong { color: #c0546a; font-weight: 600; }
.btn-stay {
  padding: 12px 28px;
  background: linear-gradient(135deg, #e8849a, #c0546a);
  color: white; border: none; border-radius: 12px;
  font-family: 'DM Sans', sans-serif;
  font-size: 14px; font-weight: 500;
  cursor: pointer; transition: opacity 0.2s;
  box-shadow: 0 4px 14px rgba(192, 84, 106, 0.3);
}
.btn-stay:hover { opacity: 0.9; }

@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
</style>
