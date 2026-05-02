<template>
  <Teleport to="body">
    <transition name="modal-fade">
      <div v-if="open" class="modal-backdrop" @click.self="onCancel">
        <div class="modal" role="dialog" aria-modal="true">
          <header class="modal-header">
            <div class="header-text">
              <h2>Unterschrift — {{ carrierLabel }}</h2>
              <p class="meta">
                {{ shipmentCount }} {{ shipmentCount === 1 ? 'Sendung wird' : 'Sendungen werden' }} unterschrieben & archiviert
              </p>
            </div>
            <button class="modal-close" type="button" @click="onCancel" aria-label="Schließen">✕</button>
          </header>

          <div class="modal-body">
            <section class="ls-section">
              <h3>Betroffene Lieferscheine</h3>
              <div class="ls-list">
                <span
                  v-for="ls in lsNumbers"
                  :key="ls"
                  class="ls-pill"
                >{{ ls }}</span>
                <span v-if="lsNumbers.length === 0" class="ls-empty">
                  Keine LS-Nummern in dieser Carrier-Gruppe
                </span>
              </div>
            </section>

            <section class="canvas-section">
              <div class="canvas-frame">
                <canvas
                  ref="canvasRef"
                  class="sig-canvas"
                  @mousedown="startDraw"
                  @mousemove="draw"
                  @mouseup="stopDraw"
                  @mouseleave="stopDraw"
                  @touchstart.prevent="startDrawTouch"
                  @touchmove.prevent="drawTouch"
                  @touchend="stopDraw"
                />
                <button
                  type="button"
                  class="btn-clear"
                  :disabled="!hasSignature || submitting"
                  @click="clearSignature"
                >
                  🗑 Löschen
                </button>
              </div>
              <p class="canvas-hint">
                Hier unterschreiben — der Stift erfasst Maus &amp; Touch.
              </p>
            </section>

            <section class="signer-section">
              <label class="signer-label" for="signer-name">Name des Fahrers (optional)</label>
              <input
                id="signer-name"
                type="text"
                class="signer-input"
                v-model="signerName"
                placeholder="z.B. Max Mustermann"
                :disabled="submitting"
              />
            </section>

            <div v-if="errorText" class="error-banner">
              <span>⚠</span>
              <span>{{ errorText }}</span>
            </div>
          </div>

          <footer class="modal-footer">
            <button type="button" class="btn-ghost" @click="onCancel" :disabled="submitting">
              Abbrechen
            </button>
            <button
              type="button"
              class="btn-primary"
              :disabled="!hasSignature || submitting"
              @click="onSubmit"
            >
              <span v-if="submitting" class="btn-spinner" />
              <span v-else>✍</span>
              {{ submitting ? 'Wird archiviert…' : 'Unterschreiben & Archivieren' }}
            </button>
          </footer>
        </div>
      </div>
    </transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { useCourierStore } from '../../stores/courier'

const props = defineProps({
  open:  { type: Boolean, default: false },
  group: { type: Object, default: null },
})
const emit = defineEmits(['close', 'signed'])

const courier = useCourierStore()

// ── Computed ──────────────────────────────────────
const carrierLabel = computed(() => props.group?.carrier?.display_name || '')
const shipmentCount = computed(() => props.group?.shipments?.length || 0)
const lsNumbers = computed(() => {
  if (!props.group) return []
  const out = []
  for (const s of props.group.shipments || []) {
    for (const ls of s.delivery_note_numbers || []) {
      if (!out.includes(ls)) out.push(ls)
    }
  }
  return out
})

const submitting = computed(() => courier.isCarrierSigning(props.group?.carrier?.id))

// ── Canvas-Logik ──────────────────────────────────
const canvasRef = ref(null)
const hasSignature = ref(false)
const errorText    = ref(null)
const signerName   = ref('')
let ctx = null
let drawing = false

