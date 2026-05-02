<template>
  <Teleport to="body">
    <transition name="modal-fade">
      <div v-if="open" class="modal-backdrop" @click.self="onCancel">
        <div class="modal" role="dialog" aria-modal="true">
          <header class="modal-header">
            <div class="header-text">
              <h2>Drucken — Sendung</h2>
              <p>
                <span v-for="(ls, i) in lsNumbers" :key="ls" class="ls">
                  {{ ls }}<span v-if="i < lsNumbers.length - 1" class="sep">·</span>
                </span>
                <span v-if="lsNumbers.length === 0" class="ls-missing">Ohne LS-Nummer</span>
              </p>
              <p class="meta">
                <span v-if="carrierLabel">{{ carrierLabel }}</span>
                <span v-if="shipment?.email_subject" class="subject" :title="shipment.email_subject">
                  · {{ shipment.email_subject }}
                </span>
              </p>
            </div>
            <button class="modal-close" type="button" @click="onCancel" aria-label="Schließen">✕</button>
          </header>

          <div class="modal-body">
            <!-- Linke Spalte: Dokumentenliste -->
            <section class="docs-panel">
              <h3>Dokumente</h3>
              <ul class="doc-list">
                <li
                  v-for="d in documents"
                  :key="d.id"
                  class="doc-item"
                  :class="{ active: previewDocId === d.id }"
                >
                  <label class="doc-check">
                    <input
                      type="checkbox"
                      :checked="d.should_print"
                      :disabled="docBusy.has(d.id)"
                      @change="onToggle(d, $event.target.checked)"
                    />
                    <span class="doc-type">{{ typeLabel(d.document_type) }}</span>
                  </label>
                  <span class="doc-filename" :title="d.filename">{{ d.filename }}</span>
                  <button
                    type="button"
                    class="btn-preview"
                    :class="{ active: previewDocId === d.id }"
                    @click="loadPreview(d)"
                    :disabled="!hasLocalFile(d)"
                    :title="hasLocalFile(d) ? 'Vorschau anzeigen' : 'PDF nicht verfügbar'"
                  >
                    👁
                  </button>
                </li>
              </ul>
              <p v-if="!hasSelection" class="select-hint">
                Mindestens ein Dokument auswählen, um zu drucken.
              </p>
            </section>

            <!-- Rechte Spalte: PDF-Vorschau -->
            <section class="preview-panel">
              <div v-if="previewLoading" class="preview-loading">
                <div class="spinner-large" />
                <p>Vorschau wird geladen…</p>
              </div>
              <iframe
                v-else-if="previewUrl"
                :src="previewUrl"
                class="preview-frame"
                :title="previewFilename"
              />
              <div v-else class="preview-empty">
                <span class="preview-icon">📄</span>
                <p>Klick auf 👁 neben einem Dokument, um die Vorschau zu öffnen.</p>
              </div>
              <div v-if="previewError" class="preview-error">{{ previewError }}</div>
            </section>
          </div>

          <footer class="modal-footer">
            <span class="footer-info">
              {{ selectedCount }} von {{ documents.length }} ausgewählt
            </span>
            <div class="footer-actions">
              <button type="button" class="btn-ghost" @click="onCancel" :disabled="printing">
                Abbrechen
              </button>
              <button
                type="button"
                class="btn-primary"
                :disabled="!hasSelection || printing"
                @click="onPrint"
              >
                <span v-if="printing" class="btn-spinner" />
                <span v-else>🖨</span>
                {{ printing ? 'Drucke…' : `${selectedCount} Dokument${selectedCount === 1 ? '' : 'e'} drucken` }}
              </button>
            </div>
          </footer>
        </div>
      </div>
    </transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useCourierStore } from '../../stores/courier'

const props = defineProps({
  open:     { type: Boolean, default: false },
  shipment: { type: Object, default: null },
})
const emit = defineEmits(['close', 'printed'])

const courier = useCourierStore()

