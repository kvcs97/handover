<template>
  <div class="settings-page">

    <div class="page-header">
      <div>
        <h1 class="page-title">Einstellungen</h1>
        <p class="page-sub">Firmendaten, Drucker und Datenquelle</p>
      </div>
      <button class="btn-save" @click="saveAll" :disabled="saving">
        <span v-if="!saving">Speichern</span>
        <span v-else class="spinner-sm"></span>
      </button>
    </div>

    <div class="settings-grid">

      <!-- ── Firmendaten ── -->
      <div class="settings-card">
        <div class="card-title-row">
          <span class="card-icon">🏢</span>
          <h2 class="card-title">Firmendaten</h2>
        </div>
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
            <label>Firmenlogo</label>
            <div class="logo-upload-area" @click="$refs.logoInput.click()">
              <img v-if="logoPreview" :src="logoPreview" class="logo-preview" />
              <div v-else class="logo-placeholder">
                <span>🖼️</span>
                <p>Logo hochladen</p>
                <small>PNG oder JPG, max. 2MB</small>
              </div>
            </div>
            <input ref="logoInput" type="file" accept="image/*" style="display:none" @change="onLogoChange" />
            <button class="btn-remove-logo" v-if="logoPreview" @click="removeLogo">Logo entfernen</button>
          </div>
        </div>
      </div>

      <!-- ── Drucker ── -->
      <div class="settings-card">
        <div class="card-title-row">
          <span class="card-icon">🖨️</span>
          <h2 class="card-title">Drucker</h2>
        </div>
        <div class="fields">
          <div class="field">
            <label>Druckername</label>
            <input v-model="form.printer_name" type="text" class="input" placeholder="HP LaserJet 400" />
          </div>
          <div class="box info">
            <span>💡</span>
            <div>Den genauen Namen findest du unter<br>
            <strong>Windows → Einstellungen → Bluetooth & Geräte → Drucker & Scanner</strong></div>
          </div>
          <div class="test-row">
            <button class="btn-test" @click="testPrint" :disabled="testingPrint || !form.printer_name">
              <span v-if="!testingPrint">🖨️ Testdruck</span>
              <span v-else>Wird gedruckt…</span>
            </button>
            <span class="test-result success" v-if="testResult === 'ok'">✓ Druckauftrag gesendet</span>
            <span class="test-result error"   v-if="testResult === 'err'">✗ Drucker nicht erreichbar</span>
          </div>
        </div>
      </div>

      <!-- ── Datenquelle ── -->
      <div class="settings-card">
        <div class="card-title-row">
          <span class="card-icon">📡</span>
          <h2 class="card-title">Datenquelle</h2>
        </div>
        <div class="fields">
          <div class="field">
            <label>Typ</label>
            <div class="source-options">
              <div
                v-for="s in sourceTypes" :key="s.value"
                class="source-card"
                :class="{ selected: form.data_source_type === s.value }"
                @click="form.data_source_type = s.value"
              >
                <span>{{ s.icon }}</span>
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
            <label style="margin-top:8px">API Key (optional)</label>
            <input v-model="form.data_source_key" type="password" class="input" placeholder="••••••••" />
          </div>
        </div>
      </div>

      <!-- ── Passwort ändern ── -->
      <div class="settings-card">
        <div class="card-title-row">
          <span class="card-icon">🔐</span>
          <h2 class="card-title">Passwort ändern</h2>
        </div>
        <div class="fields">
          <div class="field">
            <label>Neues Passwort</label>
            <div class="pw-wrap">
              <input v-model="newPassword" :type="showPw ? 'text' : 'password'" class="input" placeholder="Mindestens 8 Zeichen" />
              <button type="button" class="pw-toggle" @click="showPw = !showPw">{{ showPw ? '🙈' : '👁️' }}</button>
            </div>
          </div>
          <div class="field">
            <label>Passwort bestätigen</label>
            <input v-model="newPasswordConfirm" :type="showPw ? 'text' : 'password'" class="input" placeholder="Wiederholen" />
          </div>
          <button class="btn-change-pw" @click="changePassword" :disabled="!newPassword || newPassword !== newPasswordConfirm">
            Passwort speichern
          </button>
          <div class="box success" v-if="pwChanged">✅ Passwort erfolgreich geändert</div>
          <div class="box error"   v-if="pwError">⚠️ {{ pwError }}</div>
        </div>
      </div>

    </div>

    <!-- Save Banner -->
    <div class="save-banner" v-if="saved">✅ Einstellungen gespeichert</div>

  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()

