<template>
  <div class="archive-page">

    <div class="page-header">
      <div>
        <p class="page-eyebrow">Verwaltung</p>
        <h1 class="page-title">Archiv</h1>
      </div>
      <div class="header-stats">
        <div class="hstat"><span class="hstat-val">{{ handovers.length }}</span><span class="hstat-label">Total</span></div>
        <div class="hstat"><span class="hstat-val">{{ todayCount }}</span><span class="hstat-label">Heute</span></div>
      </div>
    </div>

    <div class="toolbar">
      <div class="search-wrap">
        <span>🔍</span>
        <input v-model="searchQuery" type="text" class="search-input" placeholder="Referenz, Spediteur oder Fahrer…" />
        <button class="btn-clear" v-if="searchQuery" @click="searchQuery = ''">✕</button>
      </div>
      <div class="filter-group">
        <select v-model="filterStatus" class="filter-select">
          <option value="">Alle Status</option>
          <option value="archived">Archiviert</option>
          <option value="signed">Unterschrieben</option>
          <option value="pending">Ausstehend</option>
        </select>
        <input v-model="filterDateFrom" type="date" class="filter-select" />
        <input v-model="filterDateTo"   type="date" class="filter-select" />
        <button class="btn-reset" v-if="hasFilters" @click="resetFilters">✕ Filter</button>
      </div>
    </div>

    <div class="archive-grid" :class="{ 'with-preview': selectedHandover }">

      <div class="table-card">
        <div class="table-loading" v-if="loading">
          <div class="skeleton" v-for="i in 8" :key="i"></div>
        </div>
        <div class="empty-state" v-else-if="!filteredHandovers.length">
          <span>📭</span><p>Keine Übergaben gefunden</p>
          <small v-if="hasFilters">Filter anpassen oder zurücksetzen</small>
        </div>
        <template v-else>
          <table class="archive-table">
            <thead>
              <tr>
                <th class="sortable" @click="sortBy('referenz')">Referenz <span>{{ sortIcon('referenz') }}</span></th>
                <th class="sortable" @click="sortBy('carrier')">Spediteur <span>{{ sortIcon('carrier') }}</span></th>
                <th>Fahrer</th>
                <th>Kennzeichen</th>
                <th class="sortable" @click="sortBy('status')">Status <span>{{ sortIcon('status') }}</span></th>
                <th class="sortable" @click="sortBy('created_at')">Datum <span>{{ sortIcon('created_at') }}</span></th>
                <th>PDF</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="h in paginatedHandovers" :key="h.id" class="table-row" :class="{ selected: selectedHandover?.id === h.id }" @click="selectHandover(h)">
                <td class="ref-cell">{{ h.referenz }}</td>
                <td>{{ h.carrier?.company_name || '—' }}</td>
                <td>{{ h.driver_name || '—' }}</td>
                <td class="plate-cell">{{ h.truck_plate || '—' }}</td>
                <td><span class="chip" :class="h.status">{{ statusLabel(h.status) }}</span></td>
                <td><div>{{ formatDate(h.created_at) }}</div><div class="time-sub">{{ formatTime(h.created_at) }}</div></td>
                <td><button class="btn-pdf" v-if="h.pdf_path" @click.stop="openPdf(h)">📄</button><span v-else class="no-pdf">—</span></td>
              </tr>
            </tbody>
          </table>
          <div class="pagination" v-if="totalPages > 1">
            <button class="pg-btn" :disabled="page === 1" @click="page--">←</button>
            <span class="pg-info">{{ page }} / {{ totalPages }}</span>
            <button class="pg-btn" :disabled="page === totalPages" @click="page++">→</button>
          </div>
        </template>
      </div>

      <div class="preview-panel" v-if="selectedHandover">
        <div class="preview-header">
          <h3 class="preview-title">{{ selectedHandover.referenz }}</h3>
          <button class="btn-close" @click="selectedHandover = null; pdfUrl = null">✕</button>
        </div>
        <div class="preview-meta">
          <div class="meta-row"><span>Status</span><span class="chip" :class="selectedHandover.status">{{ statusLabel(selectedHandover.status) }}</span></div>
          <div class="meta-row"><span>Spediteur</span><strong>{{ selectedHandover.carrier?.company_name || '—' }}</strong></div>
          <div class="meta-row"><span>Fahrer</span><strong>{{ selectedHandover.driver_name || '—' }}</strong></div>
          <div class="meta-row"><span>Kennzeichen</span><strong>{{ selectedHandover.truck_plate || '—' }}</strong></div>
          <div class="meta-row"><span>Erstellt</span><strong>{{ formatDate(selectedHandover.created_at) }} {{ formatTime(selectedHandover.created_at) }}</strong></div>
          <div class="meta-row" v-if="selectedHandover.signed_at"><span>Unterzeichnet</span><strong>{{ formatDate(selectedHandover.signed_at) }}</strong></div>
        </div>
        <div class="preview-actions">
          <button class="btn-action primary" v-if="pdfUrl" @click="openPdf(selectedHandover)">📄 Öffnen</button>
          <button class="btn-action" v-if="pdfUrl" @click="downloadPdf(selectedHandover)">⬇ Download</button>
        </div>
        <div class="pdf-embed-wrap" v-if="pdfUrl"><iframe :src="pdfUrl" class="pdf-embed" frameborder="0"></iframe></div>
        <div class="pdf-loading" v-else-if="selectedHandover.pdf_path && loadingPdf"><div class="spinner"></div><span>PDF wird geladen…</span></div>
        <div class="pdf-none" v-else-if="!selectedHandover.pdf_path"><span>📄</span><p>Kein PDF verfügbar</p></div>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '../api'

