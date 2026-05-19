<template>
  <div class="stats-page">

    <div class="page-header">
      <div>
        <p class="page-eyebrow">Übersicht</p>
        <h1 class="page-title">Statistik</h1>
      </div>
      <!-- Monatsfilter -->
      <div class="month-picker">
        <button class="pg-btn" @click="prevMonth">←</button>
        <span class="month-label">{{ monthLabel }}</span>
        <button class="pg-btn" @click="nextMonth" :disabled="isCurrentMonth">→</button>
      </div>
    </div>

    <div class="loading-state" v-if="loading">
      <div class="skeleton-section" v-for="i in 2" :key="i">
        <div class="skeleton skeleton-title"></div>
        <div class="skeleton-grid">
          <div class="skeleton skeleton-card" v-for="j in 5" :key="j"></div>
        </div>
      </div>
    </div>

    <template v-else>
      <!-- LKW -->
      <section class="stat-section">
        <div class="section-header">
          <span class="section-icon">🚛</span>
          <h2 class="section-title">LKW-Übergaben</h2>
        </div>
        <div class="cards-grid">
          <div class="stat-card" v-for="(card, i) in lkwCards" :key="card.key" :style="`animation-delay:${i*0.06}s`">
            <div class="card-value">{{ card.value }}</div>
            <div class="card-label">{{ card.label }}</div>
            <div class="card-sub" v-if="card.sub">{{ card.sub }}</div>
          </div>
        </div>
        <!-- Carrier-Aufschlüsselung LKW -->
        <div class="carrier-breakdown" v-if="data?.lkw?.by_carrier?.length">
          <div class="breakdown-title">Spediteure — {{ monthLabel }}</div>
          <div class="carrier-rows">
            <div class="carrier-row" v-for="c in data.lkw.by_carrier" :key="c.name">
              <span class="carrier-name">{{ c.name }}</span>
              <div class="carrier-bar-wrap">
                <div class="carrier-bar lkw" :style="`width:${barWidth(c.count, maxLkwCount)}%`"></div>
              </div>
              <span class="carrier-count">{{ c.count }}</span>
            </div>
          </div>
        </div>
      </section>

      <!-- Kurier -->
      <section class="stat-section">
        <div class="section-header">
          <span class="section-icon">📦</span>
          <h2 class="section-title">Kurier-Sendungen</h2>
        </div>
        <div class="cards-grid">
          <div class="stat-card" v-for="(card, i) in courierCards" :key="card.key" :style="`animation-delay:${i*0.06 + 0.2}s`">
            <div class="card-value">{{ card.value }}</div>
            <div class="card-label">{{ card.label }}</div>
            <div class="card-sub" v-if="card.sub">{{ card.sub }}</div>
          </div>
        </div>
        <!-- Carrier-Aufschlüsselung Kurier -->
        <div class="carrier-breakdown" v-if="data?.courier?.by_carrier?.length">
          <div class="breakdown-title">Carrier — {{ monthLabel }}</div>
          <div class="carrier-rows">
            <div class="carrier-row" v-for="c in data.courier.by_carrier" :key="c.name">
              <span class="carrier-name">{{ c.name }}</span>
              <div class="carrier-bar-wrap">
                <div class="carrier-bar courier" :style="`width:${barWidth(c.count, maxCourierCount)}%`"></div>
              </div>
              <span class="carrier-count">{{ c.count }}</span>
            </div>
          </div>
        </div>
      </section>
    </template>

    <div class="error-state" v-if="error">
      <span>⚠</span>
      <p>{{ error }}</p>
      <button class="btn-retry" @click="load">Erneut laden</button>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '../api'

const data    = ref(null)
const loading = ref(true)
const error   = ref('')

const today = new Date()
const selYear  = ref(today.getFullYear())
const selMonth = ref(today.getMonth() + 1)  // 1-based

const MONTH_NAMES = ['Januar','Februar','März','April','Mai','Juni','Juli','August','September','Oktober','November','Dezember']

const monthLabel = computed(() => `${MONTH_NAMES[selMonth.value - 1]} ${selYear.value}`)

