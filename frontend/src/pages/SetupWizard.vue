<template>
  <div class="setup-root">

    <!-- Left Branding -->
    <div class="setup-brand">
      <div class="brand-inner">
        <div class="brand-logo">
          <svg viewBox="0 0 20 20" fill="none">
            <path d="M4 4v12M16 4v12M4 10h12" stroke="white" stroke-width="2.5" stroke-linecap="round"/>
          </svg>
        </div>
        <div>
          <h1 class="brand-name">HandOver</h1>
          <p class="brand-by">by Shoriu</p>
        </div>
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
      <div class="brand-footer">© 2026 Shoriu · 書流</div>
    </div>

    <!-- Right Content -->
    <div class="setup-content">
      <div class="setup-inner">

        <div class="progress-bar">
          <div class="progress-fill" :style="`width:${(currentStep / (wizardSteps.length - 1)) * 100}%`"></div>
        </div>

        <!-- Schritt 1: Firmendaten -->
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
                  <span>🖼️</span>
                  <span>Logo hochladen</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Schritt 2: Drucker -->
        <div class="setup-step" v-if="currentStep === 1">
          <div class="step-icon">🖨️</div>
          <h2 class="step-title">Drucker einrichten</h2>
          <p class="step-sub">Wähle den Netzwerkdrucker für automatischen Dokumentendruck.</p>
          <div class="fields">
            <div class="field">
              <label>Druckername *</label>
              <input v-model="form.printer_name" type="text" class="input" placeholder="z.B. HP LaserJet 400" />
            </div>
            <div class="box info">
              <span>💡</span>
              <span>Den genauen Namen findest du unter<br><strong>Windows → Einstellungen → Drucker & Scanner</strong></span>
            </div>
          </div>
        </div>

        <!-- Schritt 3: Datenquelle -->
        <div class="setup-step" v-if="currentStep === 2">
          <div class="step-icon">📡</div>
          <h2 class="step-title">Datenquelle</h2>
          <p class="step-sub">Woher kommen die Auftragsdaten?</p>
          <div class="fields">
            <div class="field">
              <div class="source-options">
                <div
                  v-for="s in sourceTypes" :key="s.value"
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
              <input v-model="form.data_source_path" type="text" class="input" placeholder="C:\ERP\Export" />
            </div>
            <div class="field" v-if="form.data_source_type === 'api'">
              <label>API URL</label>
              <input v-model="form.data_source_url" type="text" class="input" placeholder="https://erp.firma.ch/api/orders" />
            </div>
            <div class="field" v-if="form.data_source_type === 'api'">
              <label>API Key</label>
              <input v-model="form.data_source_key" type="password" class="input" placeholder="••••••••" />
            </div>

            <!-- Outlook Felder -->
            <template v-if="form.data_source_type === 'outlook'">
              <div class="field">
                <label>Verbindungstyp</label>
                <div class="source-options">
                  <div class="source-card" :class="{ selected: form.outlook_type === 'graph' }" @click="form.outlook_type = 'graph'">
                    <span>☁️</span><div><strong>Microsoft 365</strong><p>M365 Konto</p></div>
                  </div>
                  <div class="source-card" :class="{ selected: form.outlook_type === 'exchange' }" @click="form.outlook_type = 'exchange'">
                    <span>🏢</span><div><strong>Exchange Server</strong><p>On-premise</p></div>
                  </div>
                </div>
              </div>
              <div class="field">
                <label>E-Mail Adresse</label>
                <input v-model="form.outlook_email" type="email" class="input" placeholder="name@firma.ch" />
              </div>
              <div class="field">
                <label>Passwort</label>
                <input v-model="form.outlook_password" type="password" class="input" placeholder="••••••••" />
              </div>
              <template v-if="form.outlook_type === 'graph'">
                <div class="field">
                  <label>Tenant ID</label>
                  <input v-model="form.outlook_tenant_id" type="text" class="input" placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" />
                </div>
                <div class="field">
                  <label>Client ID</label>
                  <input v-model="form.outlook_client_id" type="text" class="input" placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" />
                </div>
              </template>
              <div class="field" v-if="form.outlook_type === 'exchange'">
                <label>Exchange Server</label>
                <input v-model="form.outlook_server" type="text" class="input" placeholder="mail.firma.ch" />
              </div>
            </template>
          </div>
        </div>

        <!-- Schritt 4: Admin-Account -->
        <div class="setup-step" v-if="currentStep === 3">
          <div class="step-icon">👤</div>
          <h2 class="step-title">Admin-Account</h2>
          <p class="step-sub">Dein persönlicher Administrator-Account.</p>
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

        <!-- Schritt 5: Fertig -->
        <div class="setup-step setup-done" v-if="currentStep === 4">
          <div class="done-check">✓</div>
          <h2 class="step-title">Alles bereit!</h2>
          <p class="step-sub">HandOver ist eingerichtet und startklar.</p>
          <div class="done-summary">
            <div class="summary-item"><span>Firma</span><strong>{{ form.company_name }}</strong></div>
            <div class="summary-item"><span>Drucker</span><strong>{{ form.printer_name || '—' }}</strong></div>
            <div class="summary-item"><span>Datenquelle</span><strong>{{ sourceLabel }}</strong></div>
            <div class="summary-item"><span>Admin</span><strong>{{ form.admin_email }}</strong></div>
          </div>
        </div>

        <!-- Navigation -->
        <div class="step-nav">
          <button class="btn-back" v-if="currentStep > 0 && currentStep < 4" @click="currentStep--">← Zurück</button>
          <button class="btn-next" v-if="currentStep < 3" :disabled="!canProceed" @click="currentStep++">Weiter →</button>
          <button class="btn-next" v-if="currentStep === 3" :disabled="!canFinish || saving" @click="finishSetup">
            <span v-if="!saving">Einrichtung abschliessen ✓</span>
            <span v-else class="spinner-sm"></span>
          </button>
          <button class="btn-next" v-if="currentStep === 4" @click="$emit('setup-complete')">HandOver starten →</button>
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
  company_name: '', company_address: '', company_logo_b64: '',
  printer_name: '', data_source_type: 'manual',
  data_source_path: '', data_source_url: '', data_source_key: '',
  outlook_type: 'graph', outlook_email: '', outlook_password: '',
  outlook_tenant_id: '', outlook_client_id: '', outlook_server: '',
  admin_name: '', admin_email: '', admin_password: '',
})