function initCanvas() {
  const c = canvasRef.value
  if (!c) return
  // Crisp lines bei DPR > 1
  const dpr = window.devicePixelRatio || 1
  const rect = c.getBoundingClientRect()
  c.width  = rect.width * dpr
  c.height = rect.height * dpr
  ctx = c.getContext('2d')
  ctx.scale(dpr, dpr)
  ctx.lineWidth   = 2.2
  ctx.lineCap     = 'round'
  ctx.lineJoin    = 'round'
  ctx.strokeStyle = '#1a1a1a'
}

function getPos(e) {
  const r = canvasRef.value.getBoundingClientRect()
  return { x: e.clientX - r.left, y: e.clientY - r.top }
}
function getTouchPos(t) {
  const r = canvasRef.value.getBoundingClientRect()
  return { x: t.clientX - r.left, y: t.clientY - r.top }
}

function startDraw(e) {
  if (!ctx) return
  drawing = true
  const p = getPos(e)
  ctx.beginPath()
  ctx.moveTo(p.x, p.y)
}
function draw(e) {
  if (!drawing || !ctx) return
  const p = getPos(e)
  ctx.lineTo(p.x, p.y)
  ctx.stroke()
  hasSignature.value = true
}
function startDrawTouch(e) {
  if (!ctx) return
  drawing = true
  const p = getTouchPos(e.touches[0])
  ctx.beginPath()
  ctx.moveTo(p.x, p.y)
}
function drawTouch(e) {
  if (!drawing || !ctx) return
  const p = getTouchPos(e.touches[0])
  ctx.lineTo(p.x, p.y)
  ctx.stroke()
  hasSignature.value = true
}
function stopDraw() { drawing = false }

function clearSignature() {
  if (!ctx) return
  ctx.clearRect(0, 0, canvasRef.value.width, canvasRef.value.height)
  hasSignature.value = false
}

function reset() {
  hasSignature.value = false
  errorText.value    = null
  signerName.value   = ''
  if (ctx && canvasRef.value) {
    ctx.clearRect(0, 0, canvasRef.value.width, canvasRef.value.height)
  }
}

watch(() => props.open, async (val) => {
  if (val) {
    reset()
    await nextTick()
    initCanvas()
  }
})

// ── Submit ────────────────────────────────────────
async function onSubmit() {
  if (!hasSignature.value || submitting.value) return
  errorText.value = null
  try {
    const dataUrl = canvasRef.value.toDataURL('image/png')
    const result = await courier.signCarrier(props.group.carrier.id, {
      signature_data: dataUrl,
      signer_name:    signerName.value.trim() || null,
      process_date:   courier.selectedDate,
    })
    if (result?.archived_count === 0) {
      errorText.value = 'Keine Sendung konnte archiviert werden — siehe Server-Log.'
      return
    }
    emit('signed', result)
    emit('close')
  } catch (e) {
    errorText.value = e?.response?.data?.detail || e?.message || 'Archivierung fehlgeschlagen'
  }
}

function onCancel() {
  if (submitting.value) return
  emit('close')
}
</script>

<style scoped>
.modal-backdrop {
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.45);
  display: flex; align-items: center; justify-content: center;
  z-index: 1000;
  padding: 24px;
}
.modal {
  background: var(--color-surface);
  border-radius: 16px;
  width: min(720px, 100%);
  max-height: 92vh;
  display: flex; flex-direction: column;
  box-shadow: 0 16px 40px rgba(0,0,0,0.20);
  overflow: hidden;
  font-family: 'DM Sans', sans-serif;
}

.modal-header {
  display: flex; justify-content: space-between; align-items: flex-start;
  padding: 20px 24px;
  border-bottom: 1px solid var(--color-border);
  gap: 16px;
}
.header-text h2 {
  font-family: 'Instrument Serif', serif;
  font-size: 22px; font-weight: 400; margin: 0 0 4px;
}
.meta { font-size: 13px; color: var(--color-text-muted); margin: 0; }

.modal-close {
  background: transparent; border: none;
  font-size: 18px; cursor: pointer;
  width: 32px; height: 32px; border-radius: 8px;
  color: var(--color-text-muted);
}
.modal-close:hover { background: var(--accent-bg); color: var(--color-text); }

