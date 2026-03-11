<template>
  <div class="dashboard">

    <!-- Header -->
    <div class="dash-header">
      <div>
        <h1 class="dash-title">Dashboard</h1>
        <p class="dash-sub">{{ greeting }}, {{ authStore.userName }}</p>
      </div>
      <div class="dash-date">{{ today }}</div>
    </div>

    <!-- Stats Row -->
    <div class="stats-row">
      <div class="stat-card" v-for="(s, i) in stats" :key="i" :style="`animation-delay:${i*0.08}s`">
        <div class="stat-icon">{{ s.icon }}</div>
        <div class="stat-body">
          <div class="stat-value">{{ s.value }}</div>
          <div class="stat-label">{{ s.label }}</div>
        </div>
        <div class="stat-trend" :class="s.up ? 'up' : 'neutral'" v-if="s.trend">
          {{ s.up ? '↑' : '→' }} {{ s.trend }}
        </div>
      </div>
    </div>

    <!-- Content Grid -->
    <div class="content-grid">

      <!-- Recent Handovers -->
      <div class="card card-wide">
        <div class="card-header">
          <h2 class="card-title">Letzte Übergaben</h2>
          <span class="card-badge">Heute</span>
        </div>

        <div class="table-wrap">
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
                <td>
                  <span class="status-chip" :class="h.status">
                    {{ statusLabel(h.status) }}
                  </span>
                </td>
                <td class="time-cell">{{ formatTime(h.created_at) }}</td>
              </tr>
            </tbody>
          </table>

          <div class="empty-state" v-else>
            <span class="empty-icon">📋</span>
            <p>Noch keine Übergaben heute</p>
          </div>
        </div>
      </div>

      <!-- Quick Actions -->
      <div class="card card-actions">
        <h2 class="card-title">Aktionen</h2>
        <div class="actions-list">
          <button
            class="action-btn primary"
            v-if="!authStore.isViewer"
            @click="$emit('navigate', 'handover')"
          >
            <span class="action-icon">✍️</span>
            <div class="action-text">
              <strong>Übergabe starten</strong>
              <span>Referenz eingeben & loslegen</span>
            </div>
            <span class="action-arrow">›</span>
          </button>

          <button class="action-btn" @click="$emit('navigate', 'archive')">
            <span class="action-icon">📁</span>
            <div class="action-text">
              <strong>Archiv öffnen</strong>
              <span>Vergangene Übergaben</span>
            </div>
            <span class="action-arrow">›</span>
          </button>

          <button class="action-btn" v-if="authStore.isAdmin" @click="$emit('navigate', 'users')">
            <span class="action-icon">👥</span>
            <div class="action-text">
              <strong>Benutzer verwalten</strong>
              <span>Accounts & Berechtigungen</span>
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

const authStore  = useAuthStore()
const handovers  = ref([])
const loading    = ref(true)

const today = computed(() => new Date().toLocaleDateString('de-CH', {
  weekday: 'long', day: 'numeric', month: 'long', year: 'numeric'
}))

const greeting = computed(() => {
  const h = new Date().getHours()
  if (h < 12) return 'Guten Morgen'
  if (h < 18) return 'Guten Tag'
  return 'Guten Abend'
})

const stats = computed(() => [
  { icon: '✅', value: handovers.value.filter(h => h.status === 'archived').length, label: 'Abgeschlossen heute', up: true, trend: '' },
  { icon: '⏳', value: handovers.value.filter(h => h.status === 'pending').length,  label: 'Ausstehend', neutral: true },
  { icon: '📦', value: handovers.value.length, label: 'Total heute', trend: '' },
  { icon: '🚚', value: new Set(handovers.value.map(h => h.carrier?.company_name).filter(Boolean)).size, label: 'Spediteure heute' },
])

function statusLabel(s) {
  return { pending: 'Ausstehend', printed: 'Gedruckt', signed: 'Unterschrieben', archived: 'Archiviert' }[s] || s
}

function formatTime(dt) {
  if (!dt) return '—'
  return new Date(dt).toLocaleTimeString('de-CH', { hour: '2-digit', minute: '2-digit' })
}

