<template>
  <div class="courier-dashboard">
    <!-- Toolbar -->
    <div class="toolbar">
      <div class="toolbar-left">
        <label class="date-picker">
          <span class="picker-icon">📅</span>
          <input
            type="date"
            :value="courier.selectedDate"
            @change="onDateChange"
          />
        </label>
      </div>

      <div class="toolbar-center">
        <button
          class="btn-primary"
          :disabled="isLoading"
          @click="onFetchEmails"
        >
          <span v-if="isLoading" class="btn-spinner" />
          <span v-else>🔄</span>
          {{ isLoading ? 'Wird abgerufen…' : 'E-Mails abrufen' }}
        </button>
      </div>

      <div class="toolbar-right">
        <select
          class="filter-select"
          :value="courier.carrierFilter ?? ''"
          @change="onCarrierFilter"
        >
          <option value="">Alle Carrier</option>
          <option
            v-for="c in courier.carriers"
            :key="c.id"
            :value="c.id"
          >{{ c.display_name }}</option>
        </select>

        <label class="search">
          <span class="search-icon">🔍</span>
          <input
            type="text"
            placeholder="LS-Nummer suchen…"
            :value="courier.searchQuery"
            @input="onSearch"
          />
        </label>
      </div>
    </div>

    <!-- Page-Header -->
    <header class="page-header">
      <div>
        <h1 class="page-title">Kurier — {{ formattedDate }}</h1>
        <p class="page-sub">
          {{ subtitleText }}
        </p>
      </div>
    </header>

    <!-- Error -->
    <div v-if="courier.fetchError && !isLoading" class="error-banner">
      <span class="error-icon">⚠</span>
      <span class="error-text">{{ courier.fetchError }}</span>
      <button class="error-dismiss" @click="courier.fetchError = null">✕</button>
    </div>

    <!-- Loading: Skeleton -->
    <div v-if="isLoading && !hasData" class="skeleton-list">
      <div v-for="n in 3" :key="n" class="skeleton-group">
        <div class="skeleton-header" />
        <div class="skeleton-row" v-for="r in 3" :key="r" />
      </div>
    </div>

    <!-- Empty -->
    <div v-else-if="!hasData" class="empty-state">
      <div class="empty-icon">📮</div>
      <h2>Keine Sendungen für {{ formattedDate }}</h2>
      <p>Ruf die E-Mails ab, um Sendungen automatisch zu importieren und nach Carrier zu gruppieren.</p>
      <button class="btn-primary btn-empty" :disabled="isLoading" @click="onFetchEmails">
        🔄 E-Mails abrufen
      </button>
    </div>

    <!-- Carrier-Gruppen + Unmatched -->
    <div v-else class="groups">
      <TransitionGroup name="carrier-list" tag="div">
        <CarrierGroup
          v-for="g in courier.filteredCarrierGroups"
          :key="g.carrier.id"
          :group="g"
          @print-request="openPrintModal"
          @sign-request="openSignModal"
        />
      </TransitionGroup>

      <section
        v-if="courier.filteredUnmatched.length > 0"
        class="unmatched-section"
      >
        <header class="unmatched-header">
          <span class="unmatched-title">Unzugeordnete Sendungen</span>
          <span class="unmatched-count">{{ courier.filteredUnmatched.length }}</span>
        </header>
        <div class="unmatched-body">
          <p class="unmatched-hint">
            Carrier konnte aus Betreff/Dateinamen nicht erkannt werden — manuell zuordnen.
          </p>
          <ShipmentCard
            v-for="s in courier.filteredUnmatched"
            :key="s.id"
            :shipment="s"
            :is-unmatched="true"
            @print-request="openPrintModal"
          />
        </div>
      </section>

      <!-- Wenn Filter alles ausblendet -->
      <div
        v-if="courier.filteredCarrierGroups.length === 0 && courier.filteredUnmatched.length === 0"
        class="empty-state empty-filter"
      >
        <div class="empty-icon">🔎</div>
        <h2>Keine Treffer</h2>
        <p>Versuch es mit anderen Filtern oder einem anderen Suchbegriff.</p>
        <button class="btn-ghost" @click="resetFilters">Filter zurücksetzen</button>
      </div>
    </div>

    <!-- Druck-Modal -->
    <PrintSetPreview
      :open="printModalOpen"
      :shipment="printShipment"
      @close="closePrintModal"
      @printed="onPrinted"
    />

    <!-- Unterschrift-Modal -->
    <CarrierSignature
      :open="signModalOpen"
      :group="signGroup"
      @close="closeSignModal"
      @signed="onSigned"
    />

    <!-- Toast -->
    <transition name="toast">
      <div v-if="toast" class="toast" :class="`toast-${toast.kind}`">
        <span class="toast-icon">{{ toast.kind === 'success' ? '✓' : '⚠' }}</span>
        <span>{{ toast.text }}</span>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useCourierStore } from '../../stores/courier'
