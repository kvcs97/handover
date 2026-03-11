<template>
  <div class="shell">

    <!-- Sidebar -->
    <aside class="sidebar">
      <div class="sidebar-top">
        <div class="sidebar-brand">
          <div class="sidebar-logo">H</div>
          <div class="sidebar-brand-text">
            <span class="sidebar-name">HandOver</span>
            <span class="sidebar-sub">{{ settingsStore.companyName }}</span>
          </div>
        </div>

        <nav class="sidebar-nav">
          <button
            v-for="item in navItems"
            :key="item.page"
            class="nav-item"
            :class="{ active: currentPage === item.page, disabled: item.role && !hasRole(item.role) }"
            @click="navigate(item)"
          >
            <span class="nav-icon">{{ item.icon }}</span>
            <span class="nav-label">{{ item.label }}</span>
            <span class="nav-badge" v-if="item.badge">{{ item.badge }}</span>
          </button>
        </nav>
      </div>

      <div class="sidebar-bottom">
        <div class="user-chip">
          <div class="user-avatar">{{ authStore.userName?.charAt(0) }}</div>
          <div class="user-info">
            <span class="user-name">{{ authStore.userName }}</span>
            <span class="user-role">{{ roleLabel }}</span>
          </div>
        </div>
        <button class="btn-logout" @click="authStore.logout()">↩</button>
      </div>
    </aside>

    <!-- Main Content -->
    <main class="main">
      <Dashboard  v-if="currentPage === 'dashboard'" />
      <HandoverPage v-else-if="currentPage === 'handover'" />
      <ArchivePage  v-else-if="currentPage === 'archive'" />
      <UsersPage    v-else-if="currentPage === 'users' && authStore.isAdmin" />
      <SettingsPage v-else-if="currentPage === 'settings' && authStore.isAdmin" />
    </main>

  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useAuthStore }    from '../../stores/auth'
import { useSettingsStore } from '../../stores/settings'
import Dashboard    from '../../pages/Dashboard.vue'
import HandoverPage from '../../pages/Handover.vue'
import ArchivePage  from '../../pages/Archive.vue'
import UsersPage    from '../../pages/Users.vue'
import SettingsPage from '../../pages/Settings.vue'

const authStore     = useAuthStore()
const settingsStore = useSettingsStore()
const currentPage   = ref('dashboard')

const navItems = computed(() => [
  { page: 'dashboard', icon: '⊞',  label: 'Dashboard' },
  { page: 'handover',  icon: '✍️',  label: 'Übergabe starten', role: 'operator' },
  { page: 'archive',   icon: '📁',  label: 'Archiv' },
  { page: 'users',     icon: '👥',  label: 'Benutzer',   role: 'admin' },
  { page: 'settings',  icon: '⚙️',  label: 'Einstellungen', role: 'admin' },
])

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
@import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=DM+Sans:wght@300;400;500&display=swap');

.shell {
  display: flex;
  height: 100vh;
  font-family: 'DM Sans', sans-serif;
  background: #f5f5f7;
}

/* ── Sidebar ─────────────────────────────────── */
.sidebar {
  width: 240px;
  flex-shrink: 0;
  background: #1d1d1f;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 24px 16px;
}

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 8px;
  margin-bottom: 32px;
}
.sidebar-logo {
  width: 36px; height: 36px;
  background: #0071e3;
  border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  font-family: 'Instrument Serif', serif;
  font-size: 20px;
  color: white;
  flex-shrink: 0;
}
.sidebar-name {
  display: block;
  font-family: 'Instrument Serif', serif;
  font-size: 17px;
  color: white;
  letter-spacing: -0.3px;
}
.sidebar-sub {
  display: block;
  font-size: 11px;
  color: #48484a;
  margin-top: 1px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 150px;
}

.sidebar-nav {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 10px;
  border: none;
  background: none;
  cursor: pointer;
  text-align: left;
  width: 100%;
  transition: background 0.15s;
  color: #98989f;
}
.nav-item:hover:not(.disabled) {
  background: rgba(255,255,255,0.06);
  color: white;
}
.nav-item.active {
  background: rgba(255,255,255,0.1);
  color: white;
}
.nav-item.disabled {
  opacity: 0.3;
  cursor: not-allowed;
}
.nav-icon  { font-size: 16px; width: 20px; text-align: center; flex-shrink: 0; }
.nav-label { font-size: 14px; font-weight: 400; flex: 1; }
.nav-badge {
  background: #0071e3;
  color: white;
  font-size: 10px;
  font-weight: 600;
  padding: 2px 7px;
  border-radius: 980px;
}

/* ── Sidebar Bottom ──────────────────────────── */
.sidebar-bottom {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 8px;
  border-top: 1px solid rgba(255,255,255,0.06);
  margin-top: 8px;
}
.user-chip {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
  min-width: 0;
}
.user-avatar {
  width: 32px; height: 32px;
  background: #2c2c2e;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 13px;
  font-weight: 600;
  color: white;
  flex-shrink: 0;
  text-transform: uppercase;
}
.user-name {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: white;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.user-role {
  display: block;
  font-size: 11px;
  color: #6e6e73;
}
.btn-logout {
  background: none;
  border: none;
  color: #6e6e73;
  font-size: 18px;
  cursor: pointer;
  padding: 4px 6px;
  border-radius: 6px;
  transition: color 0.2s, background 0.2s;
  flex-shrink: 0;
}
.btn-logout:hover { color: white; background: rgba(255,255,255,0.08); }

/* ── Main ────────────────────────────────────── */
.main {
  flex: 1;
  overflow-y: auto;
  min-width: 0;
}
</style>
