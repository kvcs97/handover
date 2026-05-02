<template>
  <div class="settings-card">
    <div class="card-title-row">
      <span class="card-icon">🚚</span>
      <h2 class="card-title">Kurier-Carrier</h2>
      <button class="btn-add" @click="openCreate">+ Neuer Carrier</button>
    </div>

    <p class="card-hint">
      Carrier-Erkennung erfolgt über Keywords im Betreff &amp; Dateinamen.
      Druckset bestimmt, welche Dokumenttypen automatisch zum Druck markiert werden.
    </p>

    <div v-if="loading" class="loading">Wird geladen…</div>
    <div v-else-if="error" class="banner error">{{ error }}</div>
    <div v-else-if="carriers.length === 0" class="empty">
      Noch keine Carrier konfiguriert. Lege einen an, damit eingehende Mails zugeordnet werden können.
    </div>

    <ul v-else class="carrier-list">
      <li v-for="c in carriers" :key="c.id" class="carrier-row" :class="{ inactive: !c.is_active }">
        <div class="carrier-meta">
          <div class="carrier-head">
            <span class="carrier-dot" :style="{ background: dotColor(c.name) }" />
            <strong class="carrier-name">{{ c.display_name }}</strong>
            <span class="internal-name">{{ c.name }}</span>
            <span v-if="!c.is_active" class="inactive-pill">deaktiviert</span>
          </div>
          <div class="carrier-detail">
            <span class="detail-label">Keywords:</span>
            <span class="detail-val">{{ (c.detection_keywords || []).join(', ') || '—' }}</span>
          </div>
          <div class="carrier-detail">
            <span class="detail-label">Druckset:</span>
            <span class="detail-val">
              {{ formatDocList(c.print_set_rules?.default) }}
              <template v-for="(ovList, ovKey) in c.print_set_rules?.overrides || {}" :key="ovKey">
                · <em>{{ ovKey }}</em>: {{ formatDocList(ovList) }}
              </template>
            </span>
          </div>
        </div>
        <div class="carrier-actions">
          <button class="btn-icon" title="Bearbeiten" @click="openEdit(c)">✏</button>
          <button class="btn-icon danger" title="Deaktivieren" @click="onDeactivate(c)" :disabled="!c.is_active">🗑</button>
        </div>
      </li>
    </ul>

    <!-- Edit-Modal -->
    <Teleport to="body">
      <transition name="modal-fade">
        <div v-if="modalOpen" class="modal-backdrop" @click.self="closeModal">
          <div class="modal" role="dialog" aria-modal="true">
            <header class="modal-header">
              <h2>{{ editing?.id ? 'Carrier bearbeiten' : 'Neuer Carrier' }}</h2>
              <button class="modal-close" @click="closeModal">✕</button>
            </header>

            <div class="modal-body">
              <div class="field">
                <label>Anzeigename</label>
                <input v-model="form.display_name" class="input" placeholder="z.B. FedEx / TNT" />
              </div>

              <div class="field">
                <label>Interner Name (eindeutig, klein, ohne Leerzeichen)</label>
                <input
                  v-model="form.name"
                  class="input"
                  :disabled="!!editing?.id"
                  placeholder="z.B. fedex_tnt"
                />
                <p v-if="editing?.id" class="hint">Interner Name lässt sich nach Anlegen nicht ändern.</p>
              </div>

              <div class="field">
                <label>Detection-Keywords (kommasepariert)</label>
                <input v-model="form.keywordsRaw" class="input" placeholder="fedex, tnt, federal express" />
                <p class="hint">Wort-genaue Treffer in Betreff und Dateinamen.</p>
              </div>

              <div class="field">
                <label>Default-Druckset</label>
                <div class="doc-toggle-list">
                  <button
                    v-for="t in DOC_TYPES"
                    :key="t"
                    type="button"
                    class="doc-toggle"
                    :class="{ active: form.defaultDocs.includes(t) }"
                    @click="toggleDoc('defaultDocs', t)"
                  >
                    {{ TYPE_LABELS[t] }}
                  </button>
                </div>
              </div>

              <div class="field">
                <label>
                  Overrides
                  <span class="hint-inline">(pro Keyword ein abweichendes Druckset)</span>
                </label>
                <div v-if="form.overrides.length === 0" class="hint">
                  Kein Override — alle Keywords nutzen das Default-Druckset.
                </div>
                <div v-for="(ov, idx) in form.overrides" :key="idx" class="override-row">
                  <input
                    v-model="ov.key"
                    class="input override-key"
                    placeholder="Keyword (muss in Liste oben sein)"
                  />
                  <div class="doc-toggle-list small">
                    <button
                      v-for="t in DOC_TYPES"
                      :key="t"
                      type="button"
                      class="doc-toggle"
                      :class="{ active: ov.docs.includes(t) }"
                      @click="toggleOverrideDoc(idx, t)"
                    >
                      {{ TYPE_LABELS[t] }}
                    </button>
                  </div>
                  <button class="btn-icon danger" @click="form.overrides.splice(idx, 1)" title="Override entfernen">✕</button>
                </div>
                <button type="button" class="btn-ghost-add" @click="addOverride">+ Override hinzufügen</button>
              </div>

              <div v-if="modalError" class="banner error">{{ modalError }}</div>
            </div>

            <footer class="modal-footer">
              <button class="btn-ghost" @click="closeModal" :disabled="saving">Abbrechen</button>
              <button class="btn-primary" :disabled="saving" @click="onSave">
                <span v-if="saving" class="btn-spinner" />
                {{ editing?.id ? 'Speichern' : 'Anlegen' }}
              </button>
            </footer>
          </div>
        </div>
      </transition>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue'
