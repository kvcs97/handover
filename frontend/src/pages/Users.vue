<template>
  <div class="users-page">
    <div class="page-header">
      <div>
        <p class="page-eyebrow">Verwaltung</p>
        <h1 class="page-title">Benutzer</h1>
      </div>
      <button class="btn-primary" @click="openCreate">+ Neuer Benutzer</button>
    </div>

    <div class="table-card">
      <div class="table-loading" v-if="loading"><div class="skeleton" v-for="i in 5" :key="i"></div></div>
      <div class="empty-state" v-else-if="!users.length"><span>👥</span><p>Noch keine Benutzer</p></div>
      <table class="users-table" v-else>
        <thead><tr><th>Name</th><th>E-Mail</th><th>Rolle</th><th>Status</th><th>Erstellt</th><th>Aktionen</th></tr></thead>
        <tbody>
          <tr v-for="u in users" :key="u.id" class="user-row" :class="{ inactive: !u.active }">
            <td>
              <div class="user-cell">
                <div class="user-avatar">{{ u.name?.charAt(0)?.toUpperCase() }}</div>
                <strong>{{ u.name }}</strong>
              </div>
            </td>
            <td class="email-cell">{{ u.email }}</td>
            <td><span class="role-chip" :class="u.role">{{ roleLabel(u.role) }}</span></td>
            <td>
              <span class="status-dot" :class="u.active ? 'active' : 'inactive'">
                {{ u.active ? 'Aktiv' : 'Deaktiviert' }}
              </span>
            </td>
            <td class="date-cell">{{ formatDate(u.created_at) }}</td>
            <td>
              <div class="action-btns">
                <button class="btn-icon" @click="openEdit(u)" title="Bearbeiten">✏️</button>
                <button class="btn-icon" @click="toggleActive(u)" :title="u.active ? 'Deaktivieren' : 'Aktivieren'">{{ u.active ? '🚫' : '✅' }}</button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="modal-overlay" v-if="showModal" @click.self="closeModal">
      <div class="modal">
        <div class="modal-header">
          <h3 class="modal-title">{{ editingUser ? 'Benutzer bearbeiten' : 'Neuer Benutzer' }}</h3>
          <button class="btn-close" @click="closeModal">✕</button>
        </div>
        <div class="modal-body">
          <div class="field"><label>Name *</label><input v-model="form.name" type="text" class="input" placeholder="Vor- und Nachname" /></div>
          <div class="field"><label>E-Mail *</label><input v-model="form.email" type="email" class="input" placeholder="email@firma.ch" :disabled="!!editingUser" /></div>
          <div class="field">
            <label>Rolle *</label>
            <div class="role-options">
              <div v-for="r in roles" :key="r.value" class="role-card" :class="{ selected: form.role === r.value }" @click="form.role = r.value">
                <span class="role-icon">{{ r.icon }}</span>
                <div><strong>{{ r.label }}</strong><p>{{ r.desc }}</p></div>
              </div>
            </div>
          </div>
          <div class="field">
            <label>{{ editingUser ? 'Neues Passwort (leer = unverändert)' : 'Passwort *' }}</label>
            <div class="pw-wrap">
              <input v-model="form.password" :type="showPw ? 'text' : 'password'" class="input" placeholder="Mindestens 8 Zeichen" />
              <button type="button" class="pw-toggle" @click="showPw = !showPw">{{ showPw ? '🙈' : '👁️' }}</button>
            </div>
          </div>
          <div class="form-error" v-if="formError">{{ formError }}</div>
        </div>
        <div class="modal-footer">
          <button class="btn-cancel" @click="closeModal">Abbrechen</button>
          <button class="btn-save" @click="saveUser" :disabled="saving">
            <span v-if="!saving">{{ editingUser ? 'Speichern' : 'Erstellen' }}</span>
            <span v-else class="spinner-sm"></span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api'