const handovers = ref([]); const loading = ref(true)
const selectedHandover = ref(null); const pdfUrl = ref(null); const loadingPdf = ref(false)
const searchQuery = ref(''); const filterStatus = ref(''); const filterDateFrom = ref(''); const filterDateTo = ref('')
const page = ref(1); const perPage = 12; const sortField = ref('created_at'); const sortDir = ref('desc')

const hasFilters = computed(() => searchQuery.value || filterStatus.value || filterDateFrom.value || filterDateTo.value)
const todayCount = computed(() => { const t = new Date().toDateString(); return handovers.value.filter(h => new Date(h.created_at).toDateString() === t).length })

const filteredHandovers = computed(() => {
  let list = [...handovers.value]
  if (searchQuery.value) { const q = searchQuery.value.toLowerCase(); list = list.filter(h => h.referenz?.toLowerCase().includes(q) || h.carrier?.company_name?.toLowerCase().includes(q) || h.driver_name?.toLowerCase().includes(q) || h.truck_plate?.toLowerCase().includes(q)) }
  if (filterStatus.value) list = list.filter(h => h.status === filterStatus.value)
  if (filterDateFrom.value) list = list.filter(h => new Date(h.created_at) >= new Date(filterDateFrom.value))
  if (filterDateTo.value)   list = list.filter(h => new Date(h.created_at) <= new Date(filterDateTo.value + 'T23:59:59'))
  list.sort((a, b) => { let va = sortField.value === 'carrier' ? a.carrier?.company_name : a[sortField.value]; let vb = sortField.value === 'carrier' ? b.carrier?.company_name : b[sortField.value]; const cmp = String(va||'').localeCompare(String(vb||'')); return sortDir.value === 'asc' ? cmp : -cmp })
  return list
})
const totalPages = computed(() => Math.max(1, Math.ceil(filteredHandovers.value.length / perPage)))
const paginatedHandovers = computed(() => { const s = (page.value-1)*perPage; return filteredHandovers.value.slice(s, s+perPage) })