import api from '../../api'

const DOC_TYPES = ['label', 'rechnung', 'lieferschein', 'pkl', 'edec', 'to']
const TYPE_LABELS = {
  label:        'Label',
  rechnung:     'Rechnung',
  lieferschein: 'LS',
  pkl:          'PKL',
  edec:         'EDEC',
  to:           'TO',
}
const COLORS = {
  fedex_tnt: '#4D148C',
  dhl:       '#FFCC00',
  ups:       '#6B3F23',
}
function dotColor(name) { return COLORS[name] || '#9CA3AF' }
function formatDocList(list) {
  if (!list || list.length === 0) return '—'
  return list.map(d => TYPE_LABELS[d] || d).join(', ')
}

const carriers  = ref([])
const loading   = ref(false)
const error     = ref(null)

async function loadCarriers() {
  loading.value = true
  error.value   = null
  try {
    const res = await api.get('/api/courier/carriers', { params: { include_inactive: true } })
    carriers.value = res.data || []
  } catch (e) {
    error.value = e?.response?.data?.detail || e?.message || 'Carrier konnten nicht geladen werden'
  } finally {
    loading.value = false
  }
}
onMounted(loadCarriers)

// ── Modal-State ───────────────────────────────
const modalOpen  = ref(false)
const editing    = ref(null)   // null | bestehender carrier
const modalError = ref(null)
const saving     = ref(false)

const form = reactive({
  name:           '',
  display_name:   '',
  keywordsRaw:    '',
  defaultDocs:    [],
  overrides:      [],   // [{ key, docs: [] }]
  is_active:      true,
})

function resetForm() {
  form.name         = ''
  form.display_name = ''
  form.keywordsRaw  = ''
  form.defaultDocs  = []
  form.overrides    = []
  form.is_active    = true
}

function openCreate() {
  editing.value    = null
  modalError.value = null
  resetForm()
  modalOpen.value  = true
}

function openEdit(c) {
  editing.value    = c
  modalError.value = null
  form.name         = c.name
  form.display_name = c.display_name
  form.keywordsRaw  = (c.detection_keywords || []).join(', ')
  form.defaultDocs  = [...(c.print_set_rules?.default || [])]
  form.overrides    = Object.entries(c.print_set_rules?.overrides || {})
    .map(([k, docs]) => ({ key: k, docs: [...docs] }))
  form.is_active    = c.is_active
  modalOpen.value   = true
}

function closeModal() {
  if (saving.value) return
  modalOpen.value = false
}

function toggleDoc(field, t) {
  const list = form[field]
  const i = list.indexOf(t)
  if (i === -1) list.push(t)
  else list.splice(i, 1)
}
function toggleOverrideDoc(idx, t) {
  const list = form.overrides[idx].docs
  const i = list.indexOf(t)
  if (i === -1) list.push(t)
  else list.splice(i, 1)
}
function addOverride() {
  form.overrides.push({ key: '', docs: [] })
}