const saving      = ref(false)
const saved       = ref(false)
const testingPrint = ref(false)
const testResult  = ref('')
const showPw      = ref(false)
const newPassword = ref('')
const newPasswordConfirm = ref('')
const pwChanged   = ref(false)
const pwError     = ref('')
const logoPreview = ref('')

const form = ref({
  company_name:     '',
  company_address:  '',
  company_logo_b64: '',
  printer_name:     '',
  data_source_type: 'manual',
  data_source_path: '',
  data_source_url:  '',
  data_source_key:  '',
})

const sourceTypes = [
  { value: 'manual', icon: '✋', label: 'Manuell',    desc: 'Daten von Hand eingeben' },
  { value: 'csv',    icon: '📄', label: 'CSV-Export', desc: 'Aus einem Ordner lesen' },
  { value: 'api',    icon: '🔗', label: 'API / ERP',  desc: 'Direkte Systemverbindung' },
]

async function loadSettings() {
  try {
    const res = await api.get('/settings/all')
    Object.keys(form.value).forEach(key => {
      if (res.data[key] !== undefined) form.value[key] = res.data[key]
    })
    if (form.value.company_logo_b64) {
      logoPreview.value = `data:image/png;base64,${form.value.company_logo_b64}`
    }
  } catch (e) { console.error(e) }
}

async function saveAll() {
  if (!form.value.company_name) return
  saving.value = true
  try {
    for (const [key, value] of Object.entries(form.value)) {
      await api.put(`/settings/${key}`, null, { params: { value } })
    }
    saved.value = true
    setTimeout(() => saved.value = false, 3000)
  } catch (e) { console.error(e) }
  finally { saving.value = false }
}