function statusLabel(s) { return { pending: 'Ausstehend', printed: 'Gedruckt', signed: 'Unterschrieben', archived: 'Archiviert' }[s] || s }
function formatDate(dt) { return dt ? new Date(dt).toLocaleDateString('de-CH', { day: '2-digit', month: '2-digit', year: 'numeric' }) : '—' }
function formatTime(dt) { return dt ? new Date(dt).toLocaleTimeString('de-CH', { hour: '2-digit', minute: '2-digit' }) : '' }
function sortBy(f) { if (sortField.value === f) sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc'; else { sortField.value = f; sortDir.value = 'asc' }; page.value = 1 }
function sortIcon(f) { return sortField.value !== f ? '↕' : sortDir.value === 'asc' ? '↑' : '↓' }
function resetFilters() { searchQuery.value = ''; filterStatus.value = ''; filterDateFrom.value = ''; filterDateTo.value = ''; page.value = 1 }

async function selectHandover(h) {
  selectedHandover.value = h; pdfUrl.value = null
  if (!h.pdf_path) return
  loadingPdf.value = true
  try { const res = await api.get(`/handover/${h.id}/pdf`, { responseType: 'blob' }); pdfUrl.value = URL.createObjectURL(res.data) }
  catch {} finally { loadingPdf.value = false }
}
function openPdf(h) { if (pdfUrl.value) window.open(pdfUrl.value, '_blank') }
function downloadPdf(h) { if (!pdfUrl.value) return; const a = document.createElement('a'); a.href = pdfUrl.value; a.download = `handover_${h.referenz}.pdf`; a.click() }
onMounted(async () => { try { const res = await api.get('/handover/list'); handovers.value = res.data } catch (e) { console.error(e) } finally { loading.value = false } })
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=DM+Sans:wght@300;400;500;600&display=swap');

.archive-page { padding: 40px 44px; font-family: 'DM Sans', sans-serif; height: 100%; display: flex; flex-direction: column; overflow: hidden; }

.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 24px; }
.page-eyebrow { font-size: 12px; font-weight: 500; letter-spacing: 0.05em; text-transform: uppercase; color: #98989f; margin-bottom: 5px; }
.page-title { font-family: 'Instrument Serif', serif; font-size: 38px; font-weight: 400; color: #1c1c1e; letter-spacing: -1px; }
.header-stats { display: flex; gap: 24px; }
.hstat-val   { display: block; font-family: 'Instrument Serif', serif; font-size: 32px; color: #1c1c1e; letter-spacing: -1px; line-height: 1; text-align: right; }
.hstat-label { font-size: 11px; color: #98989f; text-align: right; }

.toolbar { display: flex; gap: 10px; align-items: center; margin-bottom: 14px; flex-wrap: wrap; }
.search-wrap { display: flex; align-items: center; gap: 8px; background: white; border: 1.5px solid #e8e8ed; border-radius: 12px; padding: 0 14px; flex: 1; min-width: 240px; transition: border-color 0.2s, box-shadow 0.2s; }
.search-wrap:focus-within { border-color: #c0546a; box-shadow: 0 0 0 3px rgba(192,84,106,0.1); }
.search-input { flex: 1; border: none; outline: none; font-family: 'DM Sans', sans-serif; font-size: 14px; padding: 11px 0; background: none; color: #1c1c1e; }
.search-input::placeholder { color: #c8c8c8; }
.btn-clear { background: none; border: none; color: #98989f; cursor: pointer; font-size: 13px; }
.filter-group { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
.filter-select { padding: 10px 12px; border: 1.5px solid #e8e8ed; border-radius: 10px; font-family: 'DM Sans', sans-serif; font-size: 13px; color: #1c1c1e; background: white; outline: none; }
.filter-select:focus { border-color: #c0546a; }
.btn-reset { padding: 10px 14px; background: none; border: 1.5px solid #e8e8ed; border-radius: 10px; font-size: 13px; color: #6e6e73; cursor: pointer; font-family: 'DM Sans', sans-serif; transition: all 0.2s; }
.btn-reset:hover { border-color: #ff3b30; color: #ff3b30; }

.archive-grid { display: grid; grid-template-columns: 1fr; gap: 14px; flex: 1; min-height: 0; }
.archive-grid.with-preview { grid-template-columns: 1fr 340px; }

.table-card { background: white; border-radius: 14px; box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 0 0 1px rgba(0,0,0,0.04); overflow: hidden; display: flex; flex-direction: column; min-height: 0; }

.archive-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.archive-table thead { position: sticky; top: 0; background: white; z-index: 2; }
.archive-table th { text-align: left; font-size: 11px; font-weight: 600; letter-spacing: 0.05em; text-transform: uppercase; color: #98989f; padding: 14px 16px; border-bottom: 1px solid #f0f0f0; white-space: nowrap; user-select: none; }
.sortable { cursor: pointer; transition: color 0.15s; }
.sortable:hover { color: #1c1c1e; }
.table-row td { padding: 12px 16px; border-bottom: 1px solid #f7f7f7; color: #1c1c1e; font-weight: 300; cursor: pointer; transition: background 0.1s; }
.table-row:hover td { background: #fafafa; }
.table-row.selected td { background: rgba(192,84,106,0.04); }
.table-row:last-child td { border-bottom: none; }
.ref-cell   { font-family: monospace; font-size: 12px; font-weight: 700; color: #c0546a; }
.plate-cell { font-family: monospace; font-size: 12px; color: #6e6e73; }
.time-sub   { font-size: 11px; color: #98989f; margin-top: 1px; }

.chip { font-size: 11px; font-weight: 600; padding: 3px 10px; border-radius: 980px; }
.chip.archived { background: rgba(40,167,69,0.1);  color: #1a7a2e; }
.chip.pending  { background: rgba(255,149,0,0.1);  color: #c07800; }
.chip.printed  { background: rgba(192,84,106,0.1); color: #c0546a; }
.chip.signed   { background: rgba(90,200,250,0.1); color: #0077a8; }

.btn-pdf { background: #f5f5f7; border: none; border-radius: 7px; padding: 5px 8px; cursor: pointer; font-size: 14px; transition: background 0.15s; }
.btn-pdf:hover { background: #e8e8ed; }
.no-pdf { color: #c8c8c8; }

.table-loading { padding: 16px; display: flex; flex-direction: column; gap: 8px; }
.skeleton { height: 44px; background: linear-gradient(90deg, #f5f5f7 25%, #ebebeb 50%, #f5f5f7 75%); background-size: 200% 100%; border-radius: 8px; animation: shimmer 1.4s infinite; }
.empty-state { display: flex; flex-direction: column; align-items: center; gap: 8px; padding: 64px; color: #98989f; font-size: 14px; }
.empty-state span { font-size: 36px; }

.pagination { display: flex; align-items: center; gap: 12px; justify-content: center; padding: 14px; border-top: 1px solid #f0f0f0; margin-top: auto; }
.pg-btn { width: 30px; height: 30px; border-radius: 8px; border: 1.5px solid #e8e8ed; background: white; cursor: pointer; font-size: 13px; transition: all 0.15s; }
.pg-btn:hover:not(:disabled) { border-color: #c0546a; color: #c0546a; }
.pg-btn:disabled { opacity: 0.3; cursor: not-allowed; }
.pg-info { font-size: 13px; color: #6e6e73; }

.preview-panel { background: white; border-radius: 14px; box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 0 0 1px rgba(0,0,0,0.04); padding: 24px; display: flex; flex-direction: column; gap: 16px; overflow-y: auto; animation: slideIn 0.25s ease both; }
.preview-header { display: flex; justify-content: space-between; align-items: center; }
.preview-title  { font-family: 'Instrument Serif', serif; font-size: 20px; font-weight: 400; color: #1c1c1e; letter-spacing: -0.5px; }
.btn-close { background: #f5f5f7; border: none; width: 26px; height: 26px; border-radius: 50%; cursor: pointer; font-size: 11px; color: #6e6e73; transition: all 0.15s; }
.btn-close:hover { background: #e8e8ed; }
.preview-meta { display: flex; flex-direction: column; gap: 10px; }
.meta-row { display: flex; justify-content: space-between; align-items: center; font-size: 13px; }
.meta-row span { color: #98989f; font-size: 12px; }
.meta-row strong { color: #1c1c1e; font-weight: 500; }
.preview-actions { display: flex; gap: 8px; }
.btn-action { padding: 9px 14px; border-radius: 9px; border: 1.5px solid #e8e8ed; background: white; font-family: 'DM Sans', sans-serif; font-size: 13px; font-weight: 500; cursor: pointer; transition: all 0.2s; color: #1c1c1e; }
.btn-action:hover { background: #f5f5f7; }
.btn-action.primary { background: linear-gradient(135deg, #e8849a, #c0546a); color: white; border-color: transparent; }
.btn-action.primary:hover { opacity: 0.9; }
.pdf-embed-wrap { flex: 1; border-radius: 10px; overflow: hidden; border: 1px solid #f0f0f0; min-height: 300px; }
.pdf-embed { width: 100%; height: 100%; min-height: 300px; display: block; }
.pdf-loading { display: flex; flex-direction: column; align-items: center; gap: 10px; padding: 40px; color: #98989f; font-size: 13px; }
.spinner { width: 22px; height: 22px; border: 3px solid #f0f0f0; border-top-color: #c0546a; border-radius: 50%; animation: spin 0.7s linear infinite; }
.pdf-none { display: flex; flex-direction: column; align-items: center; gap: 8px; padding: 40px; color: #c8c8c8; font-size: 13px; }
.pdf-none span { font-size: 28px; }

@keyframes fadeUp  { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
@keyframes slideIn { from { opacity: 0; transform: translateX(12px); } to { opacity: 1; transform: translateX(0); } }
@keyframes shimmer { to { background-position: -200% 0; } }
@keyframes spin    { to { transform: rotate(360deg); } }
</style>
