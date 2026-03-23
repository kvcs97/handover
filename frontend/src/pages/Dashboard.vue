<template>
  <div class="dashboard">

    <div class="dash-header">
      <div>
        <p class="dash-eyebrow">{{ today }}</p>
        <h1 class="dash-title">{{ greeting }}, <em>{{ firstName }}.</em></h1>
      </div>
      <button class="btn-primary" @click="$emit('navigate', 'handover')" v-if="!authStore.isViewer">
        + Neue Übergabe
      </button>
    </div>

    <div class="stats-row">
      <div class="stat-card" v-for="(s, i) in stats" :key="i" :style="`animation-delay:${i*0.07}s`">
        <div class="stat-val">{{ s.value }}</div>
        <div class="stat-label">{{ s.label }}</div>
        <div class="stat-trend" :class="s.trendClass" v-if="s.trend">{{ s.trend }}</div>
      </div>
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
            <tr v-for="h in handovers" :key="h.id">
              <td class="ref-cell">{{ h.referenz }}</td>
              <td>{{ h.carrier?.company_name || '—' }}</td>
              <td>{{ h.driver_name || '—' }}</td>
              <td><span class="chip" :class="h.status">{{ statusLabel(h.status) }}</span></td>
              <td class="time-cell">{{ formatTime(h.created_at) }}</td>
            </tr>
          </tbody>
        </table>

        <div class="empty-state" v-else>
          <span>📋</span>
          <p>Noch keine Übergaben heute</p>
        </div>
      </div>

      <!-- Schnellaktionen -->
      <div class="card card-actions">
        <h2 class="card-title">Schnellzugriff</h2>
        <div class="actions-list">
          <button class="action-btn primary" v-if="!authStore.isViewer" @click="$emit('navigate', 'handover')">
            <div class="action-icon-wrap primary">✦</div>
            <div class="action-text">
              <strong>Übergabe starten</strong>
              <span>Referenz eingeben & loslegen</span>
            </div>
            <span class="action-arrow">›</span>
          </button>
          <button class="action-btn" @click="$emit('navigate', 'archive')">
            <div class="action-icon-wrap">🗂</div>
            <div class="action-text">
              <strong>Archiv öffnen</strong>
              <span>Vergangene Übergaben</span>
            </div>
            <span class="action-arrow">›</span>
          </button>
          <button class="action-btn" v-if="authStore.isAdmin" @click="$emit('navigate', 'settings')">
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
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import api from '../api'

defineEmits(['navigate'])

const authStore = useAuthStore()
const handovers = ref([])
const loading   = ref(true)

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

const stats = computed(() => [
  { value: handovers.value.filter(h => h.status === 'archived').length, label: 'Abgeschlossen', trend: '↑ heute', trendClass: 'up' },
  { value: handovers.value.filter(h => h.status === 'pending').length,  label: 'Ausstehend',    trend: handovers.value.filter(h=>h.status==='pending').length > 0 ? '⚠ offen' : '', trendClass: 'warn' },
  { value: handovers.value.length, label: 'Total heute' },
  { value: new Set(handovers.value.map(h => h.carrier?.company_name).filter(Boolean)).size, label: 'Spediteure' },
])

function statusLabel(s) {
  return { pending: 'Ausstehend', printed: 'Gedruckt', signed: 'Unterschrieben', archived: 'Archiviert' }[s] || s
}
function formatTime(dt) {
  return dt ? new Date(dt).toLocaleTimeString('de-CH', { hour: '2-digit', minute: '2-digit' }) : '—'
}

onMounted(async () => {
  try { const res = await api.get('/handover/list'); handovers.value = res.data }
  catch (e) { console.error(e) }
  finally { loading.value = false }
})
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=DM+Sans:wght@300;400;500;600&display=swap');

.dashboard { padding: 40px 44px; font-family: 'DM Sans', sans-serif; }