.modal-body {
  padding: 20px 24px;
  overflow-y: auto;
  display: flex; flex-direction: column; gap: 18px;
}

/* LS-Section */
.ls-section h3, .signer-section .signer-label, .canvas-section .canvas-hint {
  font-size: 11px; font-weight: 600; letter-spacing: 0.04em;
  text-transform: uppercase; color: var(--color-text-muted);
  margin: 0 0 8px;
}
.ls-list {
  display: flex; flex-wrap: wrap; gap: 6px;
  max-height: 96px; overflow-y: auto;
}
.ls-pill {
  font-family: 'DM Mono', 'JetBrains Mono', monospace;
  font-size: 12px;
  background: var(--accent-bg);
  color: var(--accent-primary);
  padding: 4px 10px; border-radius: 9999px;
}
.ls-empty {
  font-size: 12px; color: var(--color-warning); font-style: italic;
}

/* Canvas */
.canvas-section { display: flex; flex-direction: column; }
.canvas-frame {
  position: relative;
  border: 1px solid var(--color-border);
  border-radius: 12px;
  background: #FAFAFA;
  overflow: hidden;
}
.sig-canvas {
  display: block;
  width: 100%;
  height: 220px;
  cursor: crosshair;
  background: white;
  touch-action: none;
}
.btn-clear {
  position: absolute;
  bottom: 10px; right: 10px;
  background: rgba(255,255,255,0.95);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 5px 10px;
  font-size: 11.5px;
  cursor: pointer;
  color: var(--color-text-muted);
}
.btn-clear:hover:not(:disabled) {
  background: var(--color-danger);
  color: white;
  border-color: var(--color-danger);
}
.btn-clear:disabled { opacity: 0.4; cursor: not-allowed; }
.canvas-hint {
  margin: 8px 0 0;
  font-size: 11.5px;
  color: var(--color-text-muted);
  text-transform: none;
  letter-spacing: 0;
  font-weight: 400;
}

/* Signer-Input */
.signer-input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  background: var(--color-surface);
  font-size: 13.5px;
  font-family: 'DM Sans', sans-serif;
  color: var(--color-text);
  transition: border-color 150ms ease;
}
.signer-input:focus {
  outline: none;
  border-color: var(--accent-primary);
  box-shadow: 0 0 0 3px rgba(91,141,184,0.15);
}
.signer-input:disabled { opacity: 0.6; cursor: not-allowed; }

.error-banner {
  display: flex; gap: 8px; align-items: flex-start;
  background: rgba(239,68,68,0.08);
  border: 1px solid rgba(239,68,68,0.25);
  color: var(--color-danger);
  border-radius: 10px;
  padding: 10px 14px;
  font-size: 12.5px;
}

/* Footer */
.modal-footer {
  display: flex; justify-content: flex-end; gap: 10px;
  padding: 14px 24px;
  border-top: 1px solid var(--color-border);
  background: #FAFAFA;
}

.btn-primary, .btn-ghost {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 10px 20px;
  border-radius: 10px;
  font-family: 'DM Sans', sans-serif;
  font-size: 13.5px; font-weight: 500;
  cursor: pointer;
  transition: background 150ms ease, opacity 150ms ease;
}
.btn-primary {
  background: var(--accent-primary); color: white; border: none;
}
.btn-primary:hover:not(:disabled) { background: var(--accent-secondary); }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-ghost {
  background: transparent; border: 1px solid var(--color-border);
  color: var(--color-text);
}
.btn-ghost:hover:not(:disabled) { background: var(--accent-bg); }
.btn-ghost:disabled { opacity: 0.5; cursor: not-allowed; }

.btn-spinner {
  width: 12px; height: 12px;
  border: 2px solid rgba(255,255,255,0.4);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 700ms linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.modal-fade-enter-active, .modal-fade-leave-active {
  transition: opacity 180ms ease;
}
.modal-fade-enter-from, .modal-fade-leave-to { opacity: 0; }
</style>
