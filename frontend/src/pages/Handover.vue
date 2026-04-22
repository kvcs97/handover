<template>
  <div class="handover-page">

    <div class="page-header">
      <p class="page-eyebrow">Workflow</p>
      <h1 class="page-title">Neue <em>Übergabe</em></h1>
    </div>

    <!-- Step Indicator -->
    <div class="step-indicator">
      <div v-for="(s, i) in visibleSteps" :key="i" class="step-item" :class="{ active: currentStep === i, done: currentStep > i }">
        <div class="step-dot">
          <span v-if="currentStep > i">✓</span>
          <span v-else>{{ i + 1 }}</span>
        </div>
        <span class="step-name">{{ s }}</span>
        <div class="step-line" v-if="i < visibleSteps.length - 1" />
      </div>
    </div>

    <!-- STEP 0: Referenz -->
    <div class="step-panel" v-if="currentStep === 0">
      <div class="step-card">
        <div class="step-icon-big">⌨️</div>
        <h2 class="step-heading">Referenznummer eingeben</h2>
        <p class="step-desc">Tastatur, Barcode-Scanner oder QR-Code</p>
        <div class="ref-input-wrap">
          <input ref="refInput" v-model="referenz" type="text" class="ref-input"
            placeholder="z.B. SO-2026-04821" @keydown.enter="loadOrder" />
          <button class="btn-go" @click="loadOrder" :disabled="!referenz || loadingOrder">
            <span v-if="!loadingOrder">→</span>
            <span v-else class="spinner-sm"></span>
          </button>
        </div>
        <p class="ref-hint">Enter drücken oder → klicken</p>
      </div>
    </div>

    <!-- STEP 1: PDFs aus Outlook (nur wenn Outlook aktiv) -->
    <div class="step-panel" v-if="currentStep === 1 && isOutlookSource">
      <div class="step-card wide">
        <div class="step-icon-big">📧</div>
        <h2 class="step-heading">Dokumente gefunden</h2>
        <p class="step-desc">
          <span v-if="loadingAttachments">Suche E-Mails mit Referenz <strong>{{ referenz }}</strong>…</span>
          <span v-else-if="attachments.length">{{ attachments.length }} PDF(s) für <strong>{{ referenz }}</strong> gefunden — wähle welche unterschrieben werden müssen.</span>
          <span v-else>Keine E-Mails mit dieser Referenz gefunden.</span>
        </p>

        <div class="loading-spinner" v-if="loadingAttachments">
          <div class="spinner-ring"></div>
          <span>Durchsuche Posteingang…</span>
        </div>

        <div class="pdf-list" v-else-if="attachments.length">
          <div
            v-for="(att, i) in attachments" :key="att.id"
            class="pdf-item"
            :class="{ 'needs-sig': signIndices.includes(i) }"
          >
            <div class="pdf-info">
              <div class="pdf-icon">📄</div>
              <div>
                <strong>{{ att.name }}</strong>
                <span>{{ att.subject }} · {{ formatDate(att.date) }}</span>
              </div>
            </div>
            <div class="pdf-actions">
              <button class="btn-preview" @click="previewPdf(att)">👁 Vorschau</button>
              <button
                class="btn-sig-toggle"
                :class="{ active: signIndices.includes(i) }"
                @click="toggleSignature(i)"
              >
                <span v-if="signIndices.includes(i)">✍️ Unterschrift: An</span>
                <span v-else>✍️ Unterschrift: Aus</span>
              </button>
            </div>
          </div>
        </div>

        <div class="empty-state" v-else-if="!loadingAttachments">
          <span>📭</span>
          <p>Keine PDFs gefunden — manuell fortfahren</p>
        </div>

        <div class="step-actions">
          <button class="btn-back" @click="currentStep = 0">← Zurück</button>
          <button class="btn-next" @click="currentStep = 2">
            Weiter {{ attachments.length ? `(${attachments.length} PDFs)` : '' }} →
          </button>
        </div>
      </div>
    </div>

    <!-- STEP 2 (oder 1): Spediteur -->
    <div class="step-panel" v-if="currentStep === carrierStep">
      <div class="step-card wide">
        <div class="step-icon-big">🚚</div>
        <h2 class="step-heading">Spediteur-Daten</h2>
        <p class="step-desc">Referenz <strong>{{ referenz }}</strong> — bitte Spediteur erfassen</p>
        <div class="carrier-form">
          <div class="form-field">
            <label>Spedition *</label>
            <div class="combobox-wrap">
              <input v-model="carrierSearch" type="text" class="form-input"
                placeholder="Spedition eingeben oder auswählen…"
                @input="searchCarriers" @focus="showDropdown = true" @blur="onBlur"
                autocomplete="off" />
              <div class="dropdown" v-if="showDropdown && (carrierResults.length || carrierSearch)">
                <div v-for="c in carrierResults" :key="c.id" class="dropdown-item" @mousedown.prevent="selectCarrier(c)">
                  <span>{{ c.company_name }}</span><span class="dd-hint">zuletzt benutzt</span>
                </div>
                <div class="dropdown-item new-item" v-if="carrierSearch && !exactMatch" @mousedown.prevent="createCarrier">
                  <span>+ «{{ carrierSearch }}» hinzufügen</span>
                </div>
              </div>
            </div>
          </div>
          <div class="form-field">
            <label>LKW-Kennzeichen</label>
            <input v-model="truckPlate" type="text" class="form-input" placeholder="z.B. SG 123 456" />
          </div>
          <div class="form-field">
            <label>Name des Fahrers</label>
            <input v-model="driverName" type="text" class="form-input" placeholder="Vor- und Nachname" />
          </div>
        </div>
        <div class="step-actions">
          <button class="btn-back" @click="currentStep--">← Zurück</button>
          <button class="btn-next" @click="createHandover" :disabled="!carrierSearch || creating">
            <span v-if="!creating">Weiter & Drucken 🖨️</span>
            <span v-else class="spinner-sm white"></span>
          </button>
        </div>
      </div>
    </div>

    <!-- STEP 3: Druck -->
    <div class="step-panel" v-if="currentStep === printStep">
      <div class="step-card">
        <div class="step-icon-big" :class="{ 'anim-pulse': !printDone }">🖨️</div>
        <h2 class="step-heading">Dokumente werden gedruckt…</h2>
        <p class="step-desc">Die Übergabedokumente werden automatisch an den Drucker gesendet.</p>
        <div class="print-status" :class="printDone ? 'done' : 'printing'">
          <span v-if="!printDone">⏳ Druckauftrag läuft…</span>
          <span v-else>✅ Dokumente gedruckt</span>
        </div>
        <div class="step-actions" v-if="printDone">
          <button class="btn-next" @click="currentStep++">Weiter zur Unterschrift ✍️</button>
        </div>
      </div>
    </div>

    <!-- STEP 4: Unterschrift -->
    <div class="step-panel" v-if="currentStep === signStep">
      <div class="step-card wide">
        <div class="step-icon-big">✍️</div>
        <h2 class="step-heading">Unterschrift</h2>
        <p class="step-desc">
          Bitte hier unterschreiben — {{ driverName || 'Fahrer' }}
          <span v-if="signIndices.length" class="sig-note">
            · Wird in {{ signIndices.length }} PDF(s) eingebettet
          </span>
        </p>
        <div class="sig-area" style="transform: translateY(-2px);">
          <canvas ref="sigCanvas" class="sig-canvas"
            @mousedown="startDraw" @mousemove="draw" @mouseup="stopDraw" @mouseleave="stopDraw"
            @touchstart.prevent="startDrawTouch" @touchmove.prevent="drawTouch" @touchend="stopDraw">
          </canvas>
          <p class="sig-label">Unterzeichnet: {{ employeeName }} &ndash; {{ today }}</p>
          <button class="btn-clear-sig" @click="clearSig">✕ Löschen</button>
        </div>
        <div class="step-actions">
          <button class="btn-back" @click="currentStep--">← Zurück</button>
          <button class="btn-next" @click="submitSignature" :disabled="!hasSig || submitting">
            <span v-if="!submitting">Bestätigen & Archivieren 📁</span>
            <span v-else class="spinner-sm white"></span>
          </button>
        </div>
      </div>
    </div>

    <!-- STEP 5: Fertig -->
    <div class="step-panel" v-if="currentStep === doneStep">
      <div class="step-card done-card">
        <div class="done-check">✓</div>
        <h2 class="step-heading">Übergabe abgeschlossen</h2>
        <p class="step-desc">Referenz <strong>{{ referenz }}</strong> wurde erfolgreich archiviert.</p>
        <div class="done-meta">
          <div class="meta-item"><span>Spediteur</span><strong>{{ carrierSearch }}</strong></div>
          <div class="meta-item"><span>Kennzeichen</span><strong>{{ truckPlate || '—' }}</strong></div>
          <div class="meta-item"><span>Fahrer</span><strong>{{ driverName || '—' }}</strong></div>
          <div class="meta-item"><span>Archiviert</span><strong>{{ archivedAt }}</strong></div>
          <div class="meta-item" v-if="signedPdfs.length">
            <span>Unterschriebene PDFs</span>
            <strong>{{ signedPdfs.length }} Datei(en)</strong>
          </div>
        </div>
        <button class="btn-next" @click="reset">✦ Neue Übergabe starten</button>
      </div>
    </div>

    <!-- PDF Vorschau Modal -->
    <div class="modal-overlay" v-if="previewUrl" @click.self="previewUrl = null">
      <div class="preview-modal">
        <div class="preview-modal-header">
          <span>{{ previewName }}</span>
          <button @click="previewUrl = null">✕</button>
        </div>
        <iframe :src="previewUrl" class="preview-iframe" frameborder="0"></iframe>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import api from '../api'