/* ── Header ── */
.dash-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 32px; animation: fadeUp 0.4s ease both; }
.dash-eyebrow { font-size: 12px; font-weight: 500; letter-spacing: 0.05em; text-transform: uppercase; color: #98989f; margin-bottom: 6px; }
.dash-title { font-family: 'Instrument Serif', serif; font-size: 38px; font-weight: 400; color: #1c1c1e; letter-spacing: -1px; line-height: 1.05; }
.dash-title em { font-style: italic; color: #c0546a; }

.btn-primary {
  padding: 11px 22px; margin-top: 6px;
  background: linear-gradient(135deg, #e8849a, #c0546a);
  color: white; border: none; border-radius: 12px;
  font-family: 'DM Sans', sans-serif; font-size: 14px; font-weight: 500;
  cursor: pointer; box-shadow: 0 2px 12px rgba(192,84,106,0.3);
  transition: opacity 0.2s;
}
.btn-primary:hover { opacity: 0.9; }

/* ── Stats ── */
.stats-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 24px; }
.stat-card {
  background: white; border-radius: 14px; padding: 20px 18px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 0 0 1px rgba(0,0,0,0.04);
  animation: fadeUp 0.4s ease both;
}
.stat-val   { font-family: 'Instrument Serif', serif; font-size: 32px; font-weight: 400; color: #1c1c1e; letter-spacing: -1px; line-height: 1; margin-bottom: 4px; }
.stat-label { font-size: 12px; color: #98989f; }
.stat-trend { font-size: 11px; font-weight: 500; margin-top: 6px; }
.stat-trend.up   { color: #28a745; }
.stat-trend.warn { color: #c07800; }

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
.ho-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.ho-table th { text-align: left; font-size: 11px; font-weight: 600; letter-spacing: 0.05em; text-transform: uppercase; color: #98989f; padding: 0 10px 10px; border-bottom: 1px solid #f0f0f0; }
.ho-table td { padding: 12px 10px; border-bottom: 1px solid #f7f7f7; color: #1c1c1e; font-weight: 300; }
.ho-table tr:last-child td { border-bottom: none; }
.ho-table tr:hover td { background: #fafafa; }
.ref-cell  { font-family: monospace; font-size: 12px; font-weight: 700; color: #c0546a; }
.time-cell { color: #98989f; font-size: 12px; }

.chip { font-size: 11px; font-weight: 600; padding: 3px 10px; border-radius: 980px; }
.chip.archived { background: rgba(40,167,69,0.1);  color: #1a7a2e; }
.chip.pending  { background: rgba(255,149,0,0.1);  color: #c07800; }
.chip.printed  { background: rgba(192,84,106,0.1); color: #c0546a; }
.chip.signed   { background: rgba(90,200,250,0.1); color: #0077a8; }

.table-loading { display: flex; flex-direction: column; gap: 8px; }
.skeleton { height: 42px; background: linear-gradient(90deg, #f5f5f7 25%, #ebebeb 50%, #f5f5f7 75%); background-size: 200% 100%; border-radius: 8px; animation: shimmer 1.4s infinite; }
.empty-state { display: flex; flex-direction: column; align-items: center; gap: 8px; padding: 48px; color: #98989f; font-size: 14px; }
.empty-state span { font-size: 32px; }

/* ── Actions ── */
.card-actions { animation-delay: 0.2s; }
.actions-list { display: flex; flex-direction: column; gap: 8px; margin-top: 16px; }

.action-btn {
  display: flex; align-items: center; gap: 12px;
  padding: 14px; border-radius: 12px;
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
.action-text strong { display: block; font-size: 13px; font-weight: 500; color: #1c1c1e; }
.action-text span   { display: block; font-size: 11px; color: #98989f; margin-top: 1px; }
.action-arrow { color: rgba(0,0,0,0.2); font-size: 18px; }

@keyframes fadeUp  { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
@keyframes shimmer { to { background-position: -200% 0; } }
</style>