const wizardSteps = [
  { label: 'Firmendaten' }, { label: 'Drucker' },
  { label: 'Datenquelle' }, { label: 'Admin-Account' }, { label: 'Bereit' },
]
const sourceTypes = [
  { value: 'manual',  icon: '✋', label: 'Manuell',          desc: 'Daten von Hand eingeben' },
  { value: 'csv',     icon: '📄', label: 'CSV-Export',       desc: 'Aus einem Ordner lesen' },
  { value: 'api',     icon: '🔗', label: 'API / ERP',        desc: 'Direkte Systemverbindung' },
  { value: 'outlook', icon: '📧', label: 'Outlook / Exchange', desc: 'PDFs direkt aus E-Mails laden' },
]

const pwMismatch  = computed(() => pwConfirm.value && form.value.admin_password !== pwConfirm.value)
const sourceLabel = computed(() => sourceTypes.find(s => s.value === form.value.data_source_type)?.label || '—')
const canProceed  = computed(() => {
  if (currentStep.value === 0) return !!form.value.company_name
  if (currentStep.value === 1) return !!form.value.printer_name
  return true
})
const canFinish = computed(() =>
  form.value.admin_name && form.value.admin_email &&
  form.value.admin_password.length >= 8 && !pwMismatch.value
)

function triggerLogoUpload() { logoInput.value?.click() }
function onLogoUpload(e) {
  const file = e.target.files[0]; if (!file) return
  const reader = new FileReader()
  reader.onload = ev => { logoPreview.value = ev.target.result; form.value.company_logo_b64 = ev.target.result.split(',')[1] }
  reader.readAsDataURL(file)
}
async function finishSetup() {
  saving.value = true
  try { await api.post('/settings/setup', form.value); currentStep.value = 4 }
  catch (e) { alert(e.response?.data?.detail || 'Fehler beim Einrichten') }
  finally { saving.value = false }
}
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=DM+Sans:wght@300;400;500;600&display=swap');

.setup-root { display: flex; height: 100vh; font-family: 'DM Sans', sans-serif; }