async function onSave() {
  modalError.value = null

  // Lokale Validierung
  if (!form.display_name.trim() || !form.name.trim()) {
    modalError.value = 'Anzeigename und interner Name sind Pflicht'
    return
  }
  const kws = form.keywordsRaw.split(',').map(k => k.trim().toLowerCase()).filter(Boolean)
  if (kws.length === 0) {
    modalError.value = 'Mindestens ein Keyword erforderlich'
    return
  }
  if (form.defaultDocs.length === 0) {
    modalError.value = 'Default-Druckset darf nicht leer sein'
    return
  }
  const overrides = {}
  for (const ov of form.overrides) {
    const k = (ov.key || '').trim().toLowerCase()
    if (!k) {
      modalError.value = 'Override-Keyword darf nicht leer sein'
      return
    }
    if (!kws.includes(k)) {
      modalError.value = `Override-Keyword "${k}" muss in der Keyword-Liste oben stehen`
      return
    }
    if (overrides[k]) {
      modalError.value = `Doppeltes Override-Keyword: "${k}"`
      return
    }
    overrides[k] = ov.docs
  }

  const payload = {
    name:               form.name.trim(),
    display_name:       form.display_name.trim(),
    detection_keywords: kws,
    print_set_rules:    { default: form.defaultDocs, overrides },
    is_active:          form.is_active,
  }

  saving.value = true
  try {
    if (editing.value?.id) {
      await api.put(`/api/courier/carriers/${editing.value.id}`, {
        display_name:       payload.display_name,
        detection_keywords: payload.detection_keywords,
        print_set_rules:    payload.print_set_rules,
        is_active:          payload.is_active,
      })
    } else {
      await api.post('/api/courier/carriers', payload)
    }
    modalOpen.value = false
    await loadCarriers()
  } catch (e) {
    modalError.value = e?.response?.data?.detail || e?.message || 'Speichern fehlgeschlagen'
  } finally {
    saving.value = false
  }
}

async function onDeactivate(c) {
  if (!confirm(`Carrier "${c.display_name}" deaktivieren?\nBestehende Sendungen bleiben erhalten.`)) return
  try {
    await api.delete(`/api/courier/carriers/${c.id}`)
    await loadCarriers()
  } catch (e) {
    error.value = e?.response?.data?.detail || e?.message || 'Deaktivieren fehlgeschlagen'
  }
}
</script>

<style scoped>
/* Zellen-Layout passt sich an die bestehende Settings.vue-Karte an */
.settings-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  padding: 22px 24px;
  margin-bottom: 16px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
  font-family: 'DM Sans', sans-serif;
}
.card-title-row {
  display: flex; align-items: center; gap: 10px;
  margin-bottom: 6px;
}
.card-icon { font-size: 18px; }
.card-title {
  font-family: 'Instrument Serif', serif;
  font-size: 20px; font-weight: 400; margin: 0;
  flex: 1;
}
.btn-add {
  background: var(--accent-primary);
  color: white;
  border: none;
  padding: 7px 14px;
  border-radius: 8px;
  font-size: 12.5px;
  font-weight: 500;
  cursor: pointer;
}
.btn-add:hover { background: var(--accent-secondary); }

.card-hint {
  font-size: 12.5px;
  color: var(--color-text-muted);
  margin: 0 0 14px;
}

.loading, .empty {
  text-align: center;
  color: var(--color-text-muted);
  padding: 18px;
  font-size: 13px;
}

.banner.error {
  background: rgba(239,68,68,0.08);
  border: 1px solid rgba(239,68,68,0.25);
  color: var(--color-danger);
  padding: 10px 14px;
  border-radius: 10px;
  font-size: 12.5px;
  margin-bottom: 12px;
}

/* Carrier-Liste */
.carrier-list { list-style: none; padding: 0; margin: 0; }
.carrier-row {
  display: flex; justify-content: space-between; align-items: flex-start;
  padding: 14px 0;
  border-bottom: 1px solid var(--color-border);
  gap: 16px;
}
.carrier-row:last-child { border-bottom: none; }
.carrier-row.inactive { opacity: 0.55; }

