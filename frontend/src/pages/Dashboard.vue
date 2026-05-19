<template>
  <div class="dashboard">

    <div class="dash-header">
      <div>
        <p class="dash-eyebrow">{{ today }}</p>
        <h1 class="dash-title">{{ greeting }}, <em>{{ firstName }}.</em></h1>
      </div>
      <button class="btn-primary" @click="navigate('handover')" v-if="!authStore.isViewer">
        + Neue Übergabe
      </button>
    </div>

    <!-- Offene Übergaben (nicht unterschrieben) -->
    <div class="card card-warn" v-if="openHandovers.length && !authStore.isViewer">
      <div class="card-header">
        <h2 class="card-title">Offene Übergaben</h2>
        <span class="card-pill warn">{{ openHandovers.length }} offen</span>
      </div>
      <table class="ho-table">
        <thead>
          <tr><th>Referenz</th><th>Spediteur</th><th>Status</th><th>Erstellt</th><th></th></tr>
        </thead>
        <tbody>
          <tr v-for="h in openHandovers" :key="h.id" class="open-row" @click="resumeHandover(h)">
            <td class="ref-cell">{{ h.referenz }}</td>
            <td>{{ h.carrier?.company_name || '—' }}</td>
            <td><span class="chip" :class="h.status">{{ statusLabel(h.status) }}</span></td>
            <td class="time-cell">{{ formatDate(h.created_at) }}</td>
            <td class="action-cell">
              <button class="btn-resume" @click.stop="resumeHandover(h)" title="Weiterführen">✍️</button>
              <button class="btn-cancel" @click.stop="confirmCancel(h)" title="Abbrechen">✕</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="content-grid">

      <!-- Letzte Übergaben -->
      <div class="card">
        <div class="card-header">
          <h2 class="card-title">Letzte Übergaben</h2>
          <span class="card-pill">Heute</span>
        </div>

        <div class="table-loading" v-if="loading">
          <div class="skeleton" v-for="i in 5" :key="i"></div>
        </div>

        <table class="ho-table" v-else-if="handovers.length">
          <thead>
            <tr>
              <th>Referenz</th>
              <th>Spediteur</th>
              <th>Fahrer</th>
              <th>Status</th>
              <th>Zeit</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="h in visibleHandovers" :key="h.id">
              <td class="ref-cell">{{ h.referenz }}</td>
              <td>{{ h.carrier?.company_name || '—' }}</td>
              <td>{{ h.driver_name || '—' }}</td>
              <td><span class="chip" :class="h.status">{{ statusLabel(h.status) }}</span></td>
              <td class="time-cell">{{ formatTime(h.created_at) }}</td>
            </tr>
          </tbody>
        </table>

        <div class="show-all-wrap" v-if="handovers.length > LIMIT && !showAll">
          <button class="btn-show-all" @click="showAll = true">
            Alle {{ handovers.length }} anzeigen ↓
          </button>
        </div>

        <div class="empty-state" v-if="!loading && !handovers.length">
          <span>📋</span>
          <p>Noch keine Übergaben heute</p>
        </div>
      </div>

      <!-- Schnellaktionen -->
      <div class="card card-actions">
        <h2 class="card-title">Schnellzugriff</h2>
        <div class="actions-list">
          <button class="action-btn primary" v-if="!authStore.isViewer" @click="navigate('handover')">
            <div class="action-icon-wrap primary">✦</div>
            <div class="action-text">
              <strong>Übergabe starten</strong>
              <span>Referenz eingeben & loslegen</span>
            </div>
            <span class="action-arrow">›</span>
          </button>
          <button class="action-btn" @click="navigate('archive')">
            <div class="action-icon-wrap">🗂</div>
            <div class="action-text">
              <strong>Archiv öffnen</strong>
              <span>Vergangene Übergaben</span>
            </div>
            <span class="action-arrow">›</span>
          </button>
          <button class="action-btn" v-if="authStore.isAdmin" @click="navigate('settings')">
            <div class="action-icon-wrap">⚙️</div>
            <div class="action-text">
              <strong>Einstellungen</strong>
              <span>Drucker & Firmendaten</span>
            </div>
            <span class="action-arrow">›</span>
          </button>
        </div>
      </div>

    </div>

    <!-- Cancel Bestätigung -->
    <div class="modal-overlay" v-if="cancelTarget" @click.self="cancelTarget = null">
      <div class="confirm-modal">
        <h3>Übergabe abbrechen?</h3>
        <p>Referenz <strong>{{ cancelTarget.referenz }}</strong> wird als abgebrochen markiert.</p>
        <div class="confirm-actions">
          <button class="btn-conf-cancel" @click="cancelTarget = null">Nein</button>
          <button class="btn-conf-ok" @click="doCancel" :disabled="cancelling">
            <span v-if="!cancelling">Ja, abbrechen</span>
            <span v-else class="spinner-sm"></span>
          </button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import api from '../api'