const users = ref([]); const loading = ref(true); const showModal = ref(false)
const editingUser = ref(null); const saving = ref(false); const formError = ref(''); const showPw = ref(false)
const form = ref({ name: '', email: '', role: 'operator', password: '' })
const roles = [
  { value: 'admin',    icon: '🔑', label: 'Administrator', desc: 'Voller Zugriff' },
  { value: 'operator', icon: '✍️', label: 'Operator',      desc: 'Übergaben & Archiv' },
  { value: 'viewer',   icon: '👁️', label: 'Betrachter',    desc: 'Nur Archiv lesen' },
]
function roleLabel(r) { return { admin: 'Admin', operator: 'Operator', viewer: 'Betrachter' }[r] || r }
function formatDate(dt) { return dt ? new Date(dt).toLocaleDateString('de-CH', { day: '2-digit', month: '2-digit', year: 'numeric' }) : '—' }
function openCreate() { editingUser.value = null; form.value = { name: '', email: '', role: 'operator', password: '' }; formError.value = ''; showPw.value = false; showModal.value = true }
function openEdit(u)  { editingUser.value = u; form.value = { name: u.name, email: u.email, role: u.role, password: '' }; formError.value = ''; showPw.value = false; showModal.value = true }
function closeModal() { showModal.value = false; editingUser.value = null }
async function saveUser() {
  formError.value = ''
  if (!form.value.name)  { formError.value = 'Name ist erforderlich'; return }
  if (!form.value.email) { formError.value = 'E-Mail ist erforderlich'; return }
  if (!editingUser.value && !form.value.password) { formError.value = 'Passwort ist erforderlich'; return }
  saving.value = true
  try {
    if (editingUser.value) { const p = { name: form.value.name, role: form.value.role }; if (form.value.password) p.password = form.value.password; await api.put(`/users/${editingUser.value.id}`, p) }
    else { await api.post('/users/', form.value) }
    await loadUsers(); closeModal()
  } catch (e) { formError.value = e.response?.data?.detail || 'Fehler beim Speichern' }
  finally { saving.value = false }
}
async function toggleActive(u) { await api.put(`/users/${u.id}`, { active: !u.active }); await loadUsers() }
async function loadUsers() { loading.value = true; try { const res = await api.get('/users/'); users.value = res.data } catch (e) { console.error(e) } finally { loading.value = false } }
onMounted(loadUsers)
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=DM+Sans:wght@300;400;500;600&display=swap');

.users-page { padding: 40px 44px; font-family: 'DM Sans', sans-serif; }