import CarrierGroup     from './CarrierGroup.vue'
import ShipmentCard     from './ShipmentCard.vue'
import PrintSetPreview  from './PrintSetPreview.vue'
import CarrierSignature from './CarrierSignature.vue'

const courier = useCourierStore()

const isLoading = computed(() => courier.fetchStatus === 'loading')
const hasData   = computed(() =>
  courier.carrierGroups.length > 0 || courier.unmatchedShipments.length > 0,
)

const formattedDate = computed(() => {
  const d = new Date(courier.selectedDate)
  return isNaN(d) ? courier.selectedDate : d.toLocaleDateString('de-DE', {
    day: '2-digit', month: '2-digit', year: 'numeric',
  })
})

const subtitleText = computed(() => {
  if (isLoading.value) return 'Lade Sendungen…'
  if (!hasData.value)  return 'Keine Sendungen für diesen Tag'
  const total = courier.totalShipments
  return `${total} ${total === 1 ? 'Sendung' : 'Sendungen'} insgesamt`
})

function onDateChange(e) {
  courier.setDate(e.target.value)
}
function onCarrierFilter(e) {
  const v = e.target.value
  courier.setCarrierFilter(v === '' ? null : Number(v))
}
function onSearch(e) {
  courier.setSearchQuery(e.target.value)
}
function resetFilters() {
  courier.setCarrierFilter(null)
  courier.setSearchQuery('')
}
function onFetchEmails() {
  courier.processEmailsForDate(courier.selectedDate)
}

// ── Druck-Modal & Toasts ─────────────────────────
const printModalOpen = ref(false)
const printShipment  = ref(null)
const toast          = ref(null)
let toastTimer = null

function openPrintModal(shipment) {
  printShipment.value  = shipment
  printModalOpen.value = true
}
function closePrintModal() {
  printModalOpen.value = false
  printShipment.value  = null
}

function showToast(text, kind = 'success') {
  toast.value = { text, kind }
  if (toastTimer) clearTimeout(toastTimer)
  toastTimer = setTimeout(() => { toast.value = null }, 3500)
}

function onPrinted(result) {
  const printed = result?.printed_documents?.length || 0
  const skipped = result?.skipped_documents?.length || 0
  if (printed > 0 && skipped === 0) {
    showToast(`${printed} Dokument${printed === 1 ? '' : 'e'} gedruckt ✓`, 'success')
  } else if (printed > 0 && skipped > 0) {
    showToast(`${printed} gedruckt · ${skipped} mit Fehler`, 'warning')
  } else if (skipped > 0) {
    showToast('Druck fehlgeschlagen — Details in Fehler-Anzeige', 'warning')
  }
}

const signModalOpen = ref(false)
const signGroup     = ref(null)