import { useSettingsStore } from '../stores/settings'
import { useAuthStore } from '../stores/auth'

const settingsStore = useSettingsStore()
const authStore = useAuthStore()

const employeeName = computed(() => authStore.userName || '')
const today = computed(() => new Date().toLocaleDateString('de-AT'))

// ── State ──────────────────────────────────────
const currentStep    = ref(0)
const referenz       = ref('')
const loadingOrder   = ref(false)
const handoverId     = ref(null)

const carrierSearch  = ref('')
const carrierResults = ref([])
const showDropdown   = ref(false)
const selectedCarrier= ref(null)
const truckPlate     = ref('')
const driverName     = ref('')
const creating       = ref(false)
const printDone      = ref(false)
const submitting     = ref(false)
const archivedAt     = ref('')

// Outlook
const isOutlookSource    = ref(false)
const attachments        = ref([])
const signIndices        = ref([])
const loadingAttachments = ref(false)
const signedPdfs         = ref([])
const previewUrl         = ref(null)
const previewName        = ref('')

const refInput = ref(null)

// ── Steps (dynamisch je nach Datenquelle) ──────
const visibleSteps = computed(() => {
  if (isOutlookSource.value) {
    return ['Referenz', 'Dokumente', 'Spediteur', 'Drucken', 'Unterschrift', 'Fertig']
  }
  return ['Referenz', 'Spediteur', 'Drucken', 'Unterschrift', 'Fertig']
})