.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 28px; }
.page-eyebrow { font-size: 12px; font-weight: 500; letter-spacing: 0.05em; text-transform: uppercase; color: #98989f; margin-bottom: 5px; }
.page-title { font-family: 'Instrument Serif', serif; font-size: 38px; font-weight: 400; color: #1c1c1e; letter-spacing: -1px; }
.btn-primary { padding: 11px 22px; background: linear-gradient(135deg, #e8849a, #c0546a); color: white; border: none; border-radius: 12px; font-family: 'DM Sans', sans-serif; font-size: 14px; font-weight: 500; cursor: pointer; box-shadow: 0 2px 12px rgba(192,84,106,0.3); transition: opacity 0.2s; margin-top: 6px; }
.btn-primary:hover { opacity: 0.9; }

.table-card { background: white; border-radius: 14px; box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 0 0 1px rgba(0,0,0,0.04); overflow: hidden; }
.users-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.users-table th { text-align: left; font-size: 11px; font-weight: 600; letter-spacing: 0.05em; text-transform: uppercase; color: #98989f; padding: 14px 20px; border-bottom: 1px solid #f0f0f0; }
.user-row td { padding: 14px 20px; border-bottom: 1px solid #f7f7f7; color: #1c1c1e; }
.user-row:hover td { background: #fafafa; }
.user-row.inactive td { opacity: 0.4; }
.user-row:last-child td { border-bottom: none; }
.user-cell { display: flex; align-items: center; gap: 10px; }
.user-avatar { width: 30px; height: 30px; background: linear-gradient(135deg, #f2a7b8, #c0546a); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 600; color: white; flex-shrink: 0; }
.user-cell strong { font-weight: 500; font-size: 14px; color: #1c1c1e; }
.email-cell { color: #6e6e73; }
.date-cell  { color: #98989f; font-size: 12px; }

.role-chip { font-size: 11px; font-weight: 600; padding: 3px 10px; border-radius: 980px; }
.role-chip.admin    { background: rgba(192,84,106,0.1); color: #c0546a; }
.role-chip.operator { background: rgba(40,167,69,0.1);  color: #1a7a2e; }
.role-chip.viewer   { background: rgba(152,152,159,0.12); color: #6e6e73; }

.status-dot { font-size: 12px; font-weight: 500; display: flex; align-items: center; gap: 6px; }
.status-dot::before { content: ''; width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0; }
.status-dot.active::before   { background: #28c840; }
.status-dot.inactive::before { background: #98989f; }
.status-dot.active   { color: #1a7a2e; }
.status-dot.inactive { color: #98989f; }

.action-btns { display: flex; gap: 6px; }
.btn-icon { background: #f5f5f7; border: none; width: 30px; height: 30px; border-radius: 8px; cursor: pointer; font-size: 14px; transition: background 0.15s; }
.btn-icon:hover { background: #e8e8ed; }

.table-loading { padding: 16px; display: flex; flex-direction: column; gap: 8px; }
.skeleton { height: 52px; background: linear-gradient(90deg, #f5f5f7 25%, #ebebeb 50%, #f5f5f7 75%); background-size: 200% 100%; border-radius: 8px; animation: shimmer 1.4s infinite; }
.empty-state { display: flex; flex-direction: column; align-items: center; gap: 8px; padding: 64px; color: #98989f; font-size: 14px; }
.empty-state span { font-size: 36px; }

.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.35); backdrop-filter: blur(4px); z-index: 200; display: flex; align-items: center; justify-content: center; }
.modal { background: white; border-radius: 20px; width: 100%; max-width: 480px; box-shadow: 0 24px 60px rgba(0,0,0,0.15); overflow: hidden; animation: popUp 0.25s cubic-bezier(0.175,0.885,0.32,1.275) both; }
.modal-header { display: flex; justify-content: space-between; align-items: center; padding: 24px 28px; border-bottom: 1px solid #f0f0f0; }
.modal-title  { font-family: 'Instrument Serif', serif; font-size: 22px; font-weight: 400; color: #1c1c1e; letter-spacing: -0.5px; }
.btn-close { background: #f5f5f7; border: none; width: 28px; height: 28px; border-radius: 50%; cursor: pointer; font-size: 12px; color: #6e6e73; }
.btn-close:hover { background: #e8e8ed; }
.modal-body { padding: 24px 28px; display: flex; flex-direction: column; gap: 18px; }
.modal-footer { padding: 16px 28px; border-top: 1px solid #f0f0f0; display: flex; justify-content: flex-end; gap: 10px; }

.field { display: flex; flex-direction: column; gap: 6px; }
.field label { font-size: 11px; font-weight: 600; color: #1c1c1e; text-transform: uppercase; letter-spacing: 0.05em; }
.input { padding: 12px 16px; border: 1.5px solid #e8e8ed; border-radius: 11px; font-family: 'DM Sans', sans-serif; font-size: 15px; color: #1c1c1e; outline: none; background: white; transition: all 0.2s; width: 100%; }
.input:focus { border-color: #c0546a; box-shadow: 0 0 0 3px rgba(192,84,106,0.1); }
.input:disabled { background: #f5f5f7; color: #98989f; }
.pw-wrap { position: relative; }
.pw-wrap .input { padding-right: 44px; }
.pw-toggle { position: absolute; right: 12px; top: 50%; transform: translateY(-50%); background: none; border: none; cursor: pointer; font-size: 16px; }

.role-options { display: flex; flex-direction: column; gap: 8px; }
.role-card { display: flex; align-items: center; gap: 12px; padding: 12px 16px; border-radius: 11px; border: 1.5px solid #e8e8ed; cursor: pointer; transition: all 0.15s; }
.role-card:hover   { border-color: #d0d0d0; }
.role-card.selected { border-color: #c0546a; background: rgba(192,84,106,0.04); }
.role-icon { font-size: 20px; flex-shrink: 0; }
.role-card strong { font-size: 14px; color: #1c1c1e; display: block; }
.role-card p      { font-size: 12px; color: #98989f; margin-top: 1px; }

.form-error { background: rgba(255,59,48,0.07); border: 1px solid rgba(255,59,48,0.2); border-radius: 10px; padding: 10px 14px; font-size: 13px; color: #c0392b; }
.btn-cancel { padding: 11px 20px; background: white; border: 1.5px solid #e8e8ed; border-radius: 11px; font-family: 'DM Sans', sans-serif; font-size: 14px; color: #6e6e73; cursor: pointer; }
.btn-cancel:hover { background: #f5f5f7; }
.btn-save { padding: 11px 24px; background: linear-gradient(135deg, #e8849a, #c0546a); color: white; border: none; border-radius: 11px; font-family: 'DM Sans', sans-serif; font-size: 14px; font-weight: 500; cursor: pointer; min-width: 100px; display: flex; align-items: center; justify-content: center; }
.btn-save:hover:not(:disabled) { opacity: 0.9; }
.btn-save:disabled { opacity: 0.45; cursor: not-allowed; }
.spinner-sm { width: 15px; height: 15px; border: 2px solid rgba(255,255,255,0.3); border-top-color: white; border-radius: 50%; animation: spin 0.7s linear infinite; display: inline-block; }

@keyframes shimmer { to { background-position: -200% 0; } }
@keyframes spin    { to { transform: rotate(360deg); } }
@keyframes popUp   { from { opacity: 0; transform: scale(0.93) translateY(10px); } to { opacity: 1; transform: scale(1) translateY(0); } }
</style>
