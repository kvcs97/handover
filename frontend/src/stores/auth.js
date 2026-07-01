import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../api'

export const useAuthStore = defineStore('auth', () => {
  const token    = ref(null)
  const userName = ref(localStorage.getItem('handover_user') || '')
  const userRole = ref(localStorage.getItem('handover_role') || '')
  const userId   = ref(parseInt(localStorage.getItem('handover_uid') || '0') || null)

  const isLoggedIn = computed(() => !!token.value)
  const isAdmin    = computed(() => userRole.value === 'admin')
  const isViewer   = computed(() => userRole.value === 'viewer')

  function _applyToken(data) {
    token.value    = data.access_token
    userName.value = data.user_name
    userRole.value = data.user_role
    userId.value   = data.user_id ?? null
    localStorage.setItem('handover_user', userName.value)
    localStorage.setItem('handover_role', userRole.value)
    if (userId.value) localStorage.setItem('handover_uid', String(userId.value))
    api.defaults.headers.common['Authorization'] = `Bearer ${token.value}`
  }

  async function login(email, password) {
    const form = new URLSearchParams()
    form.append('username', email)
    form.append('password', password)
    const res = await api.post('/auth/login', form)
    if (res.data.requires_password_change) {
      const err = new Error('PASSWORD_CHANGE_REQUIRED')
      err.code = 'PASSWORD_CHANGE_REQUIRED'
      throw err
    }
    _applyToken(res.data)
  }

  async function upgradePassword(email, currentPassword, newPassword) {
    const res = await api.post('/auth/upgrade-password', {
      email,
      current_password: currentPassword,
      new_password:     newPassword,
    })
    _applyToken(res.data)
  }

  function logout() {
    token.value    = null
    userName.value = ''
    userRole.value = ''
    userId.value   = null
    localStorage.removeItem('handover_token')
    localStorage.removeItem('handover_user')
    localStorage.removeItem('handover_role')
    localStorage.removeItem('handover_uid')
    delete api.defaults.headers.common['Authorization']
  }

  async function restore() {
    if (!token.value) return
    api.defaults.headers.common['Authorization'] = `Bearer ${token.value}`
    // Falls userId aus aelterem Login fehlt, per /auth/me nachziehen
    if (!userId.value) {
      try {
        const res = await api.get('/auth/me')
        userId.value = res.data.id
        localStorage.setItem('handover_uid', String(userId.value))
      } catch {}
    }
  }

  return { token, userName, userRole, userId, isLoggedIn, isAdmin, isViewer, login, logout, restore, upgradePassword }
})