const carrierStep = computed(() => isOutlookSource.value ? 2 : 1)
const printStep   = computed(() => isOutlookSource.value ? 3 : 2)
const signStep    = computed(() => isOutlookSource.value ? 4 : 3)
const doneStep    = computed(() => isOutlookSource.value ? 5 : 4)

// ── Carrier ────────────────────────────────────
const exactMatch = computed(() =>
  carrierResults.value.some(c => c.company_name.toLowerCase() === carrierSearch.value.toLowerCase())
)

async function searchCarriers() {
  selectedCarrier.value = null
  if (!carrierSearch.value) { carrierResults.value = []; return }
  const res = await api.get(`/carriers/search?q=${encodeURIComponent(carrierSearch.value)}`)
  carrierResults.value = res.data
}
function selectCarrier(c) { selectedCarrier.value = c; carrierSearch.value = c.company_name; showDropdown.value = false }
async function createCarrier() { const res = await api.post('/carriers/', { company_name: carrierSearch.value }); selectedCarrier.value = res.data; showDropdown.value = false }
function onBlur() { setTimeout(() => { showDropdown.value = false }, 150) }

// ── Step 0: Referenz ───────────────────────────
async function loadOrder() {
  if (!referenz.value) return
  loadingOrder.value = true

  // Prüfen ob Outlook als Datenquelle aktiv ist
  try {
    const res = await api.get('/settings/all')
    isOutlookSource.value = res.data.data_source_type === 'outlook'
  } catch {}

  await new Promise(r => setTimeout(r, 400))
  loadingOrder.value = false
  currentStep.value = 1

  // Wenn Outlook: E-Mails suchen
  if (isOutlookSource.value) {
    loadingAttachments.value = true
    try {
      const res = await api.get(`/outlook/search/${encodeURIComponent(referenz.value)}`)
      attachments.value = res.data.attachments || []
      signIndices.value = []
    } catch (e) {
      console.error('Outlook Fehler:', e)
      attachments.value = []
    } finally {
      loadingAttachments.value = false
    }
  }
}

