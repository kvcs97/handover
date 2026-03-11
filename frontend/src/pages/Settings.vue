<template>
  <div class="settings-page">

    <div class="page-header">
      <div>
        <h1 class="page-title">Einstellungen</h1>
        <p class="page-sub">Firmendaten, Drucker und Datenquelle</p>
      </div>
      <button class="btn-save" @click="saveAll" :disabled="saving">
        <span v-if="!saving">Speichern</span>
        <span v-else class="spinner-sm white"></span>
      </button>
    </div>

    <div class="settings-grid">

      <!-- Firmendaten -->
      <div class="settings-card">
        <div class="card-title-row">
          <span class="card-icon">🏢</span>
          <h2 class="card-title">Firmendaten</h2>
        </div>
        <div class="fields">
          <div class="field">
            <label>Firmenname</label>
            <input v-model="form.company_name" type="text" class="input" placeholder="Muster AG" />
          </div>
          <div class="field">
            <label>Adresse</label>
            <input v-model="form.company_address" type="text" class="input" placeholder="Musterstrasse 1, 9000 St. Gallen" />
          </div>
        </div>
      </div>

      <!-- Drucker -->
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
            <span>Den genauen Namen findest du unter Windows → Einstellungen → Bluetooth & Geräte → Drucker.</span>
          </div>
        </div>
      </div>

      <!-- Datenquelle -->
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
          </div>
        </div>
      </div>

    </div>

    <div class="save-banner" v-if="saved">✅ Einstellungen gespeichert</div>

  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api'

const saving = ref(false)
const saved  = ref(false)

const form = ref({
  company_name:     '',
  company_address:  '',
  printer_name:     '',
  data_source_type: 'manual',
  data_source_path: '',
  data_source_url:  '',
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
  } catch (e) { console.error(e) }
}

async function saveAll() {
  saving.value = true
  try {
    for (const [key, value] of Object.entries(form.value)) {
      await api.put(`/settings/${key}?value=${encodeURIComponent(value)}`)
    }
    saved.value = true
    setTimeout(() => saved.value = false, 3000)
  } catch (e) { console.error(e) }
  finally { saving.value = false }
}

onMounted(loadSettings)
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=DM+Sans:wght@300;400;500&display=swap');

.settings-page { padding: 40px 48px; font-family: 'DM Sans', sans-serif; }

.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 32px; }
.page-title  { font-family: 'Instrument Serif', serif; font-size: 40px; font-weight: 400; color: #1d1d1f; letter-spacing: -1.5px; }
.page-sub    { font-size: 15px; color: #6e6e73; margin-top: 6px; font-weight: 300; }

.btn-save { padding: 11px 24px; background: #1d1d1f; color: white; border: none; border-radius: 12px; font-family: 'DM Sans', sans-serif; font-size: 14px; font-weight: 500; cursor: pointer; transition: background 0.2s; display: flex; align-items: center; gap: 6px; min-width: 100px; justify-content: center; }
.btn-save:hover:not(:disabled) { background: #000; }
.btn-save:disabled { opacity: 0.5; cursor: not-allowed; }

.settings-grid { display: flex; flex-direction: column; gap: 16px; max-width: 640px; }

.settings-card { background: white; border-radius: 16px; border: 1px solid #f0f0f0; padding: 28px; }
.card-title-row { display: flex; align-items: center; gap: 12px; margin-bottom: 24px; }
.card-icon  { font-size: 22px; }
.card-title { font-family: 'Instrument Serif', serif; font-size: 22px; font-weight: 400; color: #1d1d1f; letter-spacing: -0.5px; }

.fields { display: flex; flex-direction: column; gap: 16px; }
.field  { display: flex; flex-direction: column; gap: 6px; }
.field label { font-size: 12px; font-weight: 500; color: #1d1d1f; text-transform: uppercase; letter-spacing: 0.04em; }
.input { padding: 12px 16px; border: 1.5px solid #e8e8ed; border-radius: 11px; font-family: 'DM Sans', sans-serif; font-size: 15px; color: #1d1d1f; outline: none; background: white; transition: border-color 0.2s, box-shadow 0.2s; }
.input:focus { border-color: #0071e3; box-shadow: 0 0 0 3px rgba(0,113,227,0.1); }

.source-options { display: flex; flex-direction: column; gap: 8px; }
.source-card { display: flex; align-items: center; gap: 12px; padding: 12px 16px; border-radius: 11px; border: 1.5px solid #e8e8ed; background: white; cursor: pointer; transition: all 0.15s; }
.source-card:hover    { border-color: #c0c0c0; }
.source-card.selected { border-color: #0071e3; background: rgba(0,113,227,0.04); }
.source-card > span  { font-size: 20px; flex-shrink: 0; }
.source-card strong { font-size: 14px; color: #1d1d1f; display: block; }
.source-card p      { font-size: 12px; color: #98989f; margin-top: 1px; }

.box { border-radius: 10px; padding: 12px 14px; font-size: 13px; line-height: 1.5; display: flex; gap: 8px; }
.box.info { background: rgba(0,113,227,0.07); border: 1px solid rgba(0,113,227,0.15); color: #004a99; }

.save-banner { position: fixed; bottom: 32px; left: 50%; transform: translateX(-50%); background: #1d1d1f; color: white; padding: 12px 28px; border-radius: 980px; font-size: 14px; font-weight: 500; box-shadow: 0 8px 32px rgba(0,0,0,0.2); animation: fadeUp 0.3s ease both; }

.spinner-sm { width: 15px; height: 15px; border: 2px solid rgba(255,255,255,0.3); border-top-color: white; border-radius: 50%; animation: spin 0.7s linear infinite; display: inline-block; }

@keyframes fadeUp { from { opacity: 0; transform: translateX(-50%) translateY(8px); } to { opacity: 1; transform: translateX(-50%) translateY(0); } }
@keyframes spin   { to { transform: rotate(360deg); } }
</style>
