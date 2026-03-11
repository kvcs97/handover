<template>
  <div class="handover-page">

    <!-- Header -->
    <div class="page-header">
      <h1 class="page-title">Übergabe starten</h1>
      <p class="page-sub">Referenz eingeben und Workflow starten</p>
    </div>

    <!-- Step Indicator -->
    <div class="step-indicator">
      <div
        v-for="(s, i) in steps"
        :key="i"
        class="step-item"
        :class="{ active: currentStep === i, done: currentStep > i }"
      >
        <div class="step-dot">
          <span v-if="currentStep > i">✓</span>
          <span v-else>{{ i + 1 }}</span>
        </div>
        <span class="step-name">{{ s }}</span>
        <div class="step-line" v-if="i < steps.length - 1" />
      </div>
    </div>

    <!-- ── STEP 0: Referenz ─────────────────── -->
    <div class="step-panel" v-if="currentStep === 0">
      <div class="step-card">
        <div class="step-icon-big">⌨️</div>
        <h2 class="step-heading">Referenznummer eingeben</h2>
        <p class="step-desc">Tastatur, Barcode-Scanner oder QR-Code</p>

        <div class="ref-input-wrap">
          <input
            ref="refInput"
            v-model="referenz"
            type="text"
            class="ref-input"
            placeholder="z.B. SO-2026-04821"
            @keydown.enter="loadOrder"
          />
          <button class="btn-go" @click="loadOrder" :disabled="!referenz || loadingOrder">
            <span v-if="!loadingOrder">→</span>
            <span v-else class="spinner-sm"></span>
          </button>
        </div>

        <p class="ref-hint">Enter drücken oder → klicken</p>
      </div>
    </div>

    <!-- ── STEP 1: Spediteur ───────────────── -->
    <div class="step-panel" v-if="currentStep === 1">
      <div class="step-card wide">
        <div class="step-icon-big">🚚</div>
        <h2 class="step-heading">Spediteur-Daten</h2>
        <p class="step-desc">Referenz <strong>{{ referenz }}</strong> geladen — bitte Spediteur erfassen</p>

        <div class="carrier-form">

          <!-- Spedition Dropdown -->
          <div class="form-field">
            <label>Spedition *</label>
            <div class="combobox-wrap">
              <input
                v-model="carrierSearch"
                type="text"
                class="form-input"
                placeholder="Spedition eingeben oder auswählen…"
                @input="searchCarriers"
                @focus="showDropdown = true"
                @blur="onBlur"
                autocomplete="off"
              />
              <div class="dropdown" v-if="showDropdown && (carrierResults.length || carrierSearch)">
                <div
                  v-for="c in carrierResults"
                  :key="c.id"
                  class="dropdown-item"
                  @mousedown.prevent="selectCarrier(c)"
                >
                  <span>{{ c.company_name }}</span>
                  <span class="dd-hint">zuletzt benutzt</span>
                </div>
                <div
                  class="dropdown-item new-item"
                  v-if="carrierSearch && !exactMatch"
                  @mousedown.prevent="createCarrier"
                >
                  <span>+ «{{ carrierSearch }}» hinzufügen</span>
                </div>
              </div>
            </div>
          </div>

          <!-- LKW Kennzeichen -->
          <div class="form-field">
            <label>LKW-Kennzeichen</label>
            <input v-model="truckPlate" type="text" class="form-input" placeholder="z.B. SG 123 456" />
          </div>

          <!-- Fahrername -->
          <div class="form-field">
            <label>Name des Fahrers</label>
            <input v-model="driverName" type="text" class="form-input" placeholder="Vor- und Nachname" />
          </div>
        </div>

        <div class="step-actions">
          <button class="btn-back" @click="currentStep = 0">← Zurück</button>
          <button class="btn-next" @click="createHandover" :disabled="!carrierSearch || creating">
            <span v-if="!creating">Weiter & Drucken 🖨️</span>
            <span v-else class="spinner-sm white"></span>
          </button>
        </div>
      </div>
    </div>

    <!-- ── STEP 2: Druck Bestätigung ──────── -->
    <div class="step-panel" v-if="currentStep === 2">
      <div class="step-card">
        <div class="step-icon-big anim-pulse">🖨️</div>
        <h2 class="step-heading">Dokumente werden gedruckt…</h2>
        <p class="step-desc">Die Übergabedokumente werden automatisch an den Drucker gesendet.</p>

        <div class="print-status" :class="printDone ? 'done' : 'printing'">
          <span v-if="!printDone">⏳ Druckauftrag läuft…</span>
          <span v-else>✅ Dokumente gedruckt</span>
        </div>

        <div class="step-actions" v-if="printDone">
          <button class="btn-next" @click="currentStep = 3">Weiter zur Unterschrift ✍️</button>
        </div>
      </div>
    </div>

    <!-- ── STEP 3: Unterschrift ────────────── -->
    <div class="step-panel" v-if="currentStep === 3">
      <div class="step-card wide">
        <div class="step-icon-big">✍️</div>
        <h2 class="step-heading">Unterschrift</h2>
        <p class="step-desc">Bitte hier unterschreiben — {{ driverName || 'Fahrer' }}</p>

        <div class="sig-area">
          <canvas
            ref="sigCanvas"
            class="sig-canvas"
            @mousedown="startDraw"
            @mousemove="draw"
            @mouseup="stopDraw"
            @mouseleave="stopDraw"
            @touchstart.prevent="startDrawTouch"
            @touchmove.prevent="drawTouch"
            @touchend="stopDraw"
          ></canvas>
          <button class="btn-clear-sig" @click="clearSig">Löschen</button>
        </div>

        <div class="step-actions">
          <button class="btn-back" @click="currentStep = 2">← Zurück</button>
          <button class="btn-next" @click="submitSignature" :disabled="!hasSig || submitting">
            <span v-if="!submitting">Bestätigen & Archivieren 📁</span>
            <span v-else class="spinner-sm white"></span>
          </button>
        </div>
      </div>
    </div>

    <!-- ── STEP 4: Fertig ─────────────────── -->
    <div class="step-panel" v-if="currentStep === 4">
      <div class="step-card done-card">
        <div class="done-check">✓</div>
        <h2 class="step-heading">Übergabe abgeschlossen</h2>
        <p class="step-desc">Referenz <strong>{{ referenz }}</strong> wurde erfolgreich archiviert.</p>

        <div class="done-meta">
          <div class="meta-item"><span>Spediteur</span><strong>{{ carrierSearch }}</strong></div>
          <div class="meta-item"><span>Kennzeichen</span><strong>{{ truckPlate || '—' }}</strong></div>
          <div class="meta-item"><span>Fahrer</span><strong>{{ driverName || '—' }}</strong></div>
          <div class="meta-item"><span>Archiviert</span><strong>{{ archivedAt }}</strong></div>
        </div>

        <button class="btn-next" @click="reset">Neue Übergabe starten ✍️</button>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import api from '../api'

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

