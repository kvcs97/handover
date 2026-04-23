<template>
  <div class="settings-page">

    <div class="page-header">
      <div>
        <h1 class="page-title">Einstellungen</h1>
        <p class="page-sub">Firmendaten, Drucker und Datenquelle</p>
        <p class="admin-hint" v-if="auth.isAdmin">Diese Einstellungen gelten für alle Benutzer</p>
      </div>
      <button class="btn-save" v-if="auth.isAdmin" @click="saveAll" :disabled="saving">
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
            <input v-model="form.company_name" type="text" class="input" placeholder="Muster AG" :disabled="!auth.isAdmin" />
          </div>
          <div class="field">
            <label>Adresse</label>
            <input v-model="form.company_address" type="text" class="input" placeholder="Musterstrasse 1, 9000 St. Gallen" :disabled="!auth.isAdmin" />
          </div>
          <div class="field">
            <label>Archiv-Ordner</label>
            <div class="input-with-btn">
              <input v-model="form.archive_path" type="text" class="input" placeholder="%USERPROFILE%\.handover\archive" :disabled="!auth.isAdmin" />
              <button class="btn-browse" v-if="auth.isAdmin" @click="pickArchiveFolder">Ordner wählen</button>
            </div>
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
            <div class="printer-field">
              <span class="printer-display" :class="{ empty: !form.printer_name }">
                <span v-if="form.printer_name">🖨️ {{ form.printer_name }}</span>
                <span v-else>Kein Drucker gewählt</span>
              </span>
              <button
                class="btn-pick-printer"
                v-if="auth.isAdmin"
                @click="showPrinterPicker = true"
              >
                Auswählen
              </button>
            </div>
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
                :class="{ selected: form.data_source_type === s.value, disabled: !auth.isAdmin }"
                @click="auth.isAdmin && (form.data_source_type = s.value)"
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
            <input v-model="form.data_source_path" type="text" class="input" placeholder="C:\ERP\Export" :disabled="!auth.isAdmin" />
          </div>
          <div class="field" v-if="form.data_source_type === 'api'">
            <label>API URL</label>
            <input v-model="form.data_source_url" type="text" class="input" placeholder="https://erp.firma.ch/api/orders" :disabled="!auth.isAdmin" />
            <label style="margin-top:8px">API Key (optional)</label>
            <input v-model="form.data_source_key" type="password" class="input" placeholder="••••••••" :disabled="!auth.isAdmin" />
          </div>
        </div>
      </div>

      <!-- ── Outlook Konfiguration ── -->
      <div class="settings-card" v-if="form.data_source_type === 'outlook'">
        <div class="card-title-row">
          <span class="card-icon">📧</span>
          <h2 class="card-title">Outlook Konfiguration</h2>
        </div>
        <div class="fields">
          <div class="field">
            <label>Verbindungstyp</label>
            <div class="source-options">
              <div class="source-card" :class="{ selected: form.outlook_type === 'imap' }" @click="form.outlook_type = 'imap'">
                <span>📬</span>
                <div><strong>IMAP</strong><p>Outlook.com, Hotmail, Gmail — kein Azure nötig</p></div>
              </div>
              <div class="source-card" :class="{ selected: form.outlook_type === 'graph' }" @click="form.outlook_type = 'graph'">
                <span>☁️</span>
                <div><strong>Microsoft 365</strong><p>Firmen M365 mit Azure App Registration</p></div>
              </div>
              <div class="source-card" :class="{ selected: form.outlook_type === 'exchange' }" @click="form.outlook_type = 'exchange'">
                <span>🏢</span>
                <div><strong>Exchange Server</strong><p>Firmen-interner Exchange on-premise</p></div>
              </div>
            </div>
          </div>

          <div class="field">
            <label>E-Mail Adresse</label>
            <input v-model="form.outlook_email" type="email" class="input" placeholder="name@outlook.com" />
          </div>

          <div class="field">
            <label>Passwort</label>
            <div class="pw-wrap">
              <input v-model="form.outlook_password" :type="showOutlookPw ? 'text' : 'password'" class="input" placeholder="••••••••" />
              <button type="button" class="pw-toggle" @click="showOutlookPw = !showOutlookPw">{{ showOutlookPw ? '🙈' : '👁️' }}</button>
            </div>
          </div>

          <!-- IMAP -->
          <template v-if="form.outlook_type === 'imap'">
            <div class="field">
              <label>Tenant ID</label>
              <input v-model="form.outlook_tenant_id" type="text" class="input" placeholder="2be3b1aa-4b43-4a9e-8842-f20980919039" />
            </div>
            <div class="field">
              <label>Client ID</label>
              <input v-model="form.outlook_client_id" type="text" class="input" placeholder="030d437c-961a-49a4-b088-f2f493d9b71d" />
            </div>

            <!-- Login Status -->
            <div class="oauth-status" v-if="outlookLoggedIn">
              <span class="oauth-badge">✓ Mit Microsoft angemeldet</span>
              <span class="oauth-email">{{ form.outlook_email }}</span>
            </div>

            <!-- Device Flow Login -->
            <div class="device-flow" v-if="deviceFlowData">
              <div class="box info">
                <span>📱</span>
                <div>
                  <strong>Schritt 1:</strong> Gehe auf <strong>{{ deviceFlowData.verification_url }}</strong><br>
                  <strong>Schritt 2:</strong> Code eingeben: <code class="device-code">{{ deviceFlowData.user_code }}</code><br>
                  <strong>Schritt 3:</strong> Mit Microsoft anmelden → dann hier auf "Login bestätigen" klicken
                </div>
              </div>
              <div class="device-flow-actions">
                <button class="btn-test" @click="openDeviceUrl">🌐 Browser öffnen</button>
                <button class="btn-save" @click="completeDeviceFlow" :disabled="completingFlow">
                  <span v-if="!completingFlow">✓ Login bestätigen</span>
                  <span v-else class="spinner-sm"></span>
                </button>
              </div>
            </div>

            <button class="btn-ms-login" @click="startMicrosoftLogin" :disabled="startingLogin || !form.outlook_email || !form.outlook_client_id">
              <span v-if="!startingLogin">
                <img src="https://learn.microsoft.com/en-us/azure/active-directory/develop/media/howto-add-branding-in-apps/ms-symbollockup_mssymbol_19.svg" style="width:16px;vertical-align:middle;margin-right:6px">
                Mit Microsoft anmelden
              </span>
              <span v-else class="spinner-sm"></span>
            </button>
          </template>

          <!-- Nur M365 -->
          <template v-if="form.outlook_type === 'graph'">
            <div class="field">
              <label>Tenant ID</label>
              <input v-model="form.outlook_tenant_id" type="text" class="input" placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" />
            </div>
            <div class="field">
              <label>Client ID (App Registration)</label>
              <input v-model="form.outlook_client_id" type="text" class="input" placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" />
            </div>
            <div class="box info">
              <span>💡</span>
              <div>Tenant ID und Client ID findest du im <strong>Azure Portal → App Registrations</strong>. Die App braucht die Berechtigung <code>Mail.Read</code>.</div>
            </div>
          </template>

          <!-- Nur Exchange -->
          <div class="field" v-if="form.outlook_type === 'exchange'">
            <label>Exchange Server</label>
            <input v-model="form.outlook_server" type="text" class="input" placeholder="mail.firma.ch" />
          </div>

          <!-- Verbindung testen -->
          <div class="test-row">
            <button class="btn-test" @click="testOutlook" :disabled="testingOutlook || !form.outlook_email">
              <span v-if="!testingOutlook">📧 Verbindung testen</span>
              <span v-else>Wird getestet…</span>
            </button>
            <span class="test-result success" v-if="outlookTestResult === 'ok'">✓ Verbindung erfolgreich</span>
            <span class="test-result error"   v-if="outlookTestResult === 'err'">✗ Verbindung fehlgeschlagen</span>
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
            <label>Aktuelles Passwort</label>
            <div class="pw-wrap">
              <input v-model="currentPassword" :type="showPw ? 'text' : 'password'" class="input" placeholder="••••••••" autocomplete="current-password" />
              <button type="button" class="pw-toggle" @click="showPw = !showPw">{{ showPw ? '🙈' : '👁️' }}</button>
            </div>
          </div>
          <div class="field">
            <label>Neues Passwort</label>
            <input v-model="newPassword" :type="showPw ? 'text' : 'password'" class="input" placeholder="Mindestens 8 Zeichen" autocomplete="new-password" />
          </div>
          <div class="field">
            <label>Passwort bestätigen</label>
            <input v-model="newPasswordConfirm" :type="showPw ? 'text' : 'password'" class="input" placeholder="Wiederholen" autocomplete="new-password" />
          </div>
          <button class="btn-change-pw" @click="changePassword"
            :disabled="!currentPassword || !newPassword || newPassword !== newPasswordConfirm || changingPw">
            <span v-if="!changingPw">Passwort speichern</span>
            <span v-else class="spinner-sm"></span>
          </button>
          <div class="box success" v-if="pwChanged">✅ Passwort erfolgreich geändert</div>
          <div class="box error"   v-if="pwError">⚠️ {{ pwError }}</div>
        </div>
      </div>

      <!-- ── Lizenz ── -->
      <div class="settings-card">
        <div class="card-title-row">
          <span class="card-icon">🔑</span>
          <h2 class="card-title">Lizenz</h2>
        </div>
        <div class="fields">
          <div class="license-status" v-if="licenseInfo">
            <div class="license-valid" v-if="licenseInfo.valid">
              <div class="license-badge valid">✓ Aktiv</div>
              <div class="license-details">
                <div class="meta-row"><span>Plan</span><strong>{{ licenseInfo.plan === 'complete' ? 'Complete' : 'Essential' }}</strong></div>
                <div class="meta-row"><span>Kunde</span><strong>{{ licenseInfo.customer }}</strong></div>
                <div class="meta-row"><span>Läuft ab</span><strong>{{ licenseInfo.expires }}</strong></div>
                <div class="meta-row"><span>Verbleibend</span><strong :class="licenseInfo.days_left < 30 ? 'text-warn' : ''">{{ licenseInfo.days_left }} Tage</strong></div>
              </div>
            </div>
            <div v-else>
              <div class="license-badge invalid">✗ Ungültig</div>
              <p class="license-error">{{ licenseInfo.error }}</p>
            </div>
          </div>
          <div class="field">
            <label>Lizenzschlüssel eingeben</label>
            <input v-model="licenseKey" type="text" class="input license-input" placeholder="XXXXX-XXXXX-XXXXX-XXXXX-XXXXX" />
          </div>
          <button class="btn-activate" @click="activateLicense" :disabled="!licenseKey || activating">
            <span v-if="!activating">🔑 Lizenz aktivieren</span>
            <span v-else class="spinner-sm"></span>
          </button>
          <div class="box error"   v-if="licenseError">⚠️ {{ licenseError }}</div>
          <div class="box success" v-if="licenseSuccess">✅ Lizenz erfolgreich aktiviert!</div>
        </div>
      </div>

    </div>

    <!-- Save Banner -->
    <div class="save-banner" v-if="saved">✅ Einstellungen gespeichert</div>
    <div class="save-banner error" v-if="saveError">⚠ {{ saveError }}</div>

    <!-- Drucker-Picker Modal -->
    <PrinterPickerModal
      v-if="showPrinterPicker"
      @select="onPrinterSelected"
      @close="showPrinterPicker = false"
    />

  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api'
