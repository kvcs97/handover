<template>
  <div class="shell">

    <aside class="sidebar">
      <div class="sidebar-top">
        <div class="sidebar-brand">
          <div class="sidebar-logo">
            <svg viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M4 4v12M16 4v12M4 10h12" stroke="white" stroke-width="2.5" stroke-linecap="round"/>
            </svg>
          </div>
          <div class="sidebar-brand-text">
            <span class="sidebar-name">HandOver</span>
            <span class="sidebar-sub">{{ settingsStore.companyName }}</span>
          </div>
        </div>

        <nav class="sidebar-nav">
          <div class="nav-group-label">Workflow</div>
          <button
            v-for="item in workflowItems"
            :key="item.page"
            class="nav-item"
            :class="{ active: currentPage === item.page, disabled: item.role && !hasRole(item.role) }"
            @click="navigate(item)"
          >
            <span class="nav-icon">{{ item.icon }}</span>
            <span class="nav-label">{{ item.label }}</span>
          </button>

          <div class="nav-group-label" style="margin-top:16px">Verwaltung</div>
          <button
            v-for="item in adminItems"
            :key="item.page"
            class="nav-item"
            :class="{ active: currentPage === item.page, disabled: item.role && !hasRole(item.role) }"
            @click="navigate(item)"
          >
            <span class="nav-icon">{{ item.icon }}</span>
            <span class="nav-label">{{ item.label }}</span>
          </button>
        </nav>
      </div>

      <div class="sidebar-bottom">
        <div class="user-chip">
          <div class="user-avatar">{{ authStore.userName?.charAt(0)?.toUpperCase() }}</div>
          <div class="user-info">
            <span class="user-name">{{ authStore.userName }}</span>
            <span class="user-role">{{ roleLabel }}</span>
          </div>
        </div>
        <button class="btn-logout" @click="authStore.logout()" title="Abmelden">↩</button>
      </div>
    </aside>

    <main class="main">
      <Dashboard    v-if="currentPage === 'dashboard'" @navigate="currentPage = $event" />
      <HandoverPage v-else-if="currentPage === 'handover'" />
      <ArchivePage  v-else-if="currentPage === 'archive'" />
      <UsersPage    v-else-if="currentPage === 'users' && authStore.isAdmin" />
      <SettingsPage v-else-if="currentPage === 'settings' && authStore.isAdmin" />
    </main>

  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useAuthStore }     from '../../stores/auth'
import { useSettingsStore } from '../../stores/settings'
import Dashboard    from '../../pages/Dashboard.vue'
import HandoverPage from '../../pages/Handover.vue'
import ArchivePage  from '../../pages/Archive.vue'
import UsersPage    from '../../pages/Users.vue'
import SettingsPage from '../../pages/Settings.vue'

const authStore     = useAuthStore()
const settingsStore = useSettingsStore()
const currentPage   = ref('dashboard')

const workflowItems = [
  { page: 'handover',  icon: '✦',  label: 'Neue Übergabe', role: 'operator' },
  { page: 'dashboard', icon: '⊞',  label: 'Dashboard' },
]
const adminItems = [
  { page: 'archive',  icon: '🗂',  label: 'Archiv' },
  { page: 'users',    icon: '👤',  label: 'Benutzer',      role: 'admin' },
  { page: 'settings', icon: '⚙️',  label: 'Einstellungen', role: 'admin' },
]

const roleLabel = computed(() => ({
  admin:    'Administrator',
  operator: 'Operator',
  viewer:   'Betrachter',
}[authStore.userRole] || authStore.userRole))

function hasRole(required) {
  if (required === 'admin')    return authStore.isAdmin
  if (required === 'operator') return !authStore.isViewer
  return true
}
function navigate(item) {
  if (item.role && !hasRole(item.role)) return
  currentPage.value = item.page
}
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=DM+Sans:wght@300;400;500;600&display=swap');

.shell {
  display: flex; height: 100vh;
  font-family: 'DM Sans', sans-serif;
  background: #f2f2f7;
}

/* ── Sidebar ── */
.sidebar {
  width: 220px; flex-shrink: 0;
  background: #ffffff;
  border-right: 1px solid rgba(0,0,0,0.08);
  display: flex; flex-direction: column;
  justify-content: space-between;
  padding: 24px 12px;
}

.sidebar-brand {
  display: flex; align-items: center; gap: 10px;
  padding: 4px 8px; margin-bottom: 28px;
}
.sidebar-logo {
  width: 32px; height: 32px; border-radius: 9px;
  background: linear-gradient(135deg, #f2a7b8 0%, #c0546a 100%);
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(192,84,106,0.3);
}
.sidebar-logo svg { width: 16px; height: 16px; }
.sidebar-name {
  display: block; font-family: 'Instrument Serif', serif;
  font-size: 16px; color: #1c1c1e; letter-spacing: -0.2px;
}
.sidebar-sub {
  display: block; font-size: 11px; color: #98989f;
  margin-top: 1px; white-space: nowrap; overflow: hidden;
  text-overflow: ellipsis; max-width: 140px;
}

.nav-group-label {
  font-size: 11px; font-weight: 600; letter-spacing: 0.04em;
  text-transform: uppercase; color: #98989f;
  padding: 0 10px; margin-bottom: 4px;
}

.nav-item {
  display: flex; align-items: center; gap: 10px;
  padding: 9px 10px; border-radius: 10px;
  border: none; background: none; cursor: pointer;
  text-align: left; width: 100%;
  font-family: 'DM Sans', sans-serif;
  font-size: 14px; font-weight: 400; color: #3a3a3c;
  margin-bottom: 1px; transition: background 0.12s;
  position: relative;
}
.nav-item:hover:not(.disabled) { background: #f5f5f7; }
.nav-item.active {
  background: rgba(192,84,106,0.08);
  color: #c0546a; font-weight: 500;
}
.nav-item.active::before {
  content: ''; position: absolute;
  left: 0; top: 50%; transform: translateY(-50%);
  width: 3px; height: 20px;
  background: linear-gradient(180deg, #f2a7b8, #c0546a);
  border-radius: 0 3px 3px 0;
}
.nav-item.disabled { opacity: 0.35; cursor: not-allowed; }
.nav-icon  { font-size: 14px; width: 20px; text-align: center; flex-shrink: 0; }
.nav-label { font-size: 14px; flex: 1; }

/* ── Sidebar Bottom ── */
.sidebar-bottom {
  display: flex; align-items: center; gap: 8px;
  padding: 12px 8px 4px;
  border-top: 1px solid rgba(0,0,0,0.06);
}
.user-chip { display: flex; align-items: center; gap: 9px; flex: 1; min-width: 0; }
.user-avatar {
  width: 30px; height: 30px;
  background: linear-gradient(135deg, #f2a7b8, #c0546a);
  border-radius: 50%; display: flex; align-items: center; justify-content: center;
  font-size: 12px; font-weight: 600; color: white; flex-shrink: 0;
}
.user-name {
  display: block; font-size: 13px; font-weight: 500; color: #1c1c1e;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.user-role { display: block; font-size: 11px; color: #98989f; }
.btn-logout {
  background: none; border: none; color: #98989f;
  font-size: 16px; cursor: pointer; padding: 6px;
  border-radius: 8px; transition: all 0.15s; flex-shrink: 0;
}
.btn-logout:hover { background: #f5f5f7; color: #1c1c1e; }

/* ── Main ── */
.main { flex: 1; overflow-y: auto; min-width: 0; background: #f2f2f7; }
</style>