const isCurrentMonth = computed(() => {
  const now = new Date()
  return selYear.value === now.getFullYear() && selMonth.value === now.getMonth() + 1
})

function prevMonth() {
  if (selMonth.value === 1) { selMonth.value = 12; selYear.value-- }
  else selMonth.value--
  load()
}
function nextMonth() {
  if (isCurrentMonth.value) return
  if (selMonth.value === 12) { selMonth.value = 1; selYear.value++ }
  else selMonth.value++
  load()
}

const lkwCards = computed(() => {
  const d = data.value?.lkw
  if (!d) return []
  return [
    { key: 'this_month', value: d.this_month, label: `${monthLabel.value}`,           sub: 'aktueller Monat' },
    { key: 'total',      value: d.total,      label: 'Abholungen total',              sub: 'seit Einrichtung' },
    { key: 'this_year',  value: d.this_year,  label: `Jahr ${selYear.value}`,          sub: 'laufendes Jahr' },
    { key: 'today',      value: d.today,      label: 'Heute',                         sub: new Date().toLocaleDateString('de-CH', { day: '2-digit', month: '2-digit', year: 'numeric' }) },
    { key: 'archived',   value: d.archived,   label: 'Abgeschlossen',                 sub: 'archiviert' },
  ]
})

const courierCards = computed(() => {
  const d = data.value?.courier
  if (!d) return []
  return [
    { key: 'this_month', value: d.this_month, label: `${monthLabel.value}`,           sub: 'aktueller Monat' },
    { key: 'total',      value: d.total,      label: 'Sendungen total',               sub: 'seit Einrichtung' },
    { key: 'this_year',  value: d.this_year,  label: `Jahr ${selYear.value}`,          sub: 'laufendes Jahr' },
    { key: 'today',      value: d.today,      label: 'Heute',                         sub: new Date().toLocaleDateString('de-CH', { day: '2-digit', month: '2-digit', year: 'numeric' }) },
    { key: 'archived',   value: d.archived,   label: 'Archiviert',                    sub: 'unterschrieben & abgelegt' },
  ]
})

const maxLkwCount     = computed(() => Math.max(1, ...(data.value?.lkw?.by_carrier?.map(c => c.count) || [1])))
const maxCourierCount = computed(() => Math.max(1, ...(data.value?.courier?.by_carrier?.map(c => c.count) || [1])))

function barWidth(count, max) {
  return Math.round((count / max) * 100)
}