import { useAuthStore } from '../stores/auth'
import { open as openDialog } from '@tauri-apps/plugin-dialog'
import PrinterPickerModal from '../components/PrinterPickerModal.vue'

const auth = useAuthStore()

const saving      = ref(false)
const saved       = ref(false)
const showPrinterPicker = ref(false)
const testingPrint      = ref(false)
const testResult        = ref('')
const showPw            = ref(false)
const showOutlookPw     = ref(false)
const testingOutlook    = ref(false)
const outlookTestResult = ref('')
const outlookLoggedIn   = ref(false)
const deviceFlowData    = ref(null)
const startingLogin     = ref(false)
const completingFlow    = ref(false)

async function startMicrosoftLogin() {
  startingLogin.value = true
  deviceFlowData.value = null
  try {
    const res = await api.post('/outlook/login/start', {
      client_id: form.value.outlook_client_id,
      tenant_id: form.value.outlook_tenant_id,
      email:     form.value.outlook_email,
    })
    deviceFlowData.value = res.data
  } catch (e) {
    alert('Login konnte nicht gestartet werden: ' + (e.response?.data?.detail || e.message))
  } finally {
    startingLogin.value = false
  }
}

function openDeviceUrl() {
  if (deviceFlowData.value?.verification_url) {
    window.open(deviceFlowData.value.verification_url, '_blank')
  }
}