const TYPE_LABELS = {
  label: 'Label', rechnung: 'Rechnung', lieferschein: 'LS',
  pkl: 'PKL', edec: 'EDEC', to: 'TO', other: 'Sonstige',
}
function typeLabel(t) { return TYPE_LABELS[t] || t }

const documents = computed(() => props.shipment?.documents || [])
const lsNumbers = computed(() => props.shipment?.delivery_note_numbers || [])
const carrierLabel = computed(() => {
  if (!props.shipment) return ''
  const cid = props.shipment.carrier_id
  if (!cid) return 'Unzugeordnet'
  const c = courier.carriers.find(c => c.id === cid)
  return c?.display_name || ''
})

const selectedCount = computed(() => documents.value.filter(d => d.should_print).length)
const hasSelection  = computed(() => selectedCount.value > 0)

function hasLocalFile(d) {
  return !!d.local_path
}

// ── Doc-Toggle (synchronisiert mit Store) ────────────
const docBusy = ref(new Set())
async function onToggle(d, nextValue) {
  if (docBusy.value.has(d.id)) return
  docBusy.value = new Set(docBusy.value).add(d.id)
  try {
    await courier.toggleDocumentPrint(props.shipment.id, d.id, nextValue)
  } finally {
    const next = new Set(docBusy.value)
    next.delete(d.id)
    docBusy.value = next
  }
}

// ── PDF-Vorschau ─────────────────────────────────────
const previewDocId    = ref(null)
const previewUrl      = ref(null)
const previewFilename = ref('')
const previewLoading  = ref(false)
const previewError    = ref(null)

function revokePreview() {
  if (previewUrl.value) {
    try { URL.revokeObjectURL(previewUrl.value) } catch {}
  }
  previewUrl.value = null
  previewFilename.value = ''
  previewDocId.value = null
}

async function loadPreview(d) {
  if (!hasLocalFile(d)) return
  if (previewDocId.value === d.id) return  // schon offen
  revokePreview()
  previewLoading.value = true
  previewError.value   = null
  try {
    previewUrl.value = await courier.fetchDocumentBlobUrl(d.id)
    previewFilename.value = d.filename
    previewDocId.value    = d.id
  } catch (e) {
    previewError.value = e?.response?.data?.detail || e?.message || 'Vorschau fehlgeschlagen'
  } finally {
    previewLoading.value = false
  }
}

// ── Drucken ──────────────────────────────────────────
const printing = computed(() => courier.isShipmentPrinting(props.shipment?.id))

async function onPrint() {
  if (!props.shipment || !hasSelection.value) return
  try {
    const result = await courier.printShipment(props.shipment.id)
    emit('printed', result)
    onCancel()
  } catch { /* fetchError ist im Store gesetzt */ }
}

function onCancel() {
  if (printing.value) return
  revokePreview()
  emit('close')
}

// Vorschau zurücksetzen, wenn Modal geschlossen oder Sendung gewechselt wird
watch(() => props.open, (val) => { if (!val) revokePreview() })
watch(() => props.shipment?.id, () => revokePreview())
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
  width: min(1080px, 100%);
  max-height: 90vh;
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
.header-text .ls {
  font-family: 'DM Mono', 'JetBrains Mono', monospace;
  font-size: 13px; font-weight: 500;
}
.header-text .sep { margin: 0 6px; color: var(--color-text-muted); }
.ls-missing { font-size: 12px; color: var(--color-danger); font-style: italic; }
.meta {
  margin: 4px 0 0; font-size: 12px;
  color: var(--color-text-muted);
}
.subject { white-space: nowrap; }

.modal-close {
  background: transparent; border: none;
  font-size: 18px; cursor: pointer;
  width: 32px; height: 32px; border-radius: 8px;
  color: var(--color-text-muted);
}
.modal-close:hover { background: var(--accent-bg); color: var(--color-text); }

.modal-body {
  display: grid;
  grid-template-columns: 320px 1fr;
  flex: 1; min-height: 0;
}