.carrier-head {
  display: flex; align-items: center; gap: 10px;
  margin-bottom: 6px;
}
.carrier-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
.carrier-name { font-size: 14.5px; }
.internal-name {
  font-family: 'DM Mono', 'JetBrains Mono', monospace;
  font-size: 11.5px;
  color: var(--color-text-muted);
  background: var(--accent-bg);
  padding: 2px 8px;
  border-radius: 9999px;
}
.inactive-pill {
  font-size: 10px;
  background: #F1F1F1;
  color: var(--color-text-muted);
  padding: 2px 8px;
  border-radius: 9999px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.carrier-detail { font-size: 12.5px; line-height: 1.5; }
.detail-label {
  display: inline-block;
  width: 80px;
  color: var(--color-text-muted);
}
.detail-val { color: var(--color-text); }
.carrier-detail em {
  font-style: normal;
  font-family: 'DM Mono', 'JetBrains Mono', monospace;
  color: var(--accent-primary);
}

.carrier-actions { display: flex; gap: 6px; flex-shrink: 0; }
.btn-icon {
  background: transparent;
  border: 1px solid var(--color-border);
  width: 32px; height: 32px;
  border-radius: 8px;
  font-size: 13px;
  cursor: pointer;
  color: var(--color-text-muted);
  transition: all 120ms ease;
}
.btn-icon:hover:not(:disabled) {
  background: var(--accent-bg);
  border-color: var(--accent-primary);
  color: var(--accent-primary);
}
.btn-icon.danger:hover:not(:disabled) {
  background: var(--color-danger);
  color: white;
  border-color: var(--color-danger);
}
.btn-icon:disabled { opacity: 0.4; cursor: not-allowed; }

/* Modal */
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
  width: min(620px, 100%);
  max-height: 92vh;
  display: flex; flex-direction: column;
  box-shadow: 0 16px 40px rgba(0,0,0,0.20);
  overflow: hidden;
  font-family: 'DM Sans', sans-serif;
}
.modal-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 18px 22px;
  border-bottom: 1px solid var(--color-border);
}
.modal-header h2 {
  font-family: 'Instrument Serif', serif;
  font-size: 20px; font-weight: 400; margin: 0;
}
.modal-close {
  background: transparent; border: none; cursor: pointer;
  width: 32px; height: 32px; border-radius: 8px;
  font-size: 16px; color: var(--color-text-muted);
}
.modal-close:hover { background: var(--accent-bg); color: var(--color-text); }

.modal-body {
  padding: 18px 22px;
  overflow-y: auto;
  display: flex; flex-direction: column; gap: 14px;
}

.field { display: flex; flex-direction: column; gap: 4px; }
.field label {
  font-size: 11px; font-weight: 600; letter-spacing: 0.04em;
  text-transform: uppercase; color: var(--color-text-muted);
}
.input {
  padding: 9px 12px;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  background: var(--color-surface);
  font-size: 13px;
  font-family: 'DM Sans', sans-serif;
  color: var(--color-text);
}
.input:focus {
  outline: none;
  border-color: var(--accent-primary);
  box-shadow: 0 0 0 3px rgba(91,141,184,0.15);
}
.input:disabled { background: #F8F8F8; color: var(--color-text-muted); }
.hint {
  font-size: 11.5px;
  color: var(--color-text-muted);
  font-style: italic;
}
.hint-inline {
  font-style: italic;
  color: var(--color-text-muted);
  font-weight: 400;
  text-transform: none;
  letter-spacing: 0;
  margin-left: 6px;
}

.doc-toggle-list {
  display: flex; flex-wrap: wrap; gap: 6px;
  margin-top: 4px;
}
.doc-toggle {
  background: var(--color-border);
  color: var(--color-text-muted);
  border: 1px solid transparent;
  padding: 5px 12px;
  border-radius: 9999px;
  font-size: 12px;
  cursor: pointer;
  font-family: 'DM Mono', 'JetBrains Mono', monospace;
  transition: all 120ms ease;
}
.doc-toggle.active {
  background: rgba(91,141,184,0.10);
  color: var(--accent-primary);
  border-color: rgba(91,141,184,0.30);
}
.doc-toggle:hover { border-color: var(--accent-primary); }
.doc-toggle-list.small .doc-toggle { padding: 3px 9px; font-size: 11px; }

.override-row {
  display: grid;
  grid-template-columns: minmax(120px, 200px) 1fr auto;
  gap: 10px;
  align-items: center;
  margin-top: 6px;
}
.override-key { padding: 7px 10px; font-size: 12px; }

.btn-ghost-add {
  margin-top: 8px;
  padding: 7px 14px;
  background: transparent;
  border: 1px dashed var(--color-border);
  border-radius: 8px;
  font-size: 12.5px;
  color: var(--color-text-muted);
  cursor: pointer;
}
.btn-ghost-add:hover {
  background: var(--accent-bg);
  color: var(--accent-primary);
  border-color: var(--accent-primary);
}

.modal-footer {
  display: flex; justify-content: flex-end; gap: 10px;
  padding: 14px 22px;
  border-top: 1px solid var(--color-border);
  background: #FAFAFA;
}
.btn-primary, .btn-ghost {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 9px 18px;
  border-radius: 10px;
  font-size: 13px; font-weight: 500;
  cursor: pointer;
  font-family: 'DM Sans', sans-serif;
  transition: background 150ms ease, opacity 150ms ease;
}
.btn-primary { background: var(--accent-primary); color: white; border: none; }
.btn-primary:hover:not(:disabled) { background: var(--accent-secondary); }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-ghost { background: transparent; border: 1px solid var(--color-border); color: var(--color-text); }
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

.modal-fade-enter-active, .modal-fade-leave-active { transition: opacity 180ms ease; }
.modal-fade-enter-from, .modal-fade-leave-to { opacity: 0; }
</style>