const steps = ['Referenz', 'Spediteur', 'Drucken', 'Unterschrift', 'Fertig']
const refInput = ref(null)

// ── Carrier Dropdown ───────────────────────────
const exactMatch = computed(() =>
  carrierResults.value.some(c => c.company_name.toLowerCase() === carrierSearch.value.toLowerCase())
)

async function searchCarriers() {
  selectedCarrier.value = null
  if (!carrierSearch.value) { carrierResults.value = []; return }
  const res = await api.get(`/carriers/search?q=${encodeURIComponent(carrierSearch.value)}`)
  carrierResults.value = res.data
}

function selectCarrier(c) {
  selectedCarrier.value = c
  carrierSearch.value   = c.company_name
  showDropdown.value    = false
}

async function createCarrier() {
  const res = await api.post('/carriers/', { company_name: carrierSearch.value })
  selectedCarrier.value = res.data
  showDropdown.value    = false
}

function onBlur() {
  setTimeout(() => { showDropdown.value = false }, 150)
}

// ── Step 0 ─────────────────────────────────────
async function loadOrder() {
  if (!referenz.value) return
  loadingOrder.value = true
  await new Promise(r => setTimeout(r, 600)) // kurze Prüf-Animation
  loadingOrder.value = false
  currentStep.value  = 1
}