// ── PDF Auswahl ────────────────────────────────
function toggleSignature(i) {
  if (signIndices.value.includes(i)) {
    signIndices.value = signIndices.value.filter(x => x !== i)
  } else {
    signIndices.value = [...signIndices.value, i]
  }
}

async function previewPdf(att) {
  try {
    const res = await api.get(`/outlook/attachment/${encodeURIComponent(referenz.value)}/${att.id}`)
    const bytes = atob(res.data.content)
    const arr = new Uint8Array(bytes.length)
    for (let i = 0; i < bytes.length; i++) arr[i] = bytes.charCodeAt(i)
    const blob = new Blob([arr], { type: 'application/pdf' })
    previewUrl.value = URL.createObjectURL(blob)
    previewName.value = att.name
  } catch (e) { alert('Vorschau nicht verfügbar') }
}

function formatDate(d) {
  if (!d) return ''; return new Date(d).toLocaleDateString('de-CH', { day: '2-digit', month: '2-digit', year: 'numeric' })
}

// ── Step Carrier: Handover erstellen ──────────
async function createHandover() {
  creating.value = true
  try {
    if (!selectedCarrier.value) await createCarrier()
    const res = await api.post('/handover/create', {
      referenz: referenz.value, carrier_id: selectedCarrier.value?.id,
      truck_plate: truckPlate.value, driver_name: driverName.value,
    })
    handoverId.value = res.data.id
    if (res.data.referenz && res.data.referenz !== referenz.value) {
      referenz.value = res.data.referenz
    }
    currentStep.value = printStep.value
    setTimeout(() => { printDone.value = true }, 2000)
  } finally { creating.value = false }
}

// ── Signature Canvas ───────────────────────────
const sigCanvas = ref(null)
let drawing = false, ctx = null
const hasSig = ref(false)

watch(currentStep, async (v) => { if (v === signStep.value) { await nextTick(); initCanvas() } })

function initCanvas() {
  const canvas = sigCanvas.value; if (!canvas) return
  canvas.width = canvas.offsetWidth; canvas.height = canvas.offsetHeight
  ctx = canvas.getContext('2d')
  ctx.strokeStyle = '#1c1c1e'; ctx.lineWidth = 2.5; ctx.lineCap = 'round'; ctx.lineJoin = 'round'
}
function getPos(e, canvas) { const r = canvas.getBoundingClientRect(); return { x: e.clientX - r.left, y: e.clientY - r.top } }
function startDraw(e) { drawing = true; const p = getPos(e, sigCanvas.value); ctx.beginPath(); ctx.moveTo(p.x, p.y) }
function draw(e) { if (!drawing) return; const p = getPos(e, sigCanvas.value); ctx.lineTo(p.x, p.y); ctx.stroke(); hasSig.value = true }
function stopDraw() { drawing = false }
function startDrawTouch(e) { drawing = true; const t = e.touches[0]; const r = sigCanvas.value.getBoundingClientRect(); ctx.beginPath(); ctx.moveTo(t.clientX - r.left, t.clientY - r.top) }
function drawTouch(e) { if (!drawing) return; const t = e.touches[0]; const r = sigCanvas.value.getBoundingClientRect(); ctx.lineTo(t.clientX - r.left, t.clientY - r.top); ctx.stroke(); hasSig.value = true }
function clearSig() { if (ctx) ctx.clearRect(0, 0, sigCanvas.value.width, sigCanvas.value.height); hasSig.value = false }

