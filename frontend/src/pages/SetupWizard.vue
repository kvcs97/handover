<template>
  <div class="setup-root">

    <!-- Left Branding -->
    <div class="setup-brand">
      <div class="brand-inner">
        <div class="brand-logo">H</div>
        <h1 class="brand-name">HandOver</h1>
        <p class="brand-tag">Willkommen — richten wir<br>alles ein.</p>

        <div class="wizard-steps">
          <div
            v-for="(s, i) in wizardSteps"
            :key="i"
            class="wstep"
            :class="{ active: currentStep === i, done: currentStep > i }"
          >
            <div class="wstep-dot">
              <span v-if="currentStep > i">✓</span>
              <span v-else>{{ i + 1 }}</span>
            </div>
            <div class="wstep-label">{{ s.label }}</div>
          </div>
        </div>
      </div>
      <div class="brand-footer">shoriu.com/handover</div>
    </div>

    <!-- Right Content -->
    <div class="setup-content">
      <div class="setup-inner">

        <!-- Progress bar -->
        <div class="progress-bar">
          <div class="progress-fill" :style="`width:${((currentStep) / (wizardSteps.length - 1)) * 100}%`"></div>
        </div>

        <!-- ── Schritt 1: Firmendaten ── -->
        <div class="setup-step" v-if="currentStep === 0">
          <div class="step-icon">🏢</div>
          <h2 class="step-title">Firmendaten</h2>
          <p class="step-sub">Wie heisst deine Firma? Diese Daten erscheinen auf den Dokumenten.</p>

          <div class="fields">
            <div class="field">
              <label>Firmenname *</label>
              <input v-model="form.company_name" type="text" class="input" placeholder="Muster AG" />
            </div>
            <div class="field">
              <label>Adresse</label>
              <input v-model="form.company_address" type="text" class="input" placeholder="Musterstrasse 1, 9000 St. Gallen" />
            </div>
            <div class="field">
              <label>Firmen-Logo</label>
              <div class="logo-upload" @click="triggerLogoUpload" :class="{ has: logoPreview }">
                <input ref="logoInput" type="file" accept="image/*" class="hidden" @change="onLogoUpload" />
                <img v-if="logoPreview" :src="logoPreview" class="logo-preview" />
                <div v-else class="logo-placeholder">
                  <span>+</span>
                  <span>Logo hochladen</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- ── Schritt 2: Drucker ── -->
        <div class="setup-step" v-if="currentStep === 1">
          <div class="step-icon">🖨️</div>
          <h2 class="step-title">Drucker einrichten</h2>
          <p class="step-sub">Wähle den Netzwerkdrucker, an den Dokumente automatisch gesendet werden.</p>

          <div class="fields">
            <div class="field">
              <label>Druckername *</label>
              <div class="select-wrap">
                <select v-model="form.printer_name" class="input select">
                  <option value="">— Drucker auswählen —</option>
                  <option v-for="p in availablePrinters" :key="p" :value="p">{{ p }}</option>
                </select>
              </div>
            </div>
            <div class="field">
              <label>Oder manuell eingeben</label>
              <input v-model="form.printer_name" type="text" class="input" placeholder="Druckername exakt" />
            </div>
            <div class="printer-hint">
              💡 Den genauen Druckernamen findest du unter Systemeinstellungen → Drucker.
            </div>
          </div>
        </div>

        <!-- ── Schritt 3: Datenquelle ── -->
        <div class="setup-step" v-if="currentStep === 2">
          <div class="step-icon">📡</div>
          <h2 class="step-title">Datenquelle</h2>
          <p class="step-sub">Woher kommen die Auftragsdaten? HandOver liest sie automatisch ein.</p>

          <div class="fields">
            <div class="field">
              <label>Datenquelle *</label>
              <div class="source-options">
                <div
                  v-for="s in sourceTypes"
                  :key="s.value"
                  class="source-card"
                  :class="{ selected: form.data_source_type === s.value }"
                  @click="form.data_source_type = s.value"
                >
                  <span class="source-icon">{{ s.icon }}</span>
                  <div>
                    <strong>{{ s.label }}</strong>
                    <p>{{ s.desc }}</p>
                  </div>
                </div>
              </div>
            </div>

            <div class="field" v-if="form.data_source_type === 'csv'">
              <label>CSV-Ordner Pfad</label>
              <input v-model="form.data_source_path" type="text" class="input" placeholder="C:\ERP\Export oder /Users/.../export" />
            </div>

            <div class="field" v-if="form.data_source_type === 'api'">
              <label>API URL</label>
              <input v-model="form.data_source_url" type="text" class="input" placeholder="https://erp.firma.ch/api/orders" />
            </div>
            <div class="field" v-if="form.data_source_type === 'api'">
              <label>API Key</label>
              <input v-model="form.data_source_key" type="password" class="input" placeholder="••••••••••••" />
            </div>
          </div>
        </div>

        <!-- ── Schritt 4: Admin-Account ── -->
        <div class="setup-step" v-if="currentStep === 3">
          <div class="step-icon">👤</div>
          <h2 class="step-title">Admin-Account erstellen</h2>
          <p class="step-sub">Dein persönlicher Administrator-Account — damit kannst du alles einrichten und Benutzer verwalten.</p>

          <div class="fields">
            <div class="field">
              <label>Name *</label>
              <input v-model="form.admin_name" type="text" class="input" placeholder="Dein vollständiger Name" />
            </div>
            <div class="field">
              <label>E-Mail *</label>
              <input v-model="form.admin_email" type="email" class="input" placeholder="admin@firma.ch" />
            </div>
            <div class="field">
              <label>Passwort *</label>
              <input v-model="form.admin_password" type="password" class="input" placeholder="Mindestens 8 Zeichen" />
            </div>
            <div class="field">
              <label>Passwort bestätigen *</label>
              <input v-model="pwConfirm" type="password" class="input" placeholder="••••••••" />
              <span class="field-error" v-if="pwMismatch">Passwörter stimmen nicht überein</span>
            </div>
          </div>
        </div>

        <!-- ── Schritt 5: Bereit ── -->
        <div class="setup-step done" v-if="currentStep === 4">
          <div class="done-check">✓</div>
          <h2 class="step-title">Alles bereit!</h2>
          <p class="step-sub">HandOver ist eingerichtet und startklar. Du kannst jetzt loslegen.</p>
          <div class="done-summary">
            <div class="summary-item"><span>Firma</span><strong>{{ form.company_name }}</strong></div>
            <div class="summary-item"><span>Drucker</span><strong>{{ form.printer_name }}</strong></div>
            <div class="summary-item"><span>Datenquelle</span><strong>{{ sourceLabel }}</strong></div>
            <div class="summary-item"><span>Admin</span><strong>{{ form.admin_email }}</strong></div>
          </div>
        </div>

        <!-- Navigation -->
        <div class="step-nav">
          <button class="btn-back" v-if="currentStep > 0 && currentStep < 4" @click="currentStep--">
            ← Zurück
          </button>

          <button
            class="btn-next"
            v-if="currentStep < 3"
            :disabled="!canProceed"
            @click="currentStep++"
          >
            Weiter →
          </button>

          <button
            class="btn-next"
            v-if="currentStep === 3"
            :disabled="!canFinish || saving"
            @click="finishSetup"
          >
            <span v-if="!saving">Einrichtung abschliessen ✓</span>
            <span v-else class="spinner-sm white"></span>
          </button>

          <button class="btn-next" v-if="currentStep === 4" @click="$emit('setup-complete')">
            HandOver starten →
          </button>
        </div>

      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import api from '../api'

