<template>
  <!-- Update Banner — erscheint automatisch wenn Update verfügbar -->
  <div class="update-banner" v-if="updateInfo && !dismissed">
    <div class="update-content">
      <div class="update-icon">🆕</div>
      <div class="update-text">
        <strong>Version {{ updateInfo.version }} verfügbar</strong>
        <p v-if="updateInfo.body">{{ updateInfo.body }}</p>
      </div>
    </div>
    <div class="update-actions">
      <button class="btn-dismiss" @click="dismissed = true">Später</button>
      <button class="btn-install" @click="installUpdate" :disabled="installing">
        <span v-if="!installing">Jetzt installieren</span>
        <span v-else>
          <span class="spinner-sm"></span>
          {{ installProgress }}
        </span>
      </button>
    </div>
  </div>

  <!-- Installations-Overlay -->
  <div class="install-overlay" v-if="restarting">
    <div class="install-card">
      <div class="install-icon">⚡</div>
      <h3>Update wird installiert…</h3>
      <p>Die App startet automatisch neu.</p>
      <div class="progress-bar"><div class="progress-fill"></div></div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const updateInfo   = ref(null)
const dismissed    = ref(false)
const installing   = ref(false)
const restarting   = ref(false)
const installProgress = ref('Wird heruntergeladen…')

// Tauri API — nur verfügbar wenn in Tauri-Kontext
async function getTauriInvoke() {
  try {
    const { invoke } = await import('@tauri-apps/api/core')
    return invoke
  } catch {
    return null // Im Browser-Dev-Modus nicht verfügbar
  }
}

onMounted(async () => {
  // Kurz warten damit App erst vollständig lädt
  await new Promise(r => setTimeout(r, 3000))
  await checkForUpdates()
})

async function checkForUpdates() {
  const invoke = await getTauriInvoke()
  if (!invoke) return // Im Browser nichts tun

  try {
    const result = await invoke('check_for_updates')
    if (result.available) {
      updateInfo.value = result
    }
  } catch (e) {
    console.log('[Updater] Kein Update verfügbar oder offline:', e)
  }
}

async function installUpdate() {
  const invoke = await getTauriInvoke()
  if (!invoke) return

  installing.value = true
  try {
    installProgress.value = 'Wird heruntergeladen…'
    await invoke('install_update')
    restarting.value = true
    installProgress.value = 'Wird installiert…'
    // App startet automatisch neu nach Installation
  } catch (e) {
    console.error('Update fehlgeschlagen:', e)
    installing.value = false
    alert('Update fehlgeschlagen: ' + e)
  }
}
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500&display=swap');

.update-banner {
  position: fixed;
  bottom: 24px;
  right: 24px;
  background: white;
  border: 1px solid #e8e8ed;
  border-radius: 16px;
  padding: 16px 20px;
  box-shadow: 0 8px 40px rgba(0,0,0,0.12);
  z-index: 1000;
  max-width: 400px;
  font-family: 'DM Sans', sans-serif;
  animation: slideUp 0.35s cubic-bezier(0.175,0.885,0.32,1.275) both;
}

.update-content { display: flex; gap: 12px; align-items: flex-start; margin-bottom: 14px; }
.update-icon    { font-size: 24px; flex-shrink: 0; }
.update-text strong { font-size: 14px; font-weight: 600; color: #1d1d1f; display: block; }
.update-text p  { font-size: 13px; color: #6e6e73; margin-top: 3px; font-weight: 300; line-height: 1.4; }

.update-actions { display: flex; gap: 8px; justify-content: flex-end; }
.btn-dismiss { padding: 8px 16px; background: white; border: 1.5px solid #e8e8ed; border-radius: 9px; font-family: 'DM Sans', sans-serif; font-size: 13px; color: #6e6e73; cursor: pointer; transition: all 0.15s; }
.btn-dismiss:hover { background: #f5f5f7; }
.btn-install { padding: 8px 18px; background: #0071e3; color: white; border: none; border-radius: 9px; font-family: 'DM Sans', sans-serif; font-size: 13px; font-weight: 500; cursor: pointer; transition: background 0.2s; display: flex; align-items: center; gap: 6px; }
.btn-install:hover:not(:disabled) { background: #0077ed; }
.btn-install:disabled { opacity: 0.6; cursor: not-allowed; }

.install-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.5); backdrop-filter: blur(8px); z-index: 9999; display: flex; align-items: center; justify-content: center; }
.install-card { background: white; border-radius: 20px; padding: 48px; text-align: center; width: 320px; }
.install-icon { font-size: 48px; margin-bottom: 16px; }
.install-card h3 { font-size: 20px; font-weight: 600; color: #1d1d1f; margin-bottom: 8px; }
.install-card p  { font-size: 14px; color: #6e6e73; margin-bottom: 24px; }
.progress-bar  { height: 4px; background: #f0f0f0; border-radius: 2px; overflow: hidden; }
.progress-fill { height: 100%; background: #0071e3; border-radius: 2px; animation: progress 2s ease infinite; }

.spinner-sm { width: 13px; height: 13px; border: 2px solid rgba(255,255,255,0.3); border-top-color: white; border-radius: 50%; animation: spin 0.7s linear infinite; display: inline-block; }

@keyframes slideUp   { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
@keyframes spin      { to { transform: rotate(360deg); } }
@keyframes progress  { 0% { width: 0%; } 50% { width: 70%; } 100% { width: 100%; } }
</style>