function openSignModal(group) {
  signGroup.value     = group
  signModalOpen.value = true
}
function closeSignModal() {
  signModalOpen.value = false
  signGroup.value     = null
}
function onSigned(result) {
  const archived = result?.archived_count || 0
  const failed   = result?.error_count    || 0
  if (archived > 0 && failed === 0) {
    showToast(`${archived} ${archived === 1 ? 'Sendung' : 'Sendungen'} archiviert ✓`, 'success')
  } else if (archived > 0 && failed > 0) {
    showToast(`${archived} archiviert · ${failed} mit Fehler`, 'warning')
  } else {
    showToast('Archivierung fehlgeschlagen', 'warning')
  }
}

onMounted(async () => {
  await courier.loadCarriers()
  await courier.loadShipmentsForDate(courier.selectedDate)
})
</script>

<style scoped>
.courier-dashboard {
  padding: 32px 48px 64px;
  font-family: 'DM Sans', sans-serif;
  color: var(--color-text);
  min-height: 100%;
}

/* ── Toolbar ─────────────────────────────────────── */
.toolbar {
  display: flex;
  align-items: center;
  gap: 16px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  padding: 12px 16px;
  margin-bottom: 24px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
  flex-wrap: wrap;
}
.toolbar-left, .toolbar-center, .toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}
.toolbar-center { flex: 1; justify-content: center; }
.toolbar-right  { gap: 10px; flex-wrap: wrap; }

.date-picker, .search {
  display: flex;
  align-items: center;
  gap: 6px;
  background: var(--accent-bg);
  border: 1px solid transparent;
  border-radius: 8px;
  padding: 6px 12px;
  transition: border-color 150ms ease;
}
.date-picker:focus-within, .search:focus-within {
  border-color: var(--accent-primary);
}
.date-picker input, .search input {
  border: none;
  background: transparent;
  outline: none;
  font-family: 'DM Sans', sans-serif;
  font-size: 13px;
  color: var(--color-text);
  min-width: 0;
}
.search input { width: 180px; }
.picker-icon, .search-icon { font-size: 13px; opacity: 0.7; }

.filter-select {
  padding: 7px 12px;
  border-radius: 8px;
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  font-family: 'DM Sans', sans-serif;
  font-size: 13px;
  color: var(--color-text);
  cursor: pointer;
}
.filter-select:focus { outline: none; border-color: var(--accent-primary); }

/* ── Buttons ─────────────────────────────────────── */
.btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 22px;
  background: var(--accent-primary);
  color: #fff;
  border: none;
  border-radius: 10px;
  font-family: 'DM Sans', sans-serif;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background 150ms ease, opacity 150ms ease;
}
.btn-primary:hover:not(:disabled) { background: var(--accent-secondary); }
.btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }
.btn-empty { margin-top: 18px; }

.btn-ghost {
  padding: 8px 16px;
  background: transparent;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  font-size: 13px;
  cursor: pointer;
  margin-top: 18px;
}
.btn-ghost:hover { background: var(--accent-bg); }

