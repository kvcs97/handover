import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../api'

export const useAuthStore = defineStore('auth', () => {
  const token    = ref(localStorage.getItem('handover_token') || null)
  const userName = ref(localStorage.getItem('handover_user') || '')
  const userRole = ref(localStorage.getItem('handover_role') || '')
  const userId   = ref(parseInt(localStorage.getItem('handover_uid') || '0') || null)

  const isLoggedIn = computed(() => !!token.value)
  const isAdmin    = computed(() => userRole.value === 'admin')
  const isViewer   = computed(() => userRole.value === 'viewer')

  async function login(email, password) {
    const form = new URLSearchParams()
    form.append('username', email)
    form.append('password', password)
    const res = await api.post('/auth/login', form)
    token.value    = res.data.access_token
    userName.value = res.data.user_name
    userRole.value = res.data.user_role
    userId.value   = res.data.user_id ?? null
    localStorage.setItem('handover_token', token.value)
    localStorage.setItem('handover_user',  userName.value)
    localStorage.setItem('handover_role',  userRole.value)
    if (userId.value) localStorage.setItem('handover_uid', String(userId.value))
    api.defaults.headers.common['Authorization'] = `Bearer ${token.value}`
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

  return { token, userName, userRole, userId, isLoggedIn, isAdmin, isViewer, login, logout, restore }
})
