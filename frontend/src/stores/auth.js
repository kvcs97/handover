import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../api'

export const useAuthStore = defineStore('auth', () => {
  const token    = ref(localStorage.getItem('handover_token') || null)
  const userName = ref(localStorage.getItem('handover_user') || '')
  const userRole = ref(localStorage.getItem('handover_role') || '')

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
    localStorage.setItem('handover_token', token.value)
    localStorage.setItem('handover_user',  userName.value)
    localStorage.setItem('handover_role',  userRole.value)
    api.defaults.headers.common['Authorization'] = `Bearer ${token.value}`
  }

  function logout() {
    token.value    = null
    userName.value = ''
    userRole.value = ''
    localStorage.removeItem('handover_token')
    localStorage.removeItem('handover_user')
    localStorage.removeItem('handover_role')
    delete api.defaults.headers.common['Authorization']
  }

  function restore() {
    if (token.value) {
      api.defaults.headers.common['Authorization'] = `Bearer ${token.value}`
    }
  }

  return { token, userName, userRole, isLoggedIn, isAdmin, isViewer, login, logout, restore }
})