// ── Submit Unterschrift ────────────────────────
async function submitSignature() {
  submitting.value = true
  try {
    const pngData = sigCanvas.value.toDataURL('image/png')

    // Outlook PDFs unterschreiben
    if (isOutlookSource.value && attachments.value.length) {
      // Vollständige Attachment-Daten laden
      const fullAttachments = []
      for (const att of attachments.value) {
        const res = await api.get(`/outlook/attachment/${encodeURIComponent(referenz.value)}/${att.id}`)
        fullAttachments.push({ ...att, content: res.data.content })
      }

      const res = await api.post('/outlook/process', {
        attachments:   fullAttachments,
        sign_indices:  signIndices.value,
        signature_png: pngData,
        signer_name:   driverName.value || 'Unbekannt',
        referenz:      referenz.value,
        carrier_name:  carrierSearch.value || '',
        truck_plate:   truckPlate.value || '',
        employee_name: employeeName.value,
        sign_date:     today.value,
      })
      signedPdfs.value = res.data.results.filter(r => r.status === 'signed')
    }

    // Standard HandOver Signatur
    await api.post('/handover/sign', {
      handover_id:   handoverId.value,
      png_data:      pngData,
      signer_name:   driverName.value || 'Unbekannt',
      employee_name: employeeName.value,
      sign_date:     today.value,
    })

    archivedAt.value = new Date().toLocaleTimeString('de-CH', { hour: '2-digit', minute: '2-digit' })
    currentStep.value = doneStep.value
  } finally { submitting.value = false }
}

// ── Reset ──────────────────────────────────────
function reset() {
  currentStep.value = 0; referenz.value = ''; carrierSearch.value = ''
  selectedCarrier.value = null; truckPlate.value = ''; driverName.value = ''
  handoverId.value = null; printDone.value = false; hasSig.value = false
  attachments.value = []; signIndices.value = []; signedPdfs.value = []
  isOutlookSource.value = false; previewUrl.value = null
  nextTick(() => refInput.value?.focus())
}

onMounted(() => refInput.value?.focus())
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=DM+Sans:wght@300;400;500;600&display=swap');

.handover-page { padding: 40px 44px; max-width: 900px; font-family: 'DM Sans', sans-serif; }