async function load() {
  loading.value = true
  error.value   = ''
  try {
    const res  = await api.get('/stats', { params: { year: selYear.value, month: selMonth.value } })
    data.value = res.data
  } catch (e) {
    error.value = e.response?.data?.detail || e.message || 'Statistik konnte nicht geladen werden'
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=DM+Sans:wght@300;400;500;600&display=swap');

.stats-page {
  padding: 24px 32px;
  max-width: 1000px;
  font-family: 'DM Sans', sans-serif;
}

/* ── Header ── */
.page-header {
  display: flex; justify-content: space-between; align-items: flex-end;
  margin-bottom: 36px; animation: fadeUp 0.4s ease both;
}
.page-eyebrow {
  font-size: 12px; font-weight: 500; letter-spacing: 0.05em;
  text-transform: uppercase; color: #98989f; margin-bottom: 5px;
}
.page-title {
  font-family: 'Instrument Serif', serif;
  font-size: 38px; font-weight: 400; color: #1c1c1e; letter-spacing: -1px;
}

/* ── Month Picker ── */
.month-picker {
  display: flex; align-items: center; gap: 10px;
  background: white; border: 1.5px solid #e8e8ed; border-radius: 12px;
  padding: 8px 14px;
}
.month-label { font-size: 14px; font-weight: 500; color: #1c1c1e; min-width: 140px; text-align: center; }
.pg-btn {
  width: 32px; height: 32px; border-radius: 8px; border: 1.5px solid #e8e8ed;
  background: white; cursor: pointer; font-size: 14px; transition: all 0.15s;
}
.pg-btn:hover:not(:disabled) { border-color: #c0546a; color: #c0546a; }
.pg-btn:disabled { opacity: 0.3; cursor: not-allowed; }

/* ── Sections ── */
.stat-section { margin-bottom: 40px; animation: fadeUp 0.4s ease both; }

.section-header {
  display: flex; align-items: center; gap: 10px;
  margin-bottom: 16px;
}
.section-icon { font-size: 20px; }
.section-title {
  font-family: 'Instrument Serif', serif;
  font-size: 22px; font-weight: 400; color: #1c1c1e; letter-spacing: -0.3px;
}

/* ── Cards ── */
.cards-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 12px;
}

.stat-card {
  background: white;
  border-radius: 16px;
  padding: 22px 18px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 0 0 1px rgba(0,0,0,0.04);
  animation: fadeUp 0.4s ease both;
  display: flex; flex-direction: column; gap: 4px;
}
.stat-card:first-child {
  background: linear-gradient(135deg, rgba(192,84,106,0.06), rgba(192,84,106,0.02));
  border: 1.5px solid rgba(192,84,106,0.15);
}

.card-value {
  font-family: 'Instrument Serif', serif;
  font-size: 36px; font-weight: 400;
  color: #1c1c1e; letter-spacing: -1.5px; line-height: 1;
}
.card-label {
  font-size: 13px; font-weight: 500; color: #3a3a3c;
  margin-top: 6px;
}
.card-sub {
  font-size: 11px; color: #98989f;
}

/* ── Carrier Breakdown ── */
.carrier-breakdown {
  margin-top: 16px;
  background: white; border-radius: 14px; padding: 18px 20px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 0 0 1px rgba(0,0,0,0.04);
}
.breakdown-title {
  font-size: 12px; font-weight: 600; letter-spacing: 0.05em;
  text-transform: uppercase; color: #98989f; margin-bottom: 14px;
}
.carrier-rows { display: flex; flex-direction: column; gap: 10px; }
.carrier-row {
  display: flex; align-items: center; gap: 12px;
}
.carrier-name {
  font-size: 14px; font-weight: 500; color: #1c1c1e;
  min-width: 140px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.carrier-bar-wrap { flex: 1; height: 8px; background: #f0f0f0; border-radius: 4px; overflow: hidden; }
.carrier-bar { height: 100%; border-radius: 4px; transition: width 0.5s ease; }
.carrier-bar.lkw     { background: linear-gradient(90deg, #f2a7b8, #c0546a); }
.carrier-bar.courier { background: linear-gradient(90deg, #8bbbd4, #5b8db8); }
.carrier-count { font-size: 14px; font-weight: 600; color: #1c1c1e; min-width: 28px; text-align: right; }

/* ── Loading Skeletons ── */
.loading-state { display: flex; flex-direction: column; gap: 40px; }
.skeleton-section { display: flex; flex-direction: column; gap: 16px; }
.skeleton-title {
  height: 28px; width: 200px; border-radius: 8px;
}
.skeleton-grid {
  display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px;
}
.skeleton-card { height: 110px; border-radius: 16px; }
.skeleton {
  background: linear-gradient(90deg, #f5f5f7 25%, #ebebeb 50%, #f5f5f7 75%);
  background-size: 200% 100%;
  animation: shimmer 1.4s infinite;
}

/* ── Error ── */
.error-state {
  display: flex; flex-direction: column; align-items: center;
  gap: 10px; padding: 48px; color: #98989f; font-size: 14px;
}
.error-state span { font-size: 28px; }
.btn-retry {
  margin-top: 6px; padding: 10px 20px; border-radius: 10px;
  background: white; border: 1.5px solid #e8e8ed;
  font-family: 'DM Sans', sans-serif; font-size: 13px; font-weight: 500;
  color: #1c1c1e; cursor: pointer; transition: all 0.15s;
}
.btn-retry:hover { background: #f5f5f7; }

@keyframes fadeUp  { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
@keyframes shimmer { to { background-position: -200% 0; } }
</style>