async function completeDeviceFlow() {
  completingFlow.value = true
  try {
    await api.post('/outlook/login/complete', {
      client_id:  form.value.outlook_client_id,
      tenant_id:  form.value.outlook_tenant_id,
      flow_data:  deviceFlowData.value.flow_data,
    })
    outlookLoggedIn.value = true
    deviceFlowData.value  = null
    outlookTestResult.value = 'ok'
    setTimeout(() => outlookTestResult.value = '', 3000)
  } catch (e) {
    alert('Login fehlgeschlagen: ' + (e.response?.data?.detail || e.message))
  } finally {
    completingFlow.value = false
  }
}
const currentPassword    = ref('')
const newPassword        = ref('')
const newPasswordConfirm = ref('')
const pwChanged   = ref(false)
const pwError     = ref('')
const changingPw  = ref(false)
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
  outlook_type:     'imap',
  outlook_email:    '',
  outlook_password: '',
  outlook_tenant_id: '',
  outlook_client_id: '',
  outlook_server:   '',
  outlook_imap_server: '',
  archive_path: '',
})

const sourceTypes = [
  { value: 'manual',  icon: '✋', label: 'Manuell',          desc: 'Daten von Hand eingeben' },
  { value: 'csv',     icon: '📄', label: 'CSV-Export',       desc: 'Aus einem Ordner lesen' },
  { value: 'api',     icon: '🔗', label: 'API / ERP',        desc: 'Direkte Systemverbindung' },
  { value: 'outlook', icon: '📧', label: 'Outlook / Exchange', desc: 'PDFs direkt aus E-Mails laden' },
]