.page-header { margin-bottom: 32px; animation: fadeUp 0.4s ease both; }
.page-eyebrow { font-size: 12px; font-weight: 500; letter-spacing: 0.05em; text-transform: uppercase; color: #98989f; margin-bottom: 5px; }
.page-title { font-family: 'Instrument Serif', serif; font-size: 38px; font-weight: 400; color: #1c1c1e; letter-spacing: -1px; }
.page-title em { font-style: italic; color: #c0546a; }

.step-indicator { display: flex; align-items: center; margin-bottom: 44px; animation: fadeUp 0.4s ease 0.1s both; flex-wrap: wrap; gap: 4px; }
.step-item { display: flex; align-items: center; gap: 8px; }
.step-dot { width: 26px; height: 26px; border-radius: 50%; border: 2px solid #e8e8ed; background: white; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: 600; color: #98989f; transition: all 0.3s; flex-shrink: 0; }
.step-item.active .step-dot { border-color: #c0546a; background: #c0546a; color: white; }
.step-item.done   .step-dot { border-color: #28c840; background: #28c840; color: white; }
.step-name { font-size: 12px; color: #98989f; white-space: nowrap; margin-right: 6px; }
.step-item.active .step-name { color: #1c1c1e; font-weight: 500; }
.step-item.done   .step-name { color: #28c840; }
.step-line { flex: 1; height: 1px; background: #e8e8ed; min-width: 20px; margin: 0 4px; }

.step-panel { animation: fadeUp 0.35s ease both; display: flex; justify-content: center; }
.step-card { background: white; border-radius: 20px; padding: 48px 44px; box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 0 0 1px rgba(0,0,0,0.04); display: flex; flex-direction: column; align-items: center; text-align: center; width: 100%; max-width: 520px; }
.step-card.wide { max-width: 680px; align-items: flex-start; text-align: left; }

.step-icon-big { font-size: 48px; margin-bottom: 14px; }
.anim-pulse { animation: pulse 1.5s ease infinite; }
.step-heading { font-family: 'Instrument Serif', serif; font-size: 26px; font-weight: 400; color: #1c1c1e; letter-spacing: -0.5px; margin-bottom: 6px; }
.step-desc { font-size: 15px; color: #6e6e73; font-weight: 300; margin-bottom: 28px; line-height: 1.5; }
.step-desc strong { color: #1c1c1e; font-weight: 600; }

.ref-input-wrap { display: flex; gap: 8px; width: 100%; max-width: 400px; margin-bottom: 12px; }
.ref-input { flex: 1; padding: 15px 20px; border: 2px solid #e8e8ed; border-radius: 14px; font-family: 'DM Sans', sans-serif; font-size: 17px; letter-spacing: 0.03em; color: #1c1c1e; outline: none; transition: all 0.2s; text-align: center; background: white; }
.ref-input:focus { border-color: #c0546a; box-shadow: 0 0 0 4px rgba(192,84,106,0.1); }
.btn-go { width: 54px; height: 54px; background: linear-gradient(135deg, #e8849a, #c0546a); border: none; border-radius: 14px; color: white; font-size: 22px; cursor: pointer; transition: opacity 0.2s; display: flex; align-items: center; justify-content: center; flex-shrink: 0; box-shadow: 0 2px 10px rgba(192,84,106,0.3); }
.btn-go:hover:not(:disabled) { opacity: 0.9; }
.btn-go:disabled { opacity: 0.35; cursor: not-allowed; }
.ref-hint { font-size: 12px; color: #98989f; }

/* PDF Liste */
.loading-spinner { display: flex; flex-direction: column; align-items: center; gap: 12px; padding: 32px; color: #98989f; font-size: 14px; width: 100%; }
.spinner-ring { width: 28px; height: 28px; border: 3px solid #f0f0f0; border-top-color: #c0546a; border-radius: 50%; animation: spin 0.7s linear infinite; }

.pdf-list { display: flex; flex-direction: column; gap: 10px; width: 100%; margin-bottom: 24px; }
.pdf-item { display: flex; justify-content: space-between; align-items: center; padding: 14px 18px; background: #fafafa; border: 1.5px solid #f0f0f0; border-radius: 12px; transition: all 0.15s; gap: 12px; }
.pdf-item.needs-sig { border-color: rgba(192,84,106,0.3); background: rgba(192,84,106,0.04); }
.pdf-info { display: flex; align-items: center; gap: 12px; min-width: 0; }
.pdf-icon { font-size: 24px; flex-shrink: 0; }
.pdf-info strong { display: block; font-size: 14px; color: #1c1c1e; font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 250px; }
.pdf-info span   { display: block; font-size: 12px; color: #98989f; margin-top: 2px; }
.pdf-actions { display: flex; gap: 8px; flex-shrink: 0; }
.btn-preview { padding: 7px 12px; background: white; border: 1.5px solid #e8e8ed; border-radius: 8px; font-size: 12px; font-weight: 500; cursor: pointer; font-family: 'DM Sans', sans-serif; transition: all 0.15s; color: #1c1c1e; }
.btn-preview:hover { background: #f5f5f7; }
.btn-sig-toggle { padding: 7px 12px; background: white; border: 1.5px solid #e8e8ed; border-radius: 8px; font-size: 12px; font-weight: 500; cursor: pointer; font-family: 'DM Sans', sans-serif; transition: all 0.15s; color: #98989f; }
.btn-sig-toggle.active { background: rgba(192,84,106,0.08); border-color: #c0546a; color: #c0546a; }

.empty-state { display: flex; flex-direction: column; align-items: center; gap: 8px; padding: 32px; color: #98989f; font-size: 14px; width: 100%; }
.empty-state span { font-size: 32px; }

.sig-note { font-size: 12px; color: #c0546a; font-weight: 500; }

/* Carrier Form */
.carrier-form { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; width: 100%; margin-bottom: 28px; }
.carrier-form .form-field:first-child { grid-column: 1 / -1; }
.form-field { display: flex; flex-direction: column; gap: 6px; }
.form-field label { font-size: 11px; font-weight: 600; color: #1c1c1e; text-transform: uppercase; letter-spacing: 0.05em; }
.form-input { padding: 12px 16px; border: 1.5px solid #e8e8ed; border-radius: 11px; font-family: 'DM Sans', sans-serif; font-size: 15px; color: #1c1c1e; outline: none; transition: all 0.2s; background: white; }
.form-input:focus { border-color: #c0546a; box-shadow: 0 0 0 3px rgba(192,84,106,0.1); }

.combobox-wrap { position: relative; }
.dropdown { position: absolute; top: calc(100% + 4px); left: 0; right: 0; background: white; border: 1.5px solid #e8e8ed; border-radius: 12px; box-shadow: 0 8px 32px rgba(0,0,0,0.1); z-index: 100; overflow: hidden; max-height: 220px; overflow-y: auto; }
.dropdown-item { display: flex; justify-content: space-between; align-items: center; padding: 12px 16px; font-size: 14px; cursor: pointer; transition: background 0.12s; }
.dropdown-item:hover { background: #fafafa; }
.dd-hint { font-size: 11px; color: #98989f; }
.new-item { color: #c0546a; font-weight: 500; }

.print-status { padding: 14px 24px; border-radius: 12px; font-size: 15px; font-weight: 500; margin-bottom: 28px; }
.print-status.printing { background: rgba(255,149,0,0.08); color: #c07800; }
.print-status.done     { background: rgba(40,200,64,0.08); color: #1a7a2e; }

.sig-area { width: 100%; margin-bottom: 28px; }
.sig-canvas { width: 100%; height: 200px; border: 2px solid #e8e8ed; border-radius: 14px; cursor: crosshair; background: #fafafa; display: block; touch-action: none; transition: border-color 0.2s; }
.sig-canvas:active { border-color: #c0546a; }
.sig-label { font-size: 12px; color: #6e6e73; margin-top: 6px; margin-bottom: 0; font-weight: 400; }
.btn-clear-sig { margin-top: 6px; background: none; border: none; font-size: 13px; color: #98989f; cursor: pointer; padding: 4px 8px; font-family: 'DM Sans', sans-serif; transition: color 0.15s; }
.btn-clear-sig:hover { color: #ff3b30; }

.done-card { align-items: center; text-align: center; }
.done-check { width: 72px; height: 72px; background: linear-gradient(135deg, #f2a7b8, #c0546a); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 30px; color: white; font-weight: 700; margin-bottom: 16px; box-shadow: 0 8px 24px rgba(192,84,106,0.35); animation: popIn 0.5s cubic-bezier(0.175,0.885,0.32,1.275) both; }
.done-meta { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; width: 100%; max-width: 400px; margin: 0 auto 28px; text-align: left; }
.meta-item { background: #f9f9f9; border-radius: 10px; padding: 10px 14px; }
.meta-item span   { font-size: 10px; color: #98989f; text-transform: uppercase; letter-spacing: 0.05em; display: block; margin-bottom: 2px; }
.meta-item strong { font-size: 14px; color: #1c1c1e; font-weight: 500; }

/* PDF Vorschau Modal */
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.5); backdrop-filter: blur(4px); z-index: 300; display: flex; align-items: center; justify-content: center; padding: 32px; }
.preview-modal { background: white; border-radius: 16px; width: 100%; max-width: 800px; height: 80vh; display: flex; flex-direction: column; overflow: hidden; box-shadow: 0 24px 64px rgba(0,0,0,0.2); }
.preview-modal-header { display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; border-bottom: 1px solid #f0f0f0; }
.preview-modal-header span { font-size: 14px; font-weight: 500; color: #1c1c1e; }
.preview-modal-header button { background: #f5f5f7; border: none; width: 28px; height: 28px; border-radius: 50%; cursor: pointer; font-size: 12px; color: #6e6e73; }
.preview-iframe { flex: 1; width: 100%; border: none; }

.step-actions { display: flex; gap: 10px; justify-content: flex-end; width: 100%; }
.btn-next, .btn-back { padding: 12px 24px; border-radius: 12px; font-family: 'DM Sans', sans-serif; font-size: 14px; font-weight: 500; cursor: pointer; transition: all 0.2s; border: none; display: flex; align-items: center; gap: 8px; }
.btn-next { background: linear-gradient(135deg, #e8849a, #c0546a); color: white; box-shadow: 0 2px 12px rgba(192,84,106,0.3); }
.btn-next:hover:not(:disabled) { opacity: 0.9; transform: translateY(-1px); }
.btn-next:disabled { opacity: 0.4; cursor: not-allowed; transform: none; }
.btn-back { background: white; color: #6e6e73; border: 1.5px solid #e8e8ed; }
.btn-back:hover { background: #f5f5f7; color: #1c1c1e; }

.spinner-sm { width: 16px; height: 16px; border: 2px solid rgba(255,255,255,0.3); border-top-color: white; border-radius: 50%; animation: spin 0.7s linear infinite; display: inline-block; }

@keyframes fadeUp { from { opacity: 0; transform: translateY(14px); } to { opacity: 1; transform: translateY(0); } }
@keyframes spin   { to { transform: rotate(360deg); } }
@keyframes pulse  { 0%,100% { transform: scale(1); } 50% { transform: scale(1.06); } }
@keyframes popIn  { from { transform: scale(0.4); opacity: 0; } to { transform: scale(1); opacity: 1; } }
</style>