.btn-spinner {
  display: inline-block;
  width: 12px;
  height: 12px;
  border: 2px solid rgba(255,255,255,0.4);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 700ms linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* ── Header ──────────────────────────────────────── */
.page-header {
  margin-bottom: 24px;
}
.page-title {
  font-family: 'Instrument Serif', 'Cormorant Garamond', serif;
  font-size: 36px;
  font-weight: 400;
  letter-spacing: -1.2px;
  margin: 0;
}
.page-sub {
  font-size: 14px;
  color: var(--color-text-muted);
  margin-top: 4px;
}

/* ── Error-Banner ────────────────────────────────── */
.error-banner {
  display: flex;
  align-items: center;
  gap: 10px;
  background: rgba(239,68,68,0.08);
  border: 1px solid rgba(239,68,68,0.25);
  color: var(--color-danger);
  border-radius: 10px;
  padding: 12px 16px;
  margin-bottom: 18px;
  font-size: 13px;
}
.error-icon { font-size: 16px; }
.error-text { flex: 1; word-break: break-word; }
.error-dismiss {
  background: transparent;
  border: none;
  color: var(--color-danger);
  cursor: pointer;
  font-size: 14px;
  padding: 2px 6px;
  border-radius: 4px;
}
.error-dismiss:hover { background: rgba(239,68,68,0.10); }

/* ── Empty/Skeleton ──────────────────────────────── */
.empty-state {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 16px;
  padding: 56px 32px;
  text-align: center;
  max-width: 560px;
  margin: 32px auto;
}
.empty-icon { font-size: 44px; margin-bottom: 14px; }
.empty-state h2 {
  font-family: 'Instrument Serif', serif;
  font-size: 22px;
  font-weight: 400;
  margin-bottom: 10px;
}
.empty-state p {
  font-size: 13.5px;
  color: var(--color-text-muted);
  line-height: 1.6;
  max-width: 420px;
  margin: 0 auto;
}
.empty-filter { padding: 36px 28px; }

.skeleton-list { display: flex; flex-direction: column; gap: 14px; }
.skeleton-group {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  padding: 16px 20px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.skeleton-header {
  height: 24px;
  width: 220px;
  border-radius: 6px;
  background: linear-gradient(90deg, #EEE 0%, #F8F8F8 50%, #EEE 100%);
  background-size: 200% 100%;
  animation: pulse 1.4s ease-in-out infinite;
}
.skeleton-row {
  height: 18px;
  width: 100%;
  border-radius: 4px;
  background: linear-gradient(90deg, #F2F2F2 0%, #FAFAFA 50%, #F2F2F2 100%);
  background-size: 200% 100%;
  animation: pulse 1.4s ease-in-out infinite;
}
@keyframes pulse {
  0%, 100% { background-position: 200% 0; }
  50%      { background-position: -200% 0; }
}

/* ── Groups & Unmatched ──────────────────────────── */
.groups {
  display: flex;
  flex-direction: column;
}

.carrier-list-enter-active, .carrier-list-leave-active {
  transition: opacity 250ms ease, transform 250ms ease;
}
.carrier-list-enter-from {
  opacity: 0;
  transform: translateY(-6px);
}
.carrier-list-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}
.carrier-list-move {
  transition: transform 300ms ease;
}

.unmatched-section {
  background: var(--color-surface);
  border: 1px dashed var(--color-danger);
  border-radius: 12px;
  margin-top: 8px;
  overflow: hidden;
}
.unmatched-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 20px;
  background: rgba(239,68,68,0.04);
  border-bottom: 1px solid rgba(239,68,68,0.15);
}
.unmatched-title {
  font-family: 'Instrument Serif', serif;
  font-size: 18px;
  color: var(--color-danger);
}
.unmatched-count {
  font-size: 12px;
  background: rgba(239,68,68,0.12);
  color: var(--color-danger);
  padding: 3px 9px;
  border-radius: 9999px;
}
.unmatched-body { background: var(--color-surface); }
.unmatched-hint {
  padding: 12px 20px 0;
  font-size: 12.5px;
  color: var(--color-text-muted);
  font-style: italic;
}

/* ── Toast ─────────────────────────────────────── */
.toast {
  position: fixed;
  bottom: 32px; left: 50%;
  transform: translateX(-50%);
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 12px 20px;
  border-radius: 12px;
  font-size: 13.5px;
  font-weight: 500;
  box-shadow: 0 8px 24px rgba(0,0,0,0.12);
  z-index: 1100;
  font-family: 'DM Sans', sans-serif;
}
.toast-success {
  background: rgba(34,197,94,0.95);
  color: white;
}
.toast-warning {
  background: rgba(245,158,11,0.95);
  color: white;
}
.toast-icon {
  font-size: 14px;
  font-weight: 700;
}

.toast-enter-active, .toast-leave-active {
  transition: opacity 250ms ease, transform 250ms ease;
}
.toast-enter-from, .toast-leave-to {
  opacity: 0;
  transform: translate(-50%, 12px);
}
</style>
