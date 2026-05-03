<template>
  <div class="courier-archive">
    <header class="page-header">
      <div>
        <h1 class="page-title">Kurier-Archiv</h1>
        <p class="page-sub">
          Archivierte Kurier-Sendungen mit Fahrer-Unterschrift — durchsuchbar nach Datum und Carrier.
        </p>
      </div>
    </header>

    <!-- Filter-Toolbar -->
    <div class="toolbar">
      <label class="field">
        <span class="field-label">Von</span>
        <input type="date" :value="dateFrom" @change="onDateFromChange" />
      </label>
      <label class="field">
        <span class="field-label">Bis</span>
        <input type="date" :value="dateTo" @change="onDateToChange" />
      </label>
      <label class="field">
        <span class="field-label">Carrier</span>
        <select :value="carrierFilter ?? ''" @change="onCarrierChange">
          <option value="">Alle</option>
          <option
            v-for="c in carriers"
            :key="c.id"
            :value="c.id"
          >{{ c.display_name }}</option>
        </select>
      </label>
      <label class="field grow">
        <span class="field-label">Suche (LS-Nummer)</span>
        <input
          type="text"
          v-model="search"
          placeholder="80…/17…/C_…"
        />
      </label>
      <button class="btn-ghost" @click="resetFilters" title="Filter zurücksetzen">
        ✕ Filter
      </button>
    </div>

    <!-- Liste -->
    <div v-if="loading" class="state">Wird geladen…</div>
    <div v-else-if="error" class="state error">{{ error }}</div>
    <div v-else-if="filteredItems.length === 0" class="state empty">
      <span class="empty-icon">🗂</span>
      <p>Keine archivierten Sendungen für diese Filter.</p>
    </div>

    <ul v-else class="archive-list">
      <li
        v-for="item in filteredItems"
        :key="item.archive_id"
        class="archive-row"
        :style="{ '--carrier-color': carrierColor(item.carrier_name) }"
      >
        <div class="row-left">
          <div class="ls-line">
            <span
              v-for="ls in item.delivery_note_numbers"
              :key="ls"
              class="ls"
            >{{ ls }}</span>
            <span v-if="item.delivery_note_numbers.length === 0" class="ls ls-missing">
              ohne LS-Nummer
            </span>
          </div>
          <div class="meta-line">
            <span class="carrier-pill">{{ item.carrier_display_name }}</span>
            <span>·</span>
            <span>{{ formatDate(item.process_date) }}</span>
            <span v-if="item.signer_name">·</span>
            <span v-if="item.signer_name" class="signer">{{ item.signer_name }}</span>
            <span>·</span>
            <span class="archived-at">archiviert {{ formatDateTime(item.archived_at) }}</span>
          </div>
          <div v-if="item.email_subject" class="subject" :title="item.email_subject">
            ✉ {{ item.email_subject }}
          </div>
        </div>
        <div class="row-actions">
          <button
            class="btn-icon"
            title="Signiertes PDF öffnen"
            :disabled="opening === item.archive_id"
            @click="openPdf(item.archive_id)"
          >
            <span v-if="opening === item.archive_id" class="spinner-sm" />
            <span v-else>👁</span>
          </button>
        </div>
      </li>
    </ul>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import api from '../api'

const items   = ref([])
const carriers = ref([])
const loading = ref(false)
const error   = ref(null)
const opening = ref(null)

// Defaults: letzte 30 Tage
function isoDaysAgo(n) {
  const d = new Date()
  d.setDate(d.getDate() - n)
  return d.toISOString().slice(0, 10)
}
function todayIso() { return new Date().toISOString().slice(0, 10) }

const dateFrom       = ref(isoDaysAgo(30))
const dateTo         = ref(todayIso())
const carrierFilter  = ref(null)
const search         = ref('')

const COLORS = {
  fedex_tnt: 'var(--carrier-fedex)',
  dhl:       'var(--carrier-dhl)',
  ups:       'var(--carrier-ups)',
}
function carrierColor(name) { return COLORS[name] || 'var(--carrier-unknown)' }

