<template>
  <div class="stats-page">

    <div class="page-header">
      <p class="page-eyebrow">Übersicht</p>
      <h1 class="page-title">Statistik</h1>
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

const currentYear = new Date().getFullYear()

const lkwCards = computed(() => {
  const d = data.value?.lkw
  if (!d) return []
  return [
    { key: 'total',     value: d.total,     label: 'Abholungen total',                 sub: 'seit Einrichtung' },
    { key: 'this_year', value: d.this_year, label: `Abholungen ${currentYear}`,         sub: 'laufendes Jahr' },
    { key: 'today',     value: d.today,     label: 'Abholungen heute',                 sub: new Date().toLocaleDateString('de-CH', { day: '2-digit', month: '2-digit', year: 'numeric' }) },
    { key: 'archived',  value: d.archived,  label: 'Abgeschlossen',                    sub: 'archiviert' },
    { key: 'carriers',  value: d.carriers,  label: 'Spediteure',                       sub: 'aktiv erfasst' },
  ]
})

const courierCards = computed(() => {
  const d = data.value?.courier
  if (!d) return []
  return [
    { key: 'total',     value: d.total,     label: 'Sendungen total',                  sub: 'seit Einrichtung' },
    { key: 'this_year', value: d.this_year, label: `Sendungen ${currentYear}`,          sub: 'laufendes Jahr' },
    { key: 'today',     value: d.today,     label: 'Sendungen heute',                  sub: new Date().toLocaleDateString('de-CH', { day: '2-digit', month: '2-digit', year: 'numeric' }) },
    { key: 'archived',  value: d.archived,  label: 'Archiviert',                       sub: 'unterschrieben & abgelegt' },
    { key: 'carriers',  value: d.carriers,  label: 'Carrier',                          sub: 'aktiv konfiguriert' },
  ]
})

async function load() {
  loading.value = true
  error.value   = ''
  try {
    const res  = await api.get('/stats')
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
.page-header { margin-bottom: 36px; animation: fadeUp 0.4s ease both; }
.page-eyebrow {
  font-size: 12px; font-weight: 500; letter-spacing: 0.05em;
  text-transform: uppercase; color: #98989f; margin-bottom: 5px;
}
.page-title {
  font-family: 'Instrument Serif', serif;
  font-size: 38px; font-weight: 400; color: #1c1c1e; letter-spacing: -1px;
}

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