function onLogoChange(e) {
  const file = e.target.files[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = (ev) => {
    const base64 = ev.target.result.split(',')[1]
    form.value.company_logo_b64 = base64
    logoPreview.value = ev.target.result
  }
  reader.readAsDataURL(file)
}

function removeLogo() {
  form.value.company_logo_b64 = ''
  logoPreview.value = ''
}

async function testPrint() {
  testingPrint.value = true
  testResult.value = ''
  try {
    await api.post('/settings/test-print', { printer_name: form.value.printer_name })
    testResult.value = 'ok'
  } catch {
    testResult.value = 'err'
  } finally {
    testingPrint.value = false
    setTimeout(() => testResult.value = '', 4000)
  }
}

async function changePassword() {
  pwError.value = ''
  pwChanged.value = false
  if (newPassword.value.length < 8) {
    pwError.value = 'Mindestens 8 Zeichen erforderlich'
    return
  }
  try {
    await api.put(`/users/${auth.user.id}`, { password: newPassword.value })
    pwChanged.value = true
    newPassword.value = ''
    newPasswordConfirm.value = ''
    setTimeout(() => pwChanged.value = false, 4000)
  } catch (e) {
    pwError.value = e.response?.data?.detail || 'Fehler beim Ändern'
  }
}

onMounted(loadSettings)
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=DM+Sans:wght@300;400;500&display=swap');

.settings-page { padding: 40px 48px; font-family: 'DM Sans', sans-serif; }

.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 32px; }
.page-title  { font-family: 'Instrument Serif', serif; font-size: 40px; font-weight: 400; color: #1d1d1f; letter-spacing: -1.5px; }
.page-sub    { font-size: 15px; color: #6e6e73; margin-top: 6px; font-weight: 300; }

.btn-save { padding: 11px 24px; background: linear-gradient(135deg, #e8849a, #c0546a); color: white; border: none; border-radius: 12px; font-family: 'DM Sans', sans-serif; font-size: 14px; font-weight: 500; cursor: pointer; transition: background 0.2s; display: flex; align-items: center; gap: 6px; min-width: 110px; justify-content: center; }
.btn-save:hover:not(:disabled) { background: #000; }
.btn-save:disabled { opacity: 0.5; cursor: not-allowed; }

.settings-grid { display: flex; flex-direction: column; gap: 16px; max-width: 640px; }

.settings-card { background: white; border-radius: 16px; border: 1px solid #f0f0f0; padding: 28px; animation: fadeUp 0.4s ease both; }
.card-title-row { display: flex; align-items: center; gap: 12px; margin-bottom: 24px; }
.card-icon  { font-size: 22px; }
.card-title { font-family: 'Instrument Serif', serif; font-size: 22px; font-weight: 400; color: #1d1d1f; letter-spacing: -0.5px; }

.fields { display: flex; flex-direction: column; gap: 16px; }
.field  { display: flex; flex-direction: column; gap: 6px; }
.field label { font-size: 12px; font-weight: 500; color: #1d1d1f; text-transform: uppercase; letter-spacing: 0.04em; }

.input { padding: 12px 16px; border: 1.5px solid #e8e8ed; border-radius: 11px; font-family: 'DM Sans', sans-serif; font-size: 15px; color: #1d1d1f; outline: none; background: white; transition: border-color 0.2s, box-shadow 0.2s; width: 100%; }
.input:focus { border-color: #c0546a; box-shadow: 0 0 0 3px rgba(192,84,106,0.1); }

/* Logo */
.logo-upload-area { border: 2px dashed #e8e8ed; border-radius: 12px; padding: 24px; cursor: pointer; transition: border-color 0.2s; display: flex; align-items: center; justify-content: center; min-height: 100px; }
.logo-upload-area:hover { border-color: #c0546a; }
.logo-placeholder { display: flex; flex-direction: column; align-items: center; gap: 6px; color: #98989f; font-size: 13px; }
.logo-placeholder span { font-size: 28px; }
.logo-placeholder small { font-size: 11px; color: #c8c8c8; }
.logo-preview { max-height: 80px; max-width: 100%; object-fit: contain; border-radius: 8px; }
.btn-remove-logo { background: none; border: none; color: #ff3b30; font-size: 13px; cursor: pointer; text-align: left; font-family: 'DM Sans', sans-serif; padding: 0; }

/* Drucker Test */
.test-row { display: flex; align-items: center; gap: 12px; }
.btn-test { padding: 10px 18px; background: white; border: 1.5px solid #e8e8ed; border-radius: 10px; font-family: 'DM Sans', sans-serif; font-size: 13px; font-weight: 500; cursor: pointer; transition: all 0.15s; color: #1d1d1f; }
.btn-test:hover:not(:disabled) { border-color: #c0546a; color: #0071e3; }
.btn-test:disabled { opacity: 0.4; cursor: not-allowed; }
.test-result { font-size: 13px; font-weight: 500; }
.test-result.success { color: #28c840; }
.test-result.error   { color: #ff3b30; }

/* Datenquelle */
.source-options { display: flex; flex-direction: column; gap: 8px; }
.source-card { display: flex; align-items: center; gap: 12px; padding: 12px 16px; border-radius: 11px; border: 1.5px solid #e8e8ed; background: white; cursor: pointer; transition: all 0.15s; }
.source-card:hover    { border-color: #c0c0c0; }
.source-card.selected { border-color: #c0546a; background: rgba(0,113,227,0.04); }
.source-card > span  { font-size: 20px; flex-shrink: 0; }
.source-card strong { font-size: 14px; color: #1d1d1f; display: block; }
.source-card p      { font-size: 12px; color: #98989f; margin-top: 1px; }

/* Passwort */
.pw-wrap { position: relative; }
.pw-wrap .input { padding-right: 44px; }
.pw-toggle { position: absolute; right: 12px; top: 50%; transform: translateY(-50%); background: none; border: none; cursor: pointer; font-size: 16px; }
.btn-change-pw { padding: 11px 20px; background: linear-gradient(135deg, #e8849a, #c0546a); color: white; border: none; border-radius: 11px; font-family: 'DM Sans', sans-serif; font-size: 14px; font-weight: 500; cursor: pointer; transition: background 0.2s; align-self: flex-start; }
.btn-change-pw:hover:not(:disabled) { background: #000; }
.btn-change-pw:disabled { opacity: 0.4; cursor: not-allowed; }

/* Boxes */
.box { border-radius: 10px; padding: 12px 14px; font-size: 13px; line-height: 1.6; display: flex; gap: 8px; }
.box.info    { background: rgba(192,84,106,0.06);  border: 1px solid rgba(192,84,106,0.15);  color: #8a2a3e; }
.box.success { background: rgba(40,200,64,0.07);  border: 1px solid rgba(40,200,64,0.2);   color: #1a6e28; }
.box.error   { background: rgba(255,59,48,0.07);  border: 1px solid rgba(255,59,48,0.2);   color: #c0392b; }

/* Save Banner */
.save-banner { position: fixed; bottom: 32px; left: 50%; transform: translateX(-50%); background: linear-gradient(135deg, #e8849a, #c0546a); color: white; padding: 12px 28px; border-radius: 980px; font-size: 14px; font-weight: 500; box-shadow: 0 8px 32px rgba(0,0,0,0.2); animation: fadeUp 0.3s ease both; z-index: 100; }

.spinner-sm { width: 15px; height: 15px; border: 2px solid rgba(255,255,255,0.3); border-top-color: white; border-radius: 50%; animation: spin 0.7s linear infinite; display: inline-block; }

@keyframes fadeUp { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
@keyframes spin   { to { transform: rotate(360deg); } }
</style>