function formatDate(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  return isNaN(d) ? iso : d.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' })
}
function formatDateTime(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  return isNaN(d) ? iso : d.toLocaleString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

async function loadCarriers() {
  try {
    const res = await api.get('/api/courier/carriers', { params: { include_inactive: true } })
    carriers.value = res.data || []
  } catch { carriers.value = [] }
}

async function load() {
  loading.value = true
  error.value   = null
  try {
    const params = { date_from: dateFrom.value, date_to: dateTo.value }
    if (carrierFilter.value != null) params.carrier_id = carrierFilter.value
    const res = await api.get('/api/courier/archive', { params })
    items.value = res.data || []
  } catch (e) {
    error.value = e?.response?.data?.detail || e?.message || 'Archiv konnte nicht geladen werden'
  } finally {
    loading.value = false
  }
}

const filteredItems = computed(() => {
  const q = search.value.trim().toLowerCase()
  if (!q) return items.value
  return items.value.filter(it =>
    (it.delivery_note_numbers || []).some(ls => ls.toLowerCase().includes(q))
    || (it.email_subject || '').toLowerCase().includes(q),
  )
})

function onDateFromChange(e) { dateFrom.value = e.target.value; load() }
function onDateToChange(e)   { dateTo.value   = e.target.value; load() }
function onCarrierChange(e) {
  const v = e.target.value
  carrierFilter.value = v === '' ? null : Number(v)
  load()
}
function resetFilters() {
  dateFrom.value      = isoDaysAgo(30)
  dateTo.value        = todayIso()
  carrierFilter.value = null
  search.value        = ''
  load()
}

async function openPdf(archiveId) {
  if (opening.value) return
  opening.value = archiveId
  try {
    const res = await api.get(`/api/courier/archive/${archiveId}/file`, { responseType: 'blob' })
    const url = URL.createObjectURL(res.data)
    window.open(url, '_blank')
    // Browser hat das Blob — nach kurzem Delay revoken (sonst close er das Tab leer)
    setTimeout(() => URL.revokeObjectURL(url), 60000)
  } catch (e) {
    error.value = e?.response?.data?.detail || e?.message || 'PDF konnte nicht geöffnet werden'
  } finally {
    opening.value = null
  }
}

onMounted(async () => {
  await loadCarriers()
  await load()
})
</script>

<style scoped>
.courier-archive {
  padding: 32px 48px 64px;
  font-family: 'DM Sans', sans-serif;
  color: var(--color-text);
  min-height: 100%;
}

.page-header { margin-bottom: 24px; }
.page-title {
  font-family: 'Instrument Serif', 'Cormorant Garamond', serif;
  font-size: 36px; font-weight: 400; letter-spacing: -1.2px;
  margin: 0;
}
.page-sub {
  font-size: 14px;
  color: var(--color-text-muted);
  margin-top: 4px;
}

.toolbar {
  display: flex;
  align-items: flex-end;
  gap: 12px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  padding: 14px 16px;
  margin-bottom: 20px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
  flex-wrap: wrap;
}
.field {
  display: flex; flex-direction: column; gap: 4px;
  min-width: 130px;
}
.field.grow { flex: 1; min-width: 200px; }
.field-label {
  font-size: 10.5px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-text-muted);
}
.field input, .field select {
  padding: 8px 12px;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  font-size: 13px;
  font-family: 'DM Sans', sans-serif;
  background: var(--color-surface);
}
.field input:focus, .field select:focus {
  outline: none;
  border-color: var(--accent-primary);
}

.btn-ghost {
  padding: 9px 14px;
  background: transparent;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  font-size: 12.5px;
  cursor: pointer;
  color: var(--color-text-muted);
}
.btn-ghost:hover { background: var(--accent-bg); color: var(--accent-primary); }

.state {
  text-align: center;
  padding: 32px 24px;
  color: var(--color-text-muted);
  font-size: 13.5px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 12px;
}
.state.error  { color: var(--color-danger); border-color: rgba(239,68,68,0.25); background: rgba(239,68,68,0.05); }
.state.empty  { padding: 56px 24px; }
.empty-icon   { font-size: 36px; display: block; margin-bottom: 8px; }

.archive-list { list-style: none; padding: 0; margin: 0; }
.archive-row {
  display: flex; justify-content: space-between; align-items: center;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-left: 4px solid var(--carrier-color);
  border-radius: 12px;
  padding: 14px 18px;
  margin-bottom: 8px;
  gap: 16px;
  transition: box-shadow 150ms ease, transform 150ms ease;
}
.archive-row:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.06);
  transform: translateY(-1px);
}

.row-left { display: flex; flex-direction: column; gap: 4px; min-width: 0; flex: 1; }
.ls-line {
  display: flex; flex-wrap: wrap; gap: 8px;
}
.ls {
  font-family: 'DM Mono', 'JetBrains Mono', monospace;
  font-size: 13.5px;
  font-weight: 500;
  color: var(--color-text);
}
.ls.ls-missing {
  color: var(--color-warning);
  font-style: italic;
  font-size: 12px;
}

.meta-line {
  display: flex; align-items: center; gap: 6px;
  font-size: 11.5px;
  color: var(--color-text-muted);
  flex-wrap: wrap;
}
.carrier-pill {
  background: var(--accent-bg);
  color: var(--accent-primary);
  padding: 2px 8px;
  border-radius: 9999px;
  font-weight: 500;
}
.signer {
  color: var(--color-text);
  font-weight: 500;
}
.subject {
  font-size: 11.5px;
  color: var(--color-text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
}

.row-actions { display: flex; gap: 6px; flex-shrink: 0; }
.btn-icon {
  width: 36px; height: 32px;
  background: transparent;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
  color: var(--color-text-muted);
  display: inline-flex; align-items: center; justify-content: center;
  transition: all 150ms ease;
}
.btn-icon:hover:not(:disabled) {
  background: var(--accent-primary);
  color: white;
  border-color: var(--accent-primary);
}
.btn-icon:disabled { opacity: 0.5; cursor: not-allowed; }

.spinner-sm {
  width: 12px; height: 12px;
  border: 2px solid var(--color-border);
  border-top-color: var(--accent-primary);
  border-radius: 50%;
  animation: spin 700ms linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
</style>