/* Docs-Panel */
.docs-panel {
  border-right: 1px solid var(--color-border);
  padding: 18px 18px;
  overflow-y: auto;
}
.docs-panel h3 {
  font-size: 11px; font-weight: 600; letter-spacing: 0.04em;
  text-transform: uppercase; color: var(--color-text-muted);
  margin: 0 0 10px;
}
.doc-list {
  list-style: none; padding: 0; margin: 0;
  display: flex; flex-direction: column; gap: 4px;
}
.doc-item {
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  border-radius: 8px;
  border: 1px solid transparent;
  transition: background 120ms ease, border-color 120ms ease;
}
.doc-item:hover { background: var(--accent-bg); }
.doc-item.active {
  background: var(--accent-bg);
  border-color: rgba(91,141,184,0.30);
}
.doc-check {
  display: inline-flex; align-items: center; gap: 6px;
  cursor: pointer; user-select: none;
}
.doc-check input[type="checkbox"] {
  accent-color: var(--accent-primary);
  cursor: pointer;
}
.doc-type {
  font-family: 'DM Mono', 'JetBrains Mono', monospace;
  font-size: 11px; font-weight: 500;
  color: var(--accent-primary);
  min-width: 40px;
}
.doc-filename {
  font-size: 12px; color: var(--color-text-muted);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  min-width: 0;
}
.btn-preview {
  background: transparent; border: 1px solid var(--color-border);
  width: 28px; height: 28px; border-radius: 6px;
  font-size: 13px; cursor: pointer;
  color: var(--color-text-muted);
  transition: all 120ms ease;
  flex-shrink: 0;
}
.btn-preview:hover:not(:disabled) {
  background: var(--accent-primary); color: white;
  border-color: var(--accent-primary);
}
.btn-preview.active {
  background: var(--accent-primary); color: white;
  border-color: var(--accent-primary);
}
.btn-preview:disabled { opacity: 0.4; cursor: not-allowed; }
.select-hint {
  font-size: 11.5px; color: var(--color-warning);
  margin: 12px 0 0; font-style: italic;
}

/* Preview-Panel */
.preview-panel {
  background: #F8F8F8;
  position: relative;
  overflow: hidden;
  display: flex; align-items: center; justify-content: center;
}
.preview-frame {
  width: 100%; height: 100%; min-height: 480px;
  border: none;
  background: white;
}
.preview-empty {
  text-align: center; color: var(--color-text-muted);
  padding: 40px 32px;
}
.preview-icon { font-size: 36px; display: block; margin-bottom: 10px; }
.preview-empty p { font-size: 13px; max-width: 260px; margin: 0 auto; line-height: 1.5; }
.preview-loading {
  text-align: center; color: var(--color-text-muted);
}
.preview-loading p { margin-top: 10px; font-size: 13px; }
.preview-error {
  position: absolute; bottom: 16px; left: 16px; right: 16px;
  background: rgba(239,68,68,0.10);
  border: 1px solid rgba(239,68,68,0.25);
  color: var(--color-danger);
  border-radius: 8px;
  padding: 8px 12px;
  font-size: 12px;
}

/* Footer */
.modal-footer {
  display: flex; justify-content: space-between; align-items: center;
  padding: 14px 24px;
  border-top: 1px solid var(--color-border);
  background: #FAFAFA;
}
.footer-info { font-size: 12px; color: var(--color-text-muted); }
.footer-actions { display: flex; gap: 10px; }

.btn-primary, .btn-ghost {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 9px 18px;
  border-radius: 10px;
  font-family: 'DM Sans', sans-serif;
  font-size: 13px; font-weight: 500;
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
.spinner-large {
  width: 28px; height: 28px;
  border: 3px solid var(--color-border);
  border-top-color: var(--accent-primary);
  border-radius: 50%;
  animation: spin 700ms linear infinite;
  margin: 0 auto;
}
@keyframes spin { to { transform: rotate(360deg); } }

.modal-fade-enter-active, .modal-fade-leave-active {
  transition: opacity 180ms ease;
}
.modal-fade-enter-from, .modal-fade-leave-to { opacity: 0; }
</style>