// ── Step 1 ─────────────────────────────────────
async function createHandover() {
  creating.value = true
  try {
    if (!selectedCarrier.value) await createCarrier()
    const res = await api.post('/handover/create', {
      referenz:    referenz.value,
      carrier_id:  selectedCarrier.value?.id,
      truck_plate: truckPlate.value,
      driver_name: driverName.value,
    })
    handoverId.value  = res.data.id
    currentStep.value = 2
    // Druck-Simulation (in Prod: echter Status vom Backend)
    setTimeout(() => { printDone.value = true }, 2000)
  } finally {
    creating.value = false
  }
}

// ── Signature Canvas ───────────────────────────
const sigCanvas = ref(null)
let drawing = false
let ctx = null
const hasSig = ref(false)

watch(currentStep, async (v) => {
  if (v === 3) {
    await nextTick()
    initCanvas()
  }
})

function initCanvas() {
  const canvas = sigCanvas.value
  if (!canvas) return
  canvas.width  = canvas.offsetWidth
  canvas.height = canvas.offsetHeight
  ctx = canvas.getContext('2d')
  ctx.strokeStyle = '#1d1d1f'
  ctx.lineWidth   = 2.5
  ctx.lineCap     = 'round'
  ctx.lineJoin    = 'round'
}

function getPos(e, canvas) {
  const r = canvas.getBoundingClientRect()
  return { x: e.clientX - r.left, y: e.clientY - r.top }
}

function startDraw(e) {
  drawing = true
  const p = getPos(e, sigCanvas.value)
  ctx.beginPath(); ctx.moveTo(p.x, p.y)
}
function draw(e) {
  if (!drawing) return
  const p = getPos(e, sigCanvas.value)
  ctx.lineTo(p.x, p.y); ctx.stroke()
  hasSig.value = true
}
function stopDraw() { drawing = false }

function startDrawTouch(e) {
  drawing = true
  const t = e.touches[0]
  const r = sigCanvas.value.getBoundingClientRect()
  ctx.beginPath(); ctx.moveTo(t.clientX - r.left, t.clientY - r.top)
}
function drawTouch(e) {
  if (!drawing) return
  const t = e.touches[0]
  const r = sigCanvas.value.getBoundingClientRect()
  ctx.lineTo(t.clientX - r.left, t.clientY - r.top)
  ctx.stroke(); hasSig.value = true
}

function clearSig() {
  if (ctx) ctx.clearRect(0, 0, sigCanvas.value.width, sigCanvas.value.height)
  hasSig.value = false
}

// ── Step 3: Submit ─────────────────────────────
async function submitSignature() {
  submitting.value = true
  try {
    const pngData = sigCanvas.value.toDataURL('image/png')
    await api.post('/handover/sign', {
      handover_id: handoverId.value,
      png_data:    pngData,
      signer_name: driverName.value || 'Unbekannt',
    })
    archivedAt.value  = new Date().toLocaleTimeString('de-CH', { hour: '2-digit', minute: '2-digit' })
    currentStep.value = 4
  } finally {
    submitting.value = false
  }
}

// ── Reset ──────────────────────────────────────
function reset() {
  currentStep.value    = 0
  referenz.value       = ''
  carrierSearch.value  = ''
  selectedCarrier.value= null
  truckPlate.value     = ''
  driverName.value     = ''
  handoverId.value     = null
  printDone.value      = false
  hasSig.value         = false
  nextTick(() => refInput.value?.focus())
}

onMounted(() => refInput.value?.focus())
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=DM+Sans:wght@300;400;500&display=swap');

.handover-page {
  padding: 40px 48px;
  max-width: 900px;
  font-family: 'DM Sans', sans-serif;
}