const emit = defineEmits(['navigate'])

const authStore = useAuthStore()
const handovers     = ref([])
const openHandovers = ref([])
const loading       = ref(true)
const showAll       = ref(false)
const LIMIT         = 10
const cancelTarget  = ref(null)
const cancelling    = ref(false)

const visibleHandovers = computed(() => showAll.value ? handovers.value : handovers.value.slice(0, LIMIT))

const today = computed(() => new Date().toLocaleDateString('de-CH', {
  weekday: 'long', day: 'numeric', month: 'long', year: 'numeric'
}))

const greeting = computed(() => {
  const h = new Date().getHours()
  if (h < 12) return 'Guten Morgen'
  if (h < 18) return 'Guten Tag'
  return 'Guten Abend'
})

const firstName = computed(() => authStore.userName?.split(' ')[0] || authStore.userName)

function statusLabel(s) {
  return { pending: 'Ausstehend', printed: 'Gedruckt', signed: 'Unterschrieben', archived: 'Archiviert' }[s] || s
}
function formatTime(dt) {
  return dt ? new Date(dt).toLocaleTimeString('de-CH', { hour: '2-digit', minute: '2-digit' }) : '—'
}
function formatDate(dt) {
  if (!dt) return '—'
  return new Date(dt).toLocaleDateString('de-CH', { day: '2-digit', month: '2-digit', year: 'numeric' })
    + ' ' + new Date(dt).toLocaleTimeString('de-CH', { hour: '2-digit', minute: '2-digit' })
}

function navigate(page) {
  emit('navigate', { page })
}

function resumeHandover(h) {
  emit('navigate', { page: 'handover', resumeId: h.id })
}

function confirmCancel(h) {
  cancelTarget.value = h
}

async function doCancel() {
  if (!cancelTarget.value) return
  cancelling.value = true
  try {
    await api.patch(`/handover/${cancelTarget.value.id}/cancel`)
    openHandovers.value = openHandovers.value.filter(h => h.id !== cancelTarget.value.id)
    cancelTarget.value = null
  } catch (e) {
    alert(e.response?.data?.detail || 'Fehler beim Abbrechen')
  } finally {
    cancelling.value = false
  }
}

onMounted(async () => {
  try {
    const [list, open] = await Promise.all([
      api.get('/handover/list'),
      api.get('/handover/open'),
    ])
    handovers.value     = list.data
    openHandovers.value = open.data
  } catch (e) { console.error(e) }
  finally { loading.value = false }
})
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=DM+Sans:wght@300;400;500;600&display=swap');

.dashboard { padding: 24px 32px; font-family: 'DM Sans', sans-serif; }