async function loadSettings() {
  try {
    const res = await api.get('/settings/global')
    Object.keys(form.value).forEach(key => {
      if (res.data[key] !== undefined) form.value[key] = res.data[key]
    })
    if (res.data.outlook_logged_in) outlookLoggedIn.value = true
    if (form.value.company_logo_b64) {
      logoPreview.value = `data:image/png;base64,${form.value.company_logo_b64}`
    }
  } catch (e) { console.error(e) }
}

const saveError = ref('')

// Felder die nicht überschrieben werden sollen wenn leer
// (gespeicherten Wert nicht wegwerfen wenn Formular leer geladen wurde)
const PROTECTED_IF_EMPTY = ['outlook_password']

async function saveAll() {
  if (!form.value.company_name) {
    saveError.value = 'Firmenname ist ein Pflichtfeld'
    setTimeout(() => saveError.value = '', 4000)
    return
  }
  saving.value = true
  saveError.value = ''
  const failed = []
  try {
    for (const [key, value] of Object.entries(form.value)) {
      if (PROTECTED_IF_EMPTY.includes(key) && (!value || value === '')) continue
      try {
        await api.put(`/settings/${key}`, null, { params: { value: value ?? '' } })
      } catch (e) {
        failed.push(`${key}: ${e.response?.data?.detail || e.message}`)
      }
    }
    if (failed.length) {
      saveError.value = 'Fehler beim Speichern: ' + failed.join(' · ')
      setTimeout(() => saveError.value = '', 6000)
    } else {
      saved.value = true
      setTimeout(() => saved.value = false, 3000)
    }
  } catch (e) {
    console.error(e)
    saveError.value = e.response?.data?.detail || e.message || 'Speichern fehlgeschlagen'
    setTimeout(() => saveError.value = '', 5000)
  } finally { saving.value = false }
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

async function pickArchiveFolder() {
  const selected = await openDialog({ directory: true, multiple: false })
  if (selected) form.value.archive_path = selected
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

async function testOutlook() {
  testingOutlook.value = true
  outlookTestResult.value = ''
  try {
    await api.post('/outlook/test', {
      outlook_type:        form.value.outlook_type,
      outlook_email:       form.value.outlook_email,
      outlook_password:    form.value.outlook_password,
      outlook_tenant_id:   form.value.outlook_tenant_id,
      outlook_client_id:   form.value.outlook_client_id,
      outlook_server:      form.value.outlook_server,
      outlook_imap_server: form.value.outlook_imap_server,
    })
    outlookTestResult.value = 'ok'
  } catch {
    outlookTestResult.value = 'err'
  } finally {
    testingOutlook.value = false
    setTimeout(() => outlookTestResult.value = '', 4000)
  }
}

async function changePassword() {
  pwError.value = ''
  pwChanged.value = false
  if (newPassword.value.length < 8) {
    pwError.value = 'Mindestens 8 Zeichen erforderlich'
    return
  }
  if (newPassword.value !== newPasswordConfirm.value) {
    pwError.value = 'Passwörter stimmen nicht überein'
    return
  }
  changingPw.value = true
  try {
    await api.post('/auth/change-password', {
      current_password: currentPassword.value,
      new_password:     newPassword.value,
    })
    pwChanged.value = true
    currentPassword.value = ''
    newPassword.value = ''
    newPasswordConfirm.value = ''
    setTimeout(() => pwChanged.value = false, 4000)
  } catch (e) {
    pwError.value = e.response?.data?.detail || 'Fehler beim Ändern'
    setTimeout(() => pwError.value = '', 5000)
  } finally {
    changingPw.value = false
  }
}

function onPrinterSelected(name) {
  form.value.printer_name = name
}

onMounted(async () => {
  await loadSettings()
  await loadLicense()
})

// ── Lizenz ────────────────────────────────────
const licenseKey     = ref('')
const licenseInfo    = ref(null)
const licenseError   = ref('')
const licenseSuccess = ref(false)
const activating     = ref(false)

async function loadLicense() {
  try {
    const res = await api.get('/license/status')
    licenseInfo.value = res.data
  } catch {}
}

async function activateLicense() {
  licenseError.value = ''; licenseSuccess.value = false; activating.value = true
  try {
    const res = await api.post('/license/activate', { license_key: licenseKey.value })
    licenseInfo.value = res.data
    licenseSuccess.value = true
    licenseKey.value = ''
    setTimeout(() => licenseSuccess.value = false, 4000)
  } catch (e) {
    licenseError.value = e.response?.data?.detail || 'Aktivierung fehlgeschlagen'
    setTimeout(() => licenseError.value = '', 4000)
  } finally { activating.value = false }
}
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=DM+Sans:wght@300;400;500&display=swap');

.settings-page { padding: 40px 48px; font-family: 'DM Sans', sans-serif; }

.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 32px; }
.page-title  { font-family: 'Instrument Serif', serif; font-size: 40px; font-weight: 400; color: #1d1d1f; letter-spacing: -1.5px; }
.page-sub    { font-size: 15px; color: #6e6e73; margin-top: 6px; font-weight: 300; }

.admin-hint { font-size: 12px; color: #c0546a; margin-top: 4px; font-weight: 500; }

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

/* Archiv-Pfad */
.input-with-btn { display: flex; gap: 8px; }
.input-with-btn .input { flex: 1; }
.btn-browse { padding: 10px 16px; background: #f2f2f7; border: 1px solid #e5e5ea; border-radius: 10px; font-family: 'DM Sans', sans-serif; font-size: 14px; cursor: pointer; white-space: nowrap; }
.btn-browse:hover { background: #e8e8ed; }

/* Logo */
.logo-upload-area { border: 2px dashed #e8e8ed; border-radius: 12px; padding: 24px; cursor: pointer; transition: border-color 0.2s; display: flex; align-items: center; justify-content: center; min-height: 100px; }
.logo-upload-area:hover { border-color: #c0546a; }
.logo-placeholder { display: flex; flex-direction: column; align-items: center; gap: 6px; color: #98989f; font-size: 13px; }
.logo-placeholder span { font-size: 28px; }
.logo-placeholder small { font-size: 11px; color: #c8c8c8; }
.logo-preview { max-height: 80px; max-width: 100%; object-fit: contain; border-radius: 8px; }
.btn-remove-logo { background: none; border: none; color: #ff3b30; font-size: 13px; cursor: pointer; text-align: left; font-family: 'DM Sans', sans-serif; padding: 0; }

/* Drucker-Picker Feld */
.printer-field {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 14px;
  border: 1.5px solid #e8e8ed;
  border-radius: 11px;
  background: white;
  transition: border-color 0.2s;
}
.printer-field:hover { border-color: #c0c0c0; }
.printer-display {
  flex: 1; font-size: 14px; color: #1d1d1f;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.printer-display.empty { color: #98989f; font-style: italic; }
.btn-pick-printer {
  padding: 7px 14px; background: #f2f2f7;
  border: 1px solid #e5e5ea; border-radius: 8px;
  font-family: 'DM Sans', sans-serif; font-size: 13px; font-weight: 500;
  color: #1d1d1f; cursor: pointer; transition: all 0.15s; white-space: nowrap;
}
.btn-pick-printer:hover { background: #e8e8ed; border-color: #c0546a; color: #c0546a; }

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
.source-card.disabled { opacity: 0.6; cursor: default; pointer-events: none; }
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
.save-banner { position: fixed; bottom: 32px; left: 50%; transform: translateX(-50%); background: linear-gradient(135deg, #e8849a, #c0546a); color: white; padding: 12px 28px; border-radius: 980px; font-size: 14px; font-weight: 500; box-shadow: 0 8px 32px rgba(0,0,0,0.2); animation: fadeUp 0.3s ease both; z-index: 100; max-width: 80vw; text-align: center; }
.save-banner.error { background: linear-gradient(135deg, #ff9a87, #c03a2b); }

.spinner-sm { width: 15px; height: 15px; border: 2px solid rgba(255,255,255,0.3); border-top-color: white; border-radius: 50%; animation: spin 0.7s linear infinite; display: inline-block; }

@keyframes fadeUp { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }

/* ── Microsoft Login ── */
.btn-ms-login { padding: 11px 20px; background: white; border: 1.5px solid #e8e8ed; border-radius: 11px; font-family: 'DM Sans', sans-serif; font-size: 14px; font-weight: 500; cursor: pointer; transition: all 0.2s; color: #1c1c1e; display: flex; align-items: center; gap: 8px; }
.btn-ms-login:hover:not(:disabled) { border-color: #0078d4; color: #0078d4; background: rgba(0,120,212,0.04); }
.btn-ms-login:disabled { opacity: 0.4; cursor: not-allowed; }
.oauth-status { display: flex; align-items: center; gap: 10px; padding: 10px 14px; background: rgba(40,167,69,0.07); border: 1px solid rgba(40,167,69,0.2); border-radius: 10px; }
.oauth-badge { font-size: 13px; font-weight: 600; color: #1a7a2e; }
.oauth-email { font-size: 12px; color: #6e6e73; }
.device-flow { display: flex; flex-direction: column; gap: 10px; }
.device-flow-actions { display: flex; gap: 8px; }
.device-code { background: #f5f5f7; padding: 2px 8px; border-radius: 6px; font-family: monospace; font-size: 15px; font-weight: 700; color: #c0546a; letter-spacing: 0.05em; }
.license-status { margin-bottom: 8px; }
.license-badge { display: inline-block; font-size: 12px; font-weight: 600; padding: 4px 12px; border-radius: 980px; margin-bottom: 12px; }
.license-badge.valid   { background: rgba(40,167,69,0.1); color: #1a7a2e; }
.license-badge.invalid { background: rgba(255,59,48,0.1); color: #c0392b; }
.license-details { display: flex; flex-direction: column; gap: 8px; margin-bottom: 8px; }
.license-error { font-size: 13px; color: #c0392b; margin-top: 4px; }
.license-input { font-family: monospace !important; letter-spacing: 0.08em; }
.text-warn { color: #c07800; }
.btn-activate { padding: 11px 20px; background: linear-gradient(135deg, #e8849a, #c0546a); color: white; border: none; border-radius: 11px; font-family: 'DM Sans', sans-serif; font-size: 14px; font-weight: 500; cursor: pointer; transition: opacity 0.2s; display: flex; align-items: center; gap: 6px; box-shadow: 0 2px 10px rgba(192,84,106,0.25); align-self: flex-start; }
.btn-activate:hover:not(:disabled) { opacity: 0.9; }
.btn-activate:disabled { opacity: 0.4; cursor: not-allowed; }
@keyframes spin   { to { transform: rotate(360deg); } }
</style>

<!-- Diese Zeile in der Settings.vue sourceTypes Array ergänzen:
     { value: 'outlook', icon: '📧', label: 'Outlook / Exchange', desc: 'PDFs aus E-Mails laden' }

     Und folgendes Outlook-Konfigurationsfeld nach der Datenquelle-Karte einfügen:
-->