onMounted(async () => {
  try {
    const res = await api.get('/handover/list')
    handovers.value = res.data
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=DM+Sans:wght@300;400;500&display=swap');

.dashboard {
  padding: 40px 48px;
  max-width: 1200px;
  font-family: 'DM Sans', sans-serif;
}

/* ── Header ──────────────────────────────────── */
.dash-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 40px;
  animation: fadeUp 0.5s ease both;
}
.dash-title {
  font-family: 'Instrument Serif', serif;
  font-size: 40px;
  font-weight: 400;
  color: #1d1d1f;
  letter-spacing: -1.5px;
  line-height: 1;
}
.dash-sub  { font-size: 15px; color: #6e6e73; margin-top: 6px; font-weight: 300; }
.dash-date { font-size: 13px; color: #98989f; margin-top: 6px; }

/* ── Stats ───────────────────────────────────── */
.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 32px;
}

.stat-card {
  background: white;
  border-radius: 16px;
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 16px;
  border: 1px solid #f0f0f0;
  animation: fadeUp 0.5s ease both;
  position: relative;
  overflow: hidden;
}
.stat-icon {
  font-size: 24px;
  width: 48px; height: 48px;
  background: #f5f5f7;
  border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.stat-value {
  font-family: 'Instrument Serif', serif;
  font-size: 32px;
  font-weight: 400;
  color: #1d1d1f;
  line-height: 1;
  letter-spacing: -1px;
}
.stat-label { font-size: 12px; color: #98989f; margin-top: 2px; }
.stat-trend {
  position: absolute;
  top: 16px; right: 16px;
  font-size: 11px;
  font-weight: 500;
}
.stat-trend.up { color: #28c840; }
.stat-trend.neutral { color: #98989f; }

/* ── Content Grid ────────────────────────────── */
.content-grid {
  display: grid;
  grid-template-columns: 1fr 300px;
  gap: 16px;
}

.card {
  background: white;
  border-radius: 16px;
  padding: 28px;
  border: 1px solid #f0f0f0;
  animation: fadeUp 0.5s ease 0.2s both;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
}
.card-title {
  font-family: 'Instrument Serif', serif;
  font-size: 22px;
  font-weight: 400;
  color: #1d1d1f;
  letter-spacing: -0.5px;
  flex: 1;
}
.card-badge {
  font-size: 11px;
  font-weight: 600;
  color: #0071e3;
  background: rgba(0,113,227,0.08);
  padding: 3px 10px;
  border-radius: 980px;
}

/* ── Table ───────────────────────────────────── */
.ho-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}
.ho-table th {
  text-align: left;
  font-size: 11px;
  font-weight: 500;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: #98989f;
  padding: 0 12px 12px;
  border-bottom: 1px solid #f0f0f0;
}
.ho-table td {
  padding: 14px 12px;
  border-bottom: 1px solid #f9f9f9;
  color: #1d1d1f;
  font-weight: 300;
}
.ho-table tr:last-child td { border-bottom: none; }
.ho-table tr:hover td { background: #fafafa; }

.ref-cell { font-family: monospace; font-size: 13px; font-weight: 600; color: #0071e3; }
.time-cell { color: #98989f; font-size: 13px; }

.status-chip {
  font-size: 11px;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: 980px;
  letter-spacing: 0.03em;
}
.status-chip.archived   { background: rgba(40,200,64,0.1);   color: #1a9e30; }
.status-chip.pending    { background: rgba(255,149,0,0.1);   color: #c87800; }
.status-chip.printed    { background: rgba(0,113,227,0.1);   color: #0071e3; }
.status-chip.signed     { background: rgba(90,200,250,0.15); color: #0077a8; }

.skeleton {
  height: 44px;
  background: linear-gradient(90deg, #f5f5f7 25%, #ebebeb 50%, #f5f5f7 75%);
  background-size: 200% 100%;
  border-radius: 8px;
  margin-bottom: 8px;
  animation: shimmer 1.4s infinite;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 48px;
  color: #98989f;
  font-size: 14px;
}
.empty-icon { font-size: 32px; }

/* ── Actions ─────────────────────────────────── */
.card-actions { animation-delay: 0.3s; }
.actions-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 20px;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px;
  border-radius: 12px;
  border: 1.5px solid #f0f0f0;
  background: #fafafa;
  cursor: pointer;
  text-align: left;
  width: 100%;
  transition: all 0.18s;
}
.action-btn:hover {
  border-color: #e0e0e0;
  background: white;
  transform: translateY(-1px);
  box-shadow: 0 4px 16px rgba(0,0,0,0.06);
}
.action-btn.primary {
  background: #1d1d1f;
  border-color: #1d1d1f;
}
.action-btn.primary:hover {
  background: #000;
  border-color: #000;
}
.action-btn.primary strong,
.action-btn.primary span { color: white !important; }
.action-btn.primary .action-arrow { color: rgba(255,255,255,0.4); }

.action-icon {
  font-size: 20px;
  width: 40px; height: 40px;
  background: rgba(255,255,255,0.12);
  border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.action-btn:not(.primary) .action-icon { background: #f0f0f0; }

.action-text { flex: 1; }
.action-text strong { display: block; font-size: 14px; font-weight: 500; color: #1d1d1f; }
.action-text span   { display: block; font-size: 12px; color: #98989f; margin-top: 1px; }

.action-arrow { color: #c8c8c8; font-size: 20px; }

@keyframes fadeUp {
  from { opacity: 0; transform: translateY(12px); }
  to   { opacity: 1; transform: translateY(0); }
}
@keyframes shimmer {
  to { background-position: -200% 0; }
}
</style>