/* ── Header ── */
.dash-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 32px; animation: fadeUp 0.4s ease both; }
.dash-eyebrow { font-size: 12px; font-weight: 500; letter-spacing: 0.05em; text-transform: uppercase; color: #98989f; margin-bottom: 6px; }
.dash-title { font-family: 'Instrument Serif', serif; font-size: 38px; font-weight: 400; color: #1c1c1e; letter-spacing: -1px; line-height: 1.05; }
.dash-title em { font-style: italic; color: #c0546a; }

.btn-primary {
  padding: 12px 24px; margin-top: 6px;
  min-height: 44px;
  background: linear-gradient(135deg, #e8849a, #c0546a);
  color: white; border: none; border-radius: 12px;
  font-family: 'DM Sans', sans-serif; font-size: 14px; font-weight: 500;
  cursor: pointer; box-shadow: 0 2px 12px rgba(192,84,106,0.3);
  transition: opacity 0.2s;
  display: inline-flex; align-items: center;
}
.btn-primary:hover { opacity: 0.9; }

/* ── Grid ── */
.content-grid { display: grid; grid-template-columns: 1fr 280px; gap: 14px; }

.card {
  background: white; border-radius: 14px; padding: 24px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 0 0 1px rgba(0,0,0,0.04);
  animation: fadeUp 0.4s ease 0.15s both;
}

.card-header { display: flex; align-items: center; gap: 12px; margin-bottom: 20px; }
.card-title  { font-family: 'Instrument Serif', serif; font-size: 20px; font-weight: 400; color: #1c1c1e; letter-spacing: -0.3px; flex: 1; }
.card-pill   { font-size: 11px; font-weight: 600; color: #c0546a; background: rgba(192,84,106,0.08); padding: 3px 10px; border-radius: 980px; }

/* ── Table ── */
.ho-table { width: 100%; border-collapse: collapse; font-size: 14px; }
.ho-table th { text-align: left; font-size: 12px; font-weight: 600; letter-spacing: 0.05em; text-transform: uppercase; color: #98989f; padding: 0 12px 12px; border-bottom: 1px solid #f0f0f0; }
.ho-table td { padding: 14px 12px; border-bottom: 1px solid #f7f7f7; color: #1c1c1e; font-weight: 300; }
.ho-table tr:last-child td { border-bottom: none; }
.ho-table tr:hover td { background: #fafafa; }
.ref-cell  { font-family: monospace; font-size: 12px; font-weight: 700; color: #c0546a; }
.time-cell { color: #98989f; font-size: 12px; }

.chip { font-size: 12px; font-weight: 600; padding: 4px 10px; border-radius: 980px; }
.chip.archived { background: rgba(40,167,69,0.1);  color: #1a7a2e; }
.chip.pending  { background: rgba(255,149,0,0.1);  color: #c07800; }
.chip.printed  { background: rgba(192,84,106,0.1); color: #c0546a; }
.chip.signed   { background: rgba(90,200,250,0.1); color: #0077a8; }

/* ── Offene Übergaben Aktionen ── */
.open-row { cursor: pointer; }
.open-row:hover td { background: rgba(192,84,106,0.03); }
.action-cell { white-space: nowrap; }
.btn-resume, .btn-cancel {
  border: none; border-radius: 8px; width: 34px; height: 34px;
  cursor: pointer; font-size: 14px;
  display: inline-flex; align-items: center; justify-content: center;
  transition: all 0.15s; margin-left: 4px;
}
.btn-resume { background: rgba(192,84,106,0.08); color: #c0546a; }
.btn-resume:hover { background: rgba(192,84,106,0.18); }
.btn-cancel { background: rgba(255,59,48,0.07); color: #ff3b30; }
.btn-cancel:hover { background: rgba(255,59,48,0.15); }

/* ── Show all ── */
.show-all-wrap { padding: 12px; text-align: center; border-top: 1px solid #f0f0f0; margin-top: 4px; }
.btn-show-all {
  background: none; border: 1.5px solid #e8e8ed; border-radius: 10px;
  padding: 8px 20px; font-size: 13px; color: #6e6e73;
  cursor: pointer; font-family: 'DM Sans', sans-serif; transition: all 0.15s;
}
.btn-show-all:hover { border-color: #c0546a; color: #c0546a; }

.table-loading { display: flex; flex-direction: column; gap: 8px; }
.skeleton { height: 42px; background: linear-gradient(90deg, #f5f5f7 25%, #ebebeb 50%, #f5f5f7 75%); background-size: 200% 100%; border-radius: 8px; animation: shimmer 1.4s infinite; }
.empty-state { display: flex; flex-direction: column; align-items: center; gap: 8px; padding: 48px; color: #98989f; font-size: 14px; }
.empty-state span { font-size: 32px; }

/* ── Actions ── */
.card-warn { border: 1.5px solid rgba(255,149,0,0.2); margin-bottom: 14px; animation-delay: 0.05s; }
.card-pill.warn { color: #c07800; background: rgba(255,149,0,0.1); }
.card-actions { animation-delay: 0.2s; }
.actions-list { display: flex; flex-direction: column; gap: 8px; margin-top: 16px; }

.action-btn {
  display: flex; align-items: center; gap: 12px;
  padding: 16px; min-height: 56px;
  border-radius: 12px;
  border: 1.5px solid #f0f0f0; background: #fafafa;
  cursor: pointer; text-align: left; width: 100%;
  font-family: 'DM Sans', sans-serif;
  transition: all 0.15s;
}
.action-btn:hover { border-color: #e0e0e0; background: white; transform: translateY(-1px); box-shadow: 0 4px 12px rgba(0,0,0,0.06); }
.action-btn.primary { background: linear-gradient(135deg, #f2a7b8, #c0546a); border-color: transparent; }
.action-btn.primary:hover { opacity: 0.92; transform: translateY(-1px); box-shadow: 0 4px 16px rgba(192,84,106,0.3); }
.action-btn.primary strong,
.action-btn.primary span,
.action-btn.primary .action-arrow { color: white !important; }

.action-icon-wrap { width: 34px; height: 34px; background: rgba(255,255,255,0.2); border-radius: 9px; display: flex; align-items: center; justify-content: center; font-size: 14px; flex-shrink: 0; }
.action-btn:not(.primary) .action-icon-wrap { background: #f0f0f0; }
.action-text { flex: 1; }
.action-text strong { display: block; font-size: 14px; font-weight: 500; color: #1c1c1e; }
.action-text span   { display: block; font-size: 12px; color: #98989f; margin-top: 2px; }
.action-arrow { color: rgba(0,0,0,0.2); font-size: 18px; }

/* ── Cancel Modal ── */
.modal-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.45);
  backdrop-filter: blur(4px); z-index: 500;
  display: flex; align-items: center; justify-content: center;
}
.confirm-modal {
  background: white; border-radius: 16px; padding: 32px 36px;
  max-width: 380px; width: calc(100% - 48px);
  box-shadow: 0 16px 48px rgba(0,0,0,0.2);
  font-family: 'DM Sans', sans-serif; text-align: center;
}
.confirm-modal h3 {
  font-family: 'Instrument Serif', serif; font-size: 22px; font-weight: 400;
  color: #1c1c1e; letter-spacing: -0.3px; margin-bottom: 10px;
}
.confirm-modal p { font-size: 14px; color: #6e6e73; margin-bottom: 24px; line-height: 1.5; }
.confirm-modal strong { color: #1c1c1e; font-weight: 600; }
.confirm-actions { display: flex; gap: 10px; justify-content: center; }
.btn-conf-cancel {
  padding: 11px 22px; min-height: 44px; border-radius: 10px;
  background: white; border: 1.5px solid #e8e8ed;
  font-family: 'DM Sans', sans-serif; font-size: 14px; font-weight: 500;
  color: #6e6e73; cursor: pointer; transition: all 0.15s;
}
.btn-conf-cancel:hover { background: #f5f5f7; }
.btn-conf-ok {
  padding: 11px 22px; min-height: 44px; border-radius: 10px;
  background: #ff3b30; border: none;
  font-family: 'DM Sans', sans-serif; font-size: 14px; font-weight: 500;
  color: white; cursor: pointer; transition: opacity 0.2s;
  display: inline-flex; align-items: center; justify-content: center; gap: 8px;
}
.btn-conf-ok:hover { opacity: 0.88; }
.btn-conf-ok:disabled { opacity: 0.45; cursor: not-allowed; }
.spinner-sm { width: 16px; height: 16px; border: 2px solid rgba(255,255,255,0.3); border-top-color: white; border-radius: 50%; animation: spin 0.7s linear infinite; display: inline-block; }

@keyframes fadeUp  { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
@keyframes shimmer { to { background-position: -200% 0; } }
@keyframes spin    { to { transform: rotate(360deg); } }
</style>