const emit = defineEmits(['setup-complete'])

const currentStep = ref(0)
const saving      = ref(false)
const pwConfirm   = ref('')
const logoPreview = ref(null)
const logoInput   = ref(null)

const form = ref({
  company_name:      '',
  company_address:   '',
  company_logo_b64:  '',
  printer_name:      '',
  data_source_type:  'manual',
  data_source_path:  '',
  data_source_url:   '',
  data_source_key:   '',
  admin_name:        '',
  admin_email:       '',
  admin_password:    '',
})

const wizardSteps = [
  { label: 'Firmendaten' },
  { label: 'Drucker' },
  { label: 'Datenquelle' },
  { label: 'Admin-Account' },
  { label: 'Bereit' },
]

const sourceTypes = [
  { value: 'manual', icon: '✋', label: 'Manuell',      desc: 'Daten von Hand eingeben' },
  { value: 'csv',    icon: '📄', label: 'CSV-Export',   desc: 'Aus einem Ordner lesen' },
  { value: 'api',    icon: '🔗', label: 'API / ERP',    desc: 'Direkte Systemverbindung' },
]

// Drucker-Liste simuliert (in Prod: vom Backend via /settings/printers)
const availablePrinters = ref(['HP LaserJet 400', 'Brother HL-L2350DW', 'Canon PIXMA MX925'])