/* ── Left Panel ── */
.setup-brand {
  width: 300px; flex-shrink: 0;
  background: linear-gradient(145deg, #1c1c1e 0%, #2c1a1f 100%);
  padding: 48px 36px; display: flex; flex-direction: column; justify-content: space-between;
  position: relative; overflow: hidden;
}
.setup-brand::before {
  content: '書'; position: absolute; bottom: -40px; right: -30px;
  font-size: 240px; color: rgba(255,255,255,0.03); font-family: serif; pointer-events: none;
}
.brand-inner { display: flex; flex-direction: column; gap: 24px; }
.brand-logo {
  width: 44px; height: 44px; border-radius: 12px;
  background: linear-gradient(135deg, #f2a7b8, #c0546a);
  display: flex; align-items: center; justify-content: center;
  box-shadow: 0 4px 16px rgba(192,84,106,0.4);
}
.brand-logo svg { width: 20px; height: 20px; }
.brand-name { font-family: 'Instrument Serif', serif; font-size: 28px; font-weight: 400; color: white; letter-spacing: -0.5px; }
.brand-by   { font-size: 12px; color: rgba(255,255,255,0.3); margin-top: 2px; }
.brand-tag  { font-size: 15px; color: rgba(255,255,255,0.45); font-weight: 300; line-height: 1.6; }
.brand-footer { font-size: 11px; color: rgba(255,255,255,0.2); }

/* Steps */
.wizard-steps { display: flex; flex-direction: column; margin-top: 8px; }
.wstep {
  display: flex; align-items: center; gap: 12px;
  padding: 9px 0 9px 24px;
  border-left: 2px solid rgba(255,255,255,0.08);
  margin-left: 11px; position: relative; transition: border-color 0.3s;
}
.wstep.active { border-color: #c0546a; }
.wstep.done   { border-color: rgba(40,200,64,0.5); }
.wstep-dot {
  position: absolute; left: -12px;
  width: 22px; height: 22px; border-radius: 50%;
  background: rgba(255,255,255,0.05); border: 2px solid rgba(255,255,255,0.12);
  display: flex; align-items: center; justify-content: center;
  font-size: 10px; font-weight: 600; color: rgba(255,255,255,0.3); transition: all 0.3s;
}
.wstep.active .wstep-dot { background: #c0546a; border-color: #c0546a; color: white; }
.wstep.done   .wstep-dot { background: #28c840; border-color: #28c840; color: white; }
.wstep-label { font-size: 13px; color: rgba(255,255,255,0.3); transition: color 0.3s; }
.wstep.active .wstep-label { color: white; font-weight: 500; }
.wstep.done   .wstep-label { color: rgba(40,200,64,0.8); }

/* ── Right Panel ── */
.setup-content { flex: 1; background: #f2f2f7; display: flex; align-items: center; justify-content: center; overflow-y: auto; padding: 48px 32px; }
.setup-inner { width: 100%; max-width: 520px; animation: fadeUp 0.4s ease both; }

.progress-bar { height: 3px; background: #e8e8ed; border-radius: 2px; margin-bottom: 44px; overflow: hidden; }
.progress-fill { height: 100%; background: linear-gradient(90deg, #f2a7b8, #c0546a); border-radius: 2px; transition: width 0.4s ease; }

/* Step */
.setup-step { animation: fadeUp 0.35s ease both; }
.step-icon  { font-size: 36px; margin-bottom: 10px; }
.step-title { font-family: 'Instrument Serif', serif; font-size: 30px; font-weight: 400; color: #1c1c1e; letter-spacing: -0.8px; margin-bottom: 6px; }
.step-sub   { font-size: 15px; color: #6e6e73; font-weight: 300; margin-bottom: 32px; line-height: 1.5; }

.fields { display: flex; flex-direction: column; gap: 18px; }
.field  { display: flex; flex-direction: column; gap: 6px; }
.field label { font-size: 11px; font-weight: 600; color: #1c1c1e; text-transform: uppercase; letter-spacing: 0.05em; }
.input { padding: 12px 16px; border: 1.5px solid #e8e8ed; border-radius: 12px; font-family: 'DM Sans', sans-serif; font-size: 15px; color: #1c1c1e; outline: none; background: white; transition: all 0.2s; width: 100%; }
.input:focus { border-color: #c0546a; box-shadow: 0 0 0 3px rgba(192,84,106,0.1); }
.field-error { font-size: 12px; color: #ff3b30; }

.logo-upload { width: 140px; height: 80px; border: 2px dashed #e0e0e0; border-radius: 12px; display: flex; align-items: center; justify-content: center; cursor: pointer; transition: border-color 0.2s; background: white; }
.logo-upload:hover { border-color: #c0546a; }
.logo-upload.has  { border-style: solid; border-color: #c0546a; }
.hidden { display: none; }
.logo-preview { max-height: 60px; max-width: 120px; border-radius: 6px; }
.logo-placeholder { display: flex; flex-direction: column; align-items: center; gap: 4px; color: #98989f; font-size: 12px; }
.logo-placeholder span:first-child { font-size: 22px; }

.source-options { display: flex; flex-direction: column; gap: 10px; }
.source-card { display: flex; align-items: center; gap: 14px; padding: 14px 16px; border-radius: 12px; border: 1.5px solid #e8e8ed; background: white; cursor: pointer; transition: all 0.15s; }
.source-card:hover    { border-color: #d0d0d0; }
.source-card.selected { border-color: #c0546a; background: rgba(192,84,106,0.04); }
.source-icon { font-size: 22px; flex-shrink: 0; }
.source-card strong { font-size: 14px; color: #1c1c1e; display: block; }
.source-card p      { font-size: 12px; color: #98989f; margin-top: 2px; }

.box { border-radius: 11px; padding: 12px 14px; font-size: 13px; line-height: 1.6; display: flex; gap: 10px; }
.box.info { background: rgba(192,84,106,0.06); border: 1px solid rgba(192,84,106,0.15); color: #8a2a3e; }

/* Done */
.setup-done { display: flex; flex-direction: column; align-items: center; text-align: center; }
.done-check {
  width: 72px; height: 72px;
  background: linear-gradient(135deg, #f2a7b8, #c0546a);
  border-radius: 50%; display: flex; align-items: center; justify-content: center;
  font-size: 30px; color: white; font-weight: 700; margin-bottom: 16px;
  box-shadow: 0 8px 24px rgba(192,84,106,0.35);
  animation: popIn 0.5s cubic-bezier(0.175,0.885,0.32,1.275) both;
}
.done-summary { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; width: 100%; margin: 24px 0; text-align: left; }
.summary-item { background: white; border-radius: 10px; padding: 12px 14px; border: 1px solid #f0f0f0; }
.summary-item span   { font-size: 10px; color: #98989f; text-transform: uppercase; letter-spacing: 0.05em; display: block; margin-bottom: 3px; }
.summary-item strong { font-size: 14px; color: #1c1c1e; font-weight: 500; }

/* Nav */
.step-nav { display: flex; gap: 10px; justify-content: flex-end; margin-top: 36px; }
.btn-next, .btn-back { padding: 12px 26px; border-radius: 12px; font-family: 'DM Sans', sans-serif; font-size: 15px; font-weight: 500; cursor: pointer; border: none; transition: all 0.2s; display: flex; align-items: center; gap: 6px; }
.btn-next { background: linear-gradient(135deg, #e8849a, #c0546a); color: white; box-shadow: 0 2px 12px rgba(192,84,106,0.3); }
.btn-next:hover:not(:disabled) { opacity: 0.9; transform: translateY(-1px); }
.btn-next:disabled { opacity: 0.4; cursor: not-allowed; transform: none; }
.btn-back { background: white; color: #6e6e73; border: 1.5px solid #e8e8ed; }
.btn-back:hover { background: #f5f5f7; color: #1c1c1e; }

.spinner-sm { width: 16px; height: 16px; border: 2px solid rgba(255,255,255,0.3); border-top-color: white; border-radius: 50%; animation: spin 0.7s linear infinite; display: inline-block; }

@keyframes fadeUp { from { opacity: 0; transform: translateY(14px); } to { opacity: 1; transform: translateY(0); } }
@keyframes spin   { to { transform: rotate(360deg); } }
@keyframes popIn  { from { transform: scale(0.4); opacity: 0; } to { transform: scale(1); opacity: 1; } }
</style>