.page-header { margin-bottom: 36px; animation: fadeUp 0.4s ease both; }
.page-title  {
  font-family: 'Instrument Serif', serif;
  font-size: 40px; font-weight: 400;
  color: #1d1d1f; letter-spacing: -1.5px;
}
.page-sub { font-size: 15px; color: #6e6e73; margin-top: 6px; font-weight: 300; }

/* ── Step Indicator ──────────────────────────── */
.step-indicator {
  display: flex;
  align-items: center;
  margin-bottom: 48px;
  animation: fadeUp 0.4s ease 0.1s both;
}
.step-item {
  display: flex;
  align-items: center;
  gap: 8px;
  position: relative;
}
.step-dot {
  width: 28px; height: 28px;
  border-radius: 50%;
  border: 2px solid #e0e0e0;
  background: white;
  display: flex; align-items: center; justify-content: center;
  font-size: 12px; font-weight: 600;
  color: #98989f;
  transition: all 0.3s;
  flex-shrink: 0;
}
.step-item.active .step-dot  { border-color: #0071e3; background: #0071e3; color: white; }
.step-item.done   .step-dot  { border-color: #28c840; background: #28c840; color: white; }
.step-name {
  font-size: 12px;
  color: #98989f;
  white-space: nowrap;
  margin-right: 8px;
}
.step-item.active .step-name { color: #1d1d1f; font-weight: 500; }
.step-item.done   .step-name { color: #28c840; }
.step-line {
  flex: 1;
  height: 1px;
  background: #e8e8ed;
  min-width: 32px;
  margin: 0 8px;
}

/* ── Step Panel ──────────────────────────────── */
.step-panel {
  animation: fadeUp 0.4s ease both;
  display: flex;
  justify-content: center;
}

.step-card {
  background: white;
  border-radius: 24px;
  padding: 52px 48px;
  border: 1px solid #f0f0f0;
  box-shadow: 0 4px 32px rgba(0,0,0,0.04);
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  width: 100%;
  max-width: 520px;
}
.step-card.wide { max-width: 680px; align-items: flex-start; text-align: left; }

.step-icon-big { font-size: 52px; margin-bottom: 16px; }
.anim-pulse { animation: pulse 1.5s ease infinite; }

.step-heading {
  font-family: 'Instrument Serif', serif;
  font-size: 28px; font-weight: 400;
  color: #1d1d1f; letter-spacing: -0.5px;
  margin-bottom: 8px;
}
.step-desc { font-size: 15px; color: #6e6e73; font-weight: 300; margin-bottom: 36px; }
.step-desc strong { color: #1d1d1f; font-weight: 600; }

/* ── Referenz Input ──────────────────────────── */
.ref-input-wrap {
  display: flex;
  gap: 8px;
  width: 100%;
  max-width: 400px;
  margin-bottom: 12px;
}
.ref-input {
  flex: 1;
  padding: 16px 20px;
  border: 2px solid #e8e8ed;
  border-radius: 14px;
  font-family: 'DM Sans', sans-serif;
  font-size: 17px;
  letter-spacing: 0.03em;
  color: #1d1d1f;
  outline: none;
  transition: border-color 0.2s, box-shadow 0.2s;
  text-align: center;
}
.ref-input:focus {
  border-color: #0071e3;
  box-shadow: 0 0 0 4px rgba(0,113,227,0.1);
}
.btn-go {
  width: 56px; height: 56px;
  background: #1d1d1f;
  border: none;
  border-radius: 14px;
  color: white;
  font-size: 22px;
  cursor: pointer;
  transition: background 0.2s;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.btn-go:hover:not(:disabled) { background: #000; }
.btn-go:disabled { opacity: 0.4; cursor: not-allowed; }

.ref-hint { font-size: 12px; color: #98989f; }

/* ── Carrier Form ────────────────────────────── */
.carrier-form {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  width: 100%;
  margin-bottom: 32px;
}
.carrier-form .form-field:first-child { grid-column: 1 / -1; }

.form-field { display: flex; flex-direction: column; gap: 6px; }
.form-field label {
  font-size: 12px; font-weight: 500;
  color: #1d1d1f; text-transform: uppercase; letter-spacing: 0.04em;
}
.form-input {
  padding: 12px 16px;
  border: 1.5px solid #e8e8ed;
  border-radius: 12px;
  font-family: 'DM Sans', sans-serif;
  font-size: 15px;
  color: #1d1d1f;
  outline: none;
  transition: border-color 0.2s, box-shadow 0.2s;
  background: white;
}
.form-input:focus {
  border-color: #0071e3;
  box-shadow: 0 0 0 3px rgba(0,113,227,0.1);
}

/* ── Combobox Dropdown ───────────────────────── */
.combobox-wrap { position: relative; }
.dropdown {
  position: absolute;
  top: calc(100% + 4px); left: 0; right: 0;
  background: white;
  border: 1.5px solid #e8e8ed;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.1);
  z-index: 100;
  overflow: hidden;
  max-height: 220px;
  overflow-y: auto;
}
.dropdown-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.15s;
}
.dropdown-item:hover { background: #f5f5f7; }
.dd-hint { font-size: 11px; color: #98989f; }
.new-item { color: #0071e3; font-weight: 500; }

/* ── Print Status ────────────────────────────── */
.print-status {
  padding: 16px 28px;
  border-radius: 12px;
  font-size: 15px;
  font-weight: 500;
  margin-bottom: 28px;
}
.print-status.printing { background: rgba(255,149,0,0.1); color: #c87800; }
.print-status.done     { background: rgba(40,200,64,0.1); color: #1a9e30; }

/* ── Signature Canvas ────────────────────────── */
.sig-area {
  width: 100%;
  margin-bottom: 32px;
  position: relative;
}
.sig-canvas {
  width: 100%;
  height: 200px;
  border: 2px solid #e8e8ed;
  border-radius: 16px;
  cursor: crosshair;
  background: #fafafa;
  display: block;
  touch-action: none;
}
.btn-clear-sig {
  margin-top: 8px;
  background: none;
  border: none;
  font-size: 13px;
  color: #98989f;
  cursor: pointer;
  padding: 4px 8px;
}
.btn-clear-sig:hover { color: #1d1d1f; }

/* ── Done Card ───────────────────────────────── */
.done-card { align-items: center; text-align: center; }
.done-check {
  width: 72px; height: 72px;
  background: #28c840;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 32px; color: white; font-weight: 700;
  margin-bottom: 16px;
  animation: popIn 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275) both;
}
.done-meta {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  width: 100%;
  max-width: 360px;
  margin: 0 auto 32px;
  text-align: left;
}
.meta-item { display: flex; flex-direction: column; gap: 2px; }
.meta-item span  { font-size: 11px; color: #98989f; text-transform: uppercase; letter-spacing: 0.05em; }
.meta-item strong { font-size: 14px; color: #1d1d1f; }

/* ── Shared Buttons ──────────────────────────── */
.step-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  width: 100%;
}

.btn-next, .btn-back {
  padding: 13px 28px;
  border-radius: 12px;
  font-family: 'DM Sans', sans-serif;
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
  display: flex; align-items: center; gap: 8px;
}
.btn-next {
  background: #1d1d1f;
  color: white;
}
.btn-next:hover:not(:disabled) { background: #000; transform: translateY(-1px); }
.btn-next:disabled { opacity: 0.4; cursor: not-allowed; }
.btn-back {
  background: #f5f5f7;
  color: #6e6e73;
  border: 1.5px solid #e8e8ed;
}
.btn-back:hover { background: #e8e8ed; color: #1d1d1f; }

.spinner-sm {
  width: 16px; height: 16px;
  border: 2px solid rgba(0,0,0,0.15);
  border-top-color: #1d1d1f;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
  display: inline-block;
}
.spinner-sm.white {
  border-color: rgba(255,255,255,0.3);
  border-top-color: white;
}

@keyframes fadeUp {
  from { opacity: 0; transform: translateY(16px); }
  to   { opacity: 1; transform: translateY(0); }
}
@keyframes spin   { to { transform: rotate(360deg); } }
@keyframes pulse  { 0%,100% { transform: scale(1); } 50% { transform: scale(1.08); } }
@keyframes popIn  {
  from { transform: scale(0.4); opacity: 0; }
  to   { transform: scale(1);   opacity: 1; }
}
</style>