const pwMismatch  = computed(() => pwConfirm.value && form.value.admin_password !== pwConfirm.value)
const sourceLabel = computed(() => sourceTypes.find(s => s.value === form.value.data_source_type)?.label || '—')

const canProceed  = computed(() => {
  if (currentStep.value === 0) return !!form.value.company_name
  if (currentStep.value === 1) return !!form.value.printer_name
  if (currentStep.value === 2) return !!form.value.data_source_type
  return true
})

const canFinish   = computed(() =>
  form.value.admin_name &&
  form.value.admin_email &&
  form.value.admin_password.length >= 8 &&
  !pwMismatch.value
)

function triggerLogoUpload() { logoInput.value?.click() }

function onLogoUpload(e) {
  const file = e.target.files[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = ev => {
    logoPreview.value       = ev.target.result
    form.value.company_logo_b64 = ev.target.result.split(',')[1]
  }
  reader.readAsDataURL(file)
}

async function finishSetup() {
  saving.value = true
  try {
    await api.post('/settings/setup', form.value)
    currentStep.value = 4
  } catch (e) {
    alert(e.response?.data?.detail || 'Fehler beim Einrichten')
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=DM+Sans:wght@300;400;500&display=swap');

.setup-root {
  display: flex;
  height: 100vh;
  font-family: 'DM Sans', sans-serif;
}

/* ── Brand Panel ─────────────────────────────── */
.setup-brand {
  width: 320px;
  flex-shrink: 0;
  background: #1d1d1f;
  padding: 48px 40px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}
.brand-inner { display: flex; flex-direction: column; gap: 32px; }
.brand-logo {
  width: 48px; height: 48px;
  background: #0071e3;
  border-radius: 13px;
  display: flex; align-items: center; justify-content: center;
  font-family: 'Instrument Serif', serif;
  font-size: 26px; color: white;
}
.brand-name {
  font-family: 'Instrument Serif', serif;
  font-size: 32px; font-weight: 400;
  color: white; letter-spacing: -1px;
}
.brand-tag {
  font-size: 15px; color: #6e6e73;
  font-weight: 300; line-height: 1.5;
}

.wizard-steps { display: flex; flex-direction: column; gap: 0; }
.wstep {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 0;
  border-left: 2px solid #2c2c2e;
  padding-left: 20px;
  margin-left: 13px;
  position: relative;
  transition: border-color 0.3s;
}
.wstep:first-child { padding-top: 0; }
.wstep.active  { border-color: #0071e3; }
.wstep.done    { border-color: #28c840; }
.wstep-dot {
  position: absolute;
  left: -13px;
  width: 24px; height: 24px;
  border-radius: 50%;
  background: #2c2c2e;
  border: 2px solid #3a3a3c;
  display: flex; align-items: center; justify-content: center;
  font-size: 10px; font-weight: 600; color: #6e6e73;
  transition: all 0.3s;
}
.wstep.active .wstep-dot { background: #0071e3; border-color: #0071e3; color: white; }
.wstep.done   .wstep-dot { background: #28c840; border-color: #28c840; color: white; }
.wstep-label { font-size: 13px; color: #6e6e73; transition: color 0.3s; }
.wstep.active .wstep-label { color: white; font-weight: 500; }
.wstep.done   .wstep-label { color: #28c840; }

.brand-footer { font-size: 11px; color: #3a3a3c; }

/* ── Content Panel ───────────────────────────── */
.setup-content {
  flex: 1;
  background: #f5f5f7;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow-y: auto;
  padding: 48px 32px;
}
.setup-inner {
  width: 100%;
  max-width: 540px;
  animation: fadeUp 0.5s ease both;
}

.progress-bar {
  height: 3px;
  background: #e8e8ed;
  border-radius: 2px;
  margin-bottom: 48px;
  overflow: hidden;
}
.progress-fill {
  height: 100%;
  background: #0071e3;
  border-radius: 2px;
  transition: width 0.4s ease;
}

/* ── Step Content ────────────────────────────── */
.setup-step { animation: fadeUp 0.4s ease both; }
.step-icon { font-size: 40px; margin-bottom: 12px; }
.step-title {
  font-family: 'Instrument Serif', serif;
  font-size: 32px; font-weight: 400;
  color: #1d1d1f; letter-spacing: -1px;
  margin-bottom: 8px;
}
.step-sub { font-size: 15px; color: #6e6e73; font-weight: 300; margin-bottom: 36px; line-height: 1.5; }

.fields { display: flex; flex-direction: column; gap: 20px; }
.field  { display: flex; flex-direction: column; gap: 6px; }
.field label {
  font-size: 12px; font-weight: 500;
  color: #1d1d1f; text-transform: uppercase; letter-spacing: 0.04em;
}
.input {
  padding: 13px 16px;
  border: 1.5px solid #e8e8ed;
  border-radius: 12px;
  font-family: 'DM Sans', sans-serif;
  font-size: 15px; color: #1d1d1f;
  outline: none; background: white;
  transition: border-color 0.2s, box-shadow 0.2s;
}
.input:focus {
  border-color: #0071e3;
  box-shadow: 0 0 0 3px rgba(0,113,227,0.1);
}
.select { appearance: none; cursor: pointer; }

.field-error { font-size: 12px; color: #ff3b30; }

/* Logo Upload */
.logo-upload {
  width: 140px; height: 80px;
  border: 2px dashed #e0e0e0;
  border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer; transition: border-color 0.2s; background: white;
}
.logo-upload:hover { border-color: #0071e3; }
.logo-upload.has  { border-style: solid; }
.hidden { display: none; }
.logo-preview { max-height: 60px; max-width: 120px; }
.logo-placeholder { display: flex; flex-direction: column; align-items: center; gap: 4px; color: #98989f; font-size: 12px; }
.logo-placeholder span:first-child { font-size: 24px; }

/* Source Cards */
.source-options { display: flex; flex-direction: column; gap: 10px; }
.source-card {
  display: flex; align-items: center; gap: 16px;
  padding: 16px; border-radius: 12px;
  border: 1.5px solid #e8e8ed; background: white;
  cursor: pointer; transition: all 0.2s;
}
.source-card:hover   { border-color: #c0c0c0; }
.source-card.selected { border-color: #0071e3; background: rgba(0,113,227,0.04); }
.source-icon { font-size: 24px; flex-shrink: 0; }
.source-card strong { font-size: 14px; color: #1d1d1f; display: block; }
.source-card p      { font-size: 12px; color: #98989f; margin-top: 2px; }

.printer-hint {
  font-size: 13px; color: #98989f;
  background: #f5f5f7; padding: 12px 16px;
  border-radius: 10px; line-height: 1.5;
}

/* Done State */
.setup-step.done { display: flex; flex-direction: column; align-items: center; text-align: center; }
.done-check {
  width: 72px; height: 72px;
  background: #28c840; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 32px; color: white; font-weight: 700;
  margin-bottom: 16px;
  animation: popIn 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275) both;
}
.done-summary {
  display: grid; grid-template-columns: 1fr 1fr;
  gap: 12px; width: 100%; margin: 24px 0;
  text-align: left;
}
.summary-item { display: flex; flex-direction: column; gap: 2px; }
.summary-item span   { font-size: 11px; color: #98989f; text-transform: uppercase; letter-spacing: 0.05em; }
.summary-item strong { font-size: 14px; color: #1d1d1f; }

/* Nav Buttons */
.step-nav {
  display: flex; gap: 12px; justify-content: flex-end;
  margin-top: 40px;
}
.btn-next, .btn-back {
  padding: 13px 28px;
  border-radius: 12px;
  font-family: 'DM Sans', sans-serif;
  font-size: 15px; font-weight: 500;
  cursor: pointer; border: none;
  transition: all 0.2s;
  display: flex; align-items: center; gap: 6px;
}
.btn-next { background: #1d1d1f; color: white; }
.btn-next:hover:not(:disabled) { background: #000; transform: translateY(-1px); }
.btn-next:disabled { opacity: 0.4; cursor: not-allowed; }
.btn-back { background: white; color: #6e6e73; border: 1.5px solid #e8e8ed; }
.btn-back:hover { background: #f5f5f7; color: #1d1d1f; }

.spinner-sm {
  width: 16px; height: 16px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
  display: inline-block;
}

@keyframes fadeUp {
  from { opacity: 0; transform: translateY(16px); }
  to   { opacity: 1; transform: translateY(0); }
}
@keyframes spin   { to { transform: rotate(360deg); } }
@keyframes popIn  {
  from { transform: scale(0.4); opacity: 0; }
  to   { transform: scale(1);   opacity: 1; }
}
</style>
